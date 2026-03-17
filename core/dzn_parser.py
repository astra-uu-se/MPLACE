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
# Description:  Various supplementary utilities related to DZN parsing
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.3
# Last Revision: March 2026
#

import re
import ast
import logging

from typing import Tuple


logger = logging.getLogger(__name__)


def scan_dzn(file_path: str) -> Tuple[str, str, str]:
    """Scan DZN file and extract parameters.
    
    Args:
        file_path: Path to the DZN file
        
    Returns:
        Tuple of (cols, rows, control_names)
        
    Raises:
        FileNotFoundError: If file cannot be read
        ValueError: If DZN file is corrupted or invalid
    """
    rows_str = 'num_rows'  # > num_rows = 16; %% height
    cols_str = 'num_cols'  # > num_cols = 24; %% width
    ctrs_str = 'control_names'
    nb_ctrs_str = 'num_controls'

    logger.debug(f"Scanning DZN file: {file_path}")
    
    try:
        with open(file_path, 'r') as file:
            dzn_text = file.read()
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Cannot read DZN file: {file_path}, error: {e}")
        raise FileNotFoundError(f"Could not read DZN file: {file_path}") from e

    # Remove spaces, tabs and newlines to ensure a more robust scan
    dzn_text = re.sub(r"[\n\t\s]*", "", dzn_text)

    rows = __retrieve_dzn_param__(dzn_text, rows_str)
    cols = __retrieve_dzn_param__(dzn_text, cols_str)
    ctrs = __retrieve_dzn_param__(dzn_text, ctrs_str)
    nb_ctrs = __retrieve_dzn_param__(dzn_text, nb_ctrs_str)

    ctrs = ctrs.replace(nb_ctrs_str, nb_ctrs)

    if rows.isnumeric() and cols.isnumeric():
        controls = str(__parse_control_string__(ctrs))
        logger.info(f"DZN parsed: {cols}x{rows} plate, controls: {controls}")
        return cols, rows, controls
    else:
        logger.error(f"Invalid DZN file - non-numeric dimensions: rows={rows}, cols={cols}")
        raise ValueError('Corrupt dzn file - invalid numeric values')


def __retrieve_dzn_param__(text: str, param_string: str) -> str:
    """Extract parameter value from DZN text.
    
    Args:
        text: DZN file content as string
        param_string: Parameter name to search for
        
    Returns:
        Parameter value as string
        
    Raises:
        ValueError: If parameter not found in text
    """
    param_string += '='
    pos = text.find(param_string)

    if pos == -1:
        logger.error(f"DZN parameter not found: {param_string}")
        raise ValueError(f'Cannot find dzn parameter ({param_string})')

    pos += len(param_string)
    param_res = text[pos:text.find(';', pos)]
    logger.debug(f"DZN parameter extracted: {param_string[:-1]} = {param_res}")

    return param_res


def __parse_control_string__(control_string: str) -> str:
    """Parse the control_names expression from a DZN file into a flat list of names.

    The DZN control_names field can take two forms that this function handles:

    1. A plain MiniZinc list literal, e.g.:
           ["pos", "neg", "DMSO"]
       These sections are separated by '++' and parsed directly with ast.literal_eval.

    2. A MiniZinc array comprehension with a numeric range, e.g.:
           ["ctrl_\\(i) | i in 1..8"]
       This encodes names like ctrl_1, ctrl_2, ..., ctrl_8.
       Detected by the presence of '..' in the section.

    When multiple sections are joined by '++', the resulting names are concatenated
    in order into a single flat list.

    Args:
        control_string: The raw value of the control_names DZN parameter,
                        with all whitespace already stripped by the caller.

    Returns:
        Stringified Python list of control name strings (e.g. "['pos', 'ctrl_1']"),
        or '[]' if any section fails to parse.
        Caller must use ast.literal_eval() to convert back to a Python list.
    """
    control_names = []
    logger.debug(f"Parsing control string: {control_string[:50]}...")
    
    for section in control_string.split('++'):
        if section.find('..') == -1:
            # Plain list literal: ["pos", "neg"]
            try:
                control_names.extend(ast.literal_eval(section))
            except (ValueError, SyntaxError):
                logger.warning(f"Failed to parse control section: {section}")
                return '[]'
        else:
            # Array comprehension: ["ctrl_\(i) | i in 1..8"]
            # Strip the outer brackets added by MiniZinc's ++ concatenation
            try:
                section = section[1:-1]

                # Locate the \(i) placeholder — the loop variable in the name template
                pos_index_s = section.find('\\(')
                pos_index_e = section.find(')', pos_index_s)

                index_str = section[pos_index_s + 2:pos_index_e]

                # Locate the range bounds after '| i in START..END'
                pos_iin = section.find('|' + index_str + 'in')
                pos_nii = pos_iin + len(index_str) + 3
                pos_dot = section.find('..')

                i_start = int(section[pos_nii:pos_dot])
                i_end = int(section[pos_dot + 2:])
                
                # Build one name per index by substituting i into the template
                for i in range(i_start, i_end + 1):
                    control_names.append(
                        section[1:pos_index_s] + str(i) + section[pos_index_e + 1:pos_iin-1])
            except (ValueError, IndexError):
                logger.warning(f"Failed to parse complex control section: {section}")
                return '[]'
    
    logger.debug(f"Parsed {len(control_names)} control names")
    return str(control_names)



