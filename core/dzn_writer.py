# Copyright 2026 Ramiz Gindullin.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Description:  DZN text generation logic
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.6
# Last Revision: June 2026
#

from models.dto import DznBuildParams, ValidationVerdict
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)


def build_dzn_text(params: DznBuildParams, verdict: ValidationVerdict) -> Tuple[str, List[str]]:
    """
    Build MiniZinc DZN (data) file content from validated parameters.

    This function generates a complete DZN string containing plate dimensions, layout flags,
    compound arrays, and control arrays. Output is compatible with PLAID and related models.

    Args:
        params: DznBuildParams object containing all form data and configuration flags
        verdict: ValidationVerdict containing per-model compatibility status and diagnostic messages

    Returns:
        Tuple of (dzn_content_string, control_names_list)
        
    Notes:
        - Input dicts are copied internally before mutation (string conversion)
        - Concentration matrices are padded with '' to rectangular shape
        - Single quotes are replaced with double quotes for MiniZinc compatibility
    """
    # Shallow copies, as values will be converted to strings
    compounds = {k: list(v) for k, v in params.compounds_dict.items()}
    control_compounds = {k: list(v) for k, v in params.controls_dict.items()}
    
    dzn_txt = _build_header(verdict)

    # Write basic values - now using params.field_name instead of individual parameters
    dzn_txt += 'num_rows = ' + params.num_rows + ';\n'
    dzn_txt += 'num_cols = ' + params.num_cols + ';\n\n'

    if not params.inner_empty_edge:  # no printing for PLAID (this parameter only exists in the COMPD model)
        dzn_txt += 'inner_empty_edge_input = ' + str(params.inner_empty_edge).lower() + ';\n'
    dzn_txt += 'size_empty_edge = ' + params.size_empty_edge + ';\n'
    dzn_txt += 'size_corner_empty_wells = ' + params.size_corner_empty_wells + ';\n\n'

    dzn_txt += 'horizontal_cell_lines = ' + params.horizontal_cell_lines + ';\n'
    dzn_txt += 'vertical_cell_lines = ' + params.vertical_cell_lines + ';\n\n'

    dzn_txt += 'allow_empty_wells = ' + str(params.flag_allow_empty_wells).lower() + ';\n'
    dzn_txt += 'concentrations_on_different_rows = ' + str(params.flag_concentrations_on_different_rows).lower() + ';\n'
    dzn_txt += 'concentrations_on_different_columns = ' + str(params.flag_concentrations_on_different_columns).lower() + ';\n'
    dzn_txt += 'replicates_on_different_plates = ' + str(params.flag_replicates_on_different_plates).lower() + ';\n'
    dzn_txt += 'replicates_on_same_plate = ' + str(params.flag_replicates_on_same_plate).lower() + ';\n\n'

    # Process compounds data
    nb_compounds = 0
    compound_concentrations: List[int] = []
    compound_names: List[str] = []
    compound_replicates: List[int] = []

    for drug in compounds:
        nb_compounds += 1
        compound_names.append(str(drug))
        compound_replicates.append(compounds[drug][0])
        compounds[drug] = [str(x) for x in compounds[drug][1:]]
        compound_concentrations.append(len(compounds[drug]))

    dzn_txt += 'compounds = ' + str(nb_compounds) + ';\n'
    dzn_txt += 'compound_concentrations = ' + str(compound_concentrations) + ';\n'
    dzn_txt += 'compound_names = ' + str(compound_names) + ';\n'
    dzn_txt += 'compound_replicates = ' + str(compound_replicates) + ';\n'
    dzn_txt += 'compound_concentration_names = \n['
    
    drug1 = True
    max_conc = max(compound_concentrations) if compound_concentrations else 0
    for drug in compounds:
        if drug1:
            drug1 = False
        else:
            dzn_txt += ' '
        dzn_txt += '| ' + str(compounds[drug])[1:-1]
        for i in range(len(compounds[drug]), max_conc):
            dzn_txt += ", ''"
        dzn_txt += '\n'
    dzn_txt += '|];\n'
    dzn_txt += 'compound_concentration_indicators = [];\n\n'

    dzn_txt += 'combinations = \t0;\ncombination_names = [];\ncombination_concentration_names = [];\ncombination_concentrations = 0;\n\n'

    # Process controls data
    nb_controls = 0
    control_concentrations: List[int] = []
    control_names_str: List[str] = []
    control_replicates: List[int] = []

    for control in control_compounds:
        nb_controls += 1
        control_names_str.append(str(control))
        control_replicates.append(control_compounds[control][0])
        control_compounds[control] = [str(x) for x in control_compounds[control][1:]]
        control_concentrations.append(len(control_compounds[control]))

    dzn_txt += 'num_controls = ' + str(nb_controls) + ';\n'
    dzn_txt += 'control_concentrations = ' + str(control_concentrations) + ';\n'
    dzn_txt += 'control_names = ' + str(control_names_str) + ';\n'
    dzn_txt += 'control_replicates = ' + str(control_replicates) + ';\n'
    dzn_txt += 'control_concentration_names = \n['
    
    control1 = True
    max_ctrl = max(control_concentrations) if control_concentrations else 0
    for control in control_compounds:
        if control1:
            control1 = False
        else:
            dzn_txt += ' '
        dzn_txt += '| ' + str(control_compounds[control])[1:-1]
        for i in range(len(control_compounds[control]), max_ctrl):
            dzn_txt += ", ''"
        dzn_txt += '\n'
    dzn_txt += '|];\n\n'

    dzn_txt = dzn_txt.replace("'", '"')
    
    logger.debug(f"DZN content generated: {len(dzn_txt)} characters")
    return dzn_txt, control_names_str
    
def _build_header(verdict: ValidationVerdict) -> str:
    """
    Build the MPLACE metadata comment block for the top of the DZN file.
    Warnings and blocks are embedded as comments so MiniZinc ignores them
    but they remain visible to humans and future MPLACE versions.
    
    Args:
        verdict: ValidationVerdict containing per-model compatibility status and diagnostic messages
    
    Returns:
        a string which contains a commented header for the generated dzn file
    """
    lines = ["% Generated by MPLACE."]

    for msg in verdict.plaid.messages:
        lines.append(f"% {msg.split(':', 1)[0]} [PLAID]: {msg.split(':', 1)[1].strip()}")
    for msg in verdict.compd.messages:
        lines.append(f"% {msg.split(':', 1)[0]} [COMPD]: {msg.split(':', 1)[1].strip()}")

    if not verdict.any_issues():
        lines.append("% Compatible with PLAID and COMPD.")

    lines.append("")  # blank line before DZN content
    return "\n".join(lines) + "\n"