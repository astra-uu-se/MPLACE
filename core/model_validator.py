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
# Description:  Model-compatibility validation for DZN parameters.
#               Checks parameters against PLAID and COMPD constraint logic
#               before file generation. Each check corresponds to a documented
#               assert or derived constraint in the respective .mzn model.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.6
# Last Revision: June 2026
#
# MAINTENANCE NOTE:
#   Quantity computations in _plaid_quantities() and _compd_quantities() must
#   be kept in sync with the arithmetic in:
#     - pharmbio/plaid:            mzn/plate-design.mzn
#     - astra-uu-se/COMPD:        mzn/plate-optimizer.mzn
#   If either model changes its derived formulas, update the corresponding
#   function here.

import math
import logging
from dataclasses import dataclass
from typing import List, Optional

from models.dto import DznBuildParams, ValidationVerdict, ModelVerdict
from models.constants import Messages

logger = logging.getLogger(__name__)


@dataclass
class _CheckResult:
    """Internal result type for a single check
    """
    severity: str        # BLOCK or WARN
    model: str           # "PLAID", "COMPD", or "BOTH"
    message: str


@dataclass
class _PlaidQuantities:
    """Quantity computation for PLAID
    """
    num_rows:           int
    num_cols:           int
    size_empty_edge:    int
    h_lines:            int
    v_lines:            int
    inner_empty_edge:   bool
    num_rows_line:      int
    num_cols_line:      int
    inner_plate_size:   int  # num_rows_line * num_cols_line (no corner deduction)
    total_wells:        int
    num_plates:         int
    empty_wells:        int
    allow_empty_wells:  bool
    replicates_on_different_plates: bool
    replicates_on_same_plate:       bool
    compounds:          int
    compound_replicates:   List[int]
    compound_concentrations: List[int]
    controls:           int


@dataclass
class _CompdQuantities:
    """Quantity computation for COMPD
    """
    num_rows:           int
    num_cols:           int
    size_empty_edge:    int
    corner_wells:       int
    h_lines:            int
    v_lines:            int
    inner_empty_edge:   bool
    num_rows_line:      int
    num_cols_line:      int
    forced_empty_total: int   # 4 * corner_wells^2
    total_wells_line:   int   # num_rows_line * num_cols_line - forced_empty_total
    total_wells:        int
    num_plates_lines:   int
    empty_wells:        int
    allow_empty_wells:  bool
    replicates_on_different_plates: bool
    replicates_on_same_plate:       bool
    compounds:          int
    compound_replicates:   List[int]
    compound_concentrations: List[int]
    controls:           int


def _compute_num_rows_line(num_rows: int, h_lines: int,
                           size_empty_edge: int, inner_empty_edge: bool) -> int:
    """Mirrors the formula in both models (identical in PLAID and COMPD)
       
       Args:
           num_rows: number of rows
           h_lines: number of horizontal lines
           size_empty_edge: the number of rows within the empty edge
           inner_empty_edge: Boolean flag denoting which kind of inner edge is used
           
       Returns:
           the number of rows within a plate line
    """
    if inner_empty_edge:
        return math.floor(num_rows / h_lines) - 2 * size_empty_edge
    else:
        return math.floor((num_rows - 2 * size_empty_edge) / h_lines)


def _compute_num_cols_line(num_cols: int, v_lines: int,
                           size_empty_edge: int, inner_empty_edge: bool) -> int:
    """Mirrors the formula in both models (identical in PLAID and COMPD)
       
       Args:
           num_cols: number of cols
           v_lines: number of vertical lines
           size_empty_edge: the number of rows within the empty edge
           inner_empty_edge: Boolean flag denoting which kind of inner edge is used
           
       Returns:
           the number of cols within a plate line
    """
    if inner_empty_edge:
        return math.floor(num_cols / v_lines) - 2 * size_empty_edge
    else:
        return math.floor((num_cols - 2 * size_empty_edge) / v_lines)


def _plaid_quantities(p: DznBuildParams) -> _PlaidQuantities:
    """Calculate all numbered quantitities for PLAID model
       
       Args:
           p: All the parameters from the dzn generation form
           
       Returns:
           All the calculated PLAID quantities
    """
    num_rows      = p.get_num_rows_int()
    num_cols      = p.get_num_cols_int()
    size_edge     = p.get_size_empty_edge_int()
    corner        = p.get_size_corner_empty_wells_int()  # PLAID ignores this value entirely
    h_lines       = p.get_horizontal_cell_lines_int()
    v_lines       = p.get_vertical_cell_lines_int()

    num_rows_line = _compute_num_rows_line(num_rows, h_lines, size_edge, p.inner_empty_edge)
    num_cols_line = _compute_num_cols_line(num_cols, v_lines, size_edge, p.inner_empty_edge)

    inner_plate_size = num_rows_line * num_cols_line  # PLAID: no corner deduction

    compounds   = len(p.compounds_dict)
    comp_reps   = [v[0] for v in p.compounds_dict.values()]
    comp_concs  = [len(v) - 1 for v in p.compounds_dict.values()]
    controls    = len(p.controls_dict)
    ctrl_reps   = [v[0] for v in p.controls_dict.values()]
    ctrl_concs  = [len(v) - 1 for v in p.controls_dict.values()]

    total_controls = sum(r * c for r, c in zip(ctrl_reps, ctrl_concs))
    total_wells    = sum(r * c for r, c in zip(comp_reps, comp_concs)) + total_controls
    num_plates     = max(math.ceil(total_wells / inner_plate_size) if inner_plate_size > 0 else 1, 1)
    empty_wells    = num_plates * inner_plate_size - total_wells

    return _PlaidQuantities(
        num_rows=num_rows, num_cols=num_cols,
        size_empty_edge=size_edge, h_lines=h_lines, v_lines=v_lines,
        inner_empty_edge=p.inner_empty_edge,
        num_rows_line=num_rows_line, num_cols_line=num_cols_line,
        inner_plate_size=inner_plate_size,
        total_wells=total_wells, num_plates=num_plates, empty_wells=empty_wells,
        allow_empty_wells=p.flag_allow_empty_wells,
        replicates_on_different_plates=p.flag_replicates_on_different_plates,
        replicates_on_same_plate=p.flag_replicates_on_same_plate,
        compounds=compounds, compound_replicates=comp_reps,
        compound_concentrations=comp_concs, controls=controls,
    )


def _compd_quantities(p: DznBuildParams) -> _CompdQuantities:
    """Calculate all numbered quantitities for COMPD model
       
       Args:
           p: All the parameters from the dzn generation form
           
       Returns:
           All the calculated COMPD quantities
    """
    num_rows      = p.get_num_rows_int()
    num_cols      = p.get_num_cols_int()
    size_edge     = p.get_size_empty_edge_int()
    corner        = p.get_size_corner_empty_wells_int()
    h_lines       = p.get_horizontal_cell_lines_int()
    v_lines       = p.get_vertical_cell_lines_int()

    num_rows_line = _compute_num_rows_line(num_rows, h_lines, size_edge, p.inner_empty_edge)
    num_cols_line = _compute_num_cols_line(num_cols, v_lines, size_edge, p.inner_empty_edge)

    forced_empty_quadrant = corner * corner
    forced_empty_total    = 4 * forced_empty_quadrant
    total_wells_line      = num_rows_line * num_cols_line - forced_empty_total

    compounds   = len(p.compounds_dict)
    comp_reps   = [v[0] for v in p.compounds_dict.values()]
    comp_concs  = [len(v) - 1 for v in p.compounds_dict.values()]
    controls    = len(p.controls_dict)
    ctrl_reps   = [v[0] for v in p.controls_dict.values()]
    ctrl_concs  = [len(v) - 1 for v in p.controls_dict.values()]

    total_controls   = sum(r * c for r, c in zip(ctrl_reps, ctrl_concs))
    total_wells      = sum(r * c for r, c in zip(comp_reps, comp_concs)) + total_controls
    num_plates_lines = max(math.ceil(total_wells / total_wells_line) if total_wells_line > 0 else 1, 1)
    empty_wells      = num_plates_lines * total_wells_line - total_wells

    return _CompdQuantities(
        num_rows=num_rows, num_cols=num_cols,
        size_empty_edge=size_edge, corner_wells=corner,
        h_lines=h_lines, v_lines=v_lines,
        inner_empty_edge=p.inner_empty_edge,
        num_rows_line=num_rows_line, num_cols_line=num_cols_line,
        forced_empty_total=forced_empty_total,
        total_wells_line=total_wells_line,
        total_wells=total_wells, num_plates_lines=num_plates_lines,
        empty_wells=empty_wells,
        allow_empty_wells=p.flag_allow_empty_wells,
        replicates_on_different_plates=p.flag_replicates_on_different_plates,
        replicates_on_same_plate=p.flag_replicates_on_same_plate,
        compounds=compounds, compound_replicates=comp_reps,
        compound_concentrations=comp_concs, controls=controls,
    )


def _check_compounds_non_negative(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check that the compounds are not negative
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.compounds < 0:
        return _CheckResult(Messages.BLOCK, "BOTH", "Number of compounds cannot be less than zero.")
    return None

def _check_combinations_non_negative(_q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check that the combinations are not negative (always passed)
       Combinations are deprecated, and the check is intentionally skipped
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    return None

def _check_controls_non_negative(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check that the controls are not negative
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.controls < 0:
        return _CheckResult(Messages.BLOCK, "BOTH", "Number of controls cannot be less than zero.")
    return None

def _check_v_lines_positive(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check that the number of vertical lines is positive
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.v_lines <= 0:
        return _CheckResult(Messages.BLOCK, "BOTH", f"Number of vertical cell lines must be > 0 (got {q.v_lines}).")
    return None

def _check_h_lines_positive(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check that the number of horizontal lines is positive
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.h_lines <= 0:
        return _CheckResult(Messages.BLOCK, "BOTH", f"Number of horizontal cell lines must be > 0 (got {q.h_lines}).")
    return None

def _check_rows_line_positive(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check that the calculated number of rows in a line is positive
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.num_rows_line <= 0:
        return _CheckResult(Messages.BLOCK, "BOTH",
            f"Number of usable rows per plate line must be > 0 (got {q.num_rows_line}). "
            f"Check plate dimensions, cell lines, and edge size.")
    return None

def _check_cols_line_positive(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check that the calculated number of cols in a line is not negative
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.num_cols_line <= 0:
        return _CheckResult(Messages.BLOCK, "BOTH",
            f"Number of usable columns per plate line must be > 0 (got {q.num_cols_line}). "
            f"Check plate dimensions, cell lines, and edge size.")
    return None

def _check_replicates_not_both(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check that the replicate allocation flags are not used together
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.replicates_on_different_plates and q.replicates_on_same_plate:
        return _CheckResult(Messages.BLOCK, "BOTH",
            "Replicates cannot be on both the same plate and different plates simultaneously.")
    return None

def _check_total_wells_positive(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check that the total number of wells is positive
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.total_wells <= 0:
        return _CheckResult(Messages.BLOCK, "BOTH", "The plate cannot be completely empty (total wells = 0).")
    return None

def _check_rows_line_even_plaid(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """PLAID requires even dimensions for quadrant distribution
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.num_rows_line % 2 != 0:
        return _CheckResult(Messages.BLOCK, "PLAID",
            f"PLAID requires an even number of usable rows per line (got {q.num_rows_line}).")
    return None

def _check_cols_line_even_plaid(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """PLAID requires even dimensions for quadrant distribution
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.num_cols_line % 2 != 0:
        return _CheckResult(Messages.BLOCK, "PLAID",
            f"PLAID requires an even number of usable columns per line (got {q.num_cols_line}).")
    return None

def _check_inner_plate_size_positive_plaid(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check that the inner plate size is non-negative (PLAID)
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.inner_plate_size <= 0:
        return _CheckResult(Messages.BLOCK, "PLAID",
            f"PLAID: usable wells per plate line is {q.inner_plate_size} ≤ 0.")
    return None

def _check_inner_plate_size_positive_compd(q: _CompdQuantities) -> Optional[_CheckResult]:
    """Check that the inner plate size (including corners) is positive (COMPD)
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.total_wells_line <= 1:
        return _CheckResult(Messages.BLOCK, "COMPD",
            f"COMPD: usable wells per plate line after corner deduction is {q.total_wells_line} "
            f"(rows_line={q.num_rows_line}, cols_line={q.num_cols_line}, "
            f"corner_forced={q.forced_empty_total}). Must be > 1.")
    return None

def _check_max_concentrations_fit_plaid(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check that the concentrations of a compound do not exceed the inner size
       of a plate line (PLAID)
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if not q.compound_concentrations:
        return None
    max_conc = max(q.compound_concentrations)
    if max_conc > q.inner_plate_size:
        return _CheckResult(Messages.BLOCK, "PLAID",
            f"PLAID: a compound has {max_conc} concentrations which exceeds the plate capacity "
            f"of {q.inner_plate_size} usable wells.")
    return None

def _check_max_concentrations_fit_compd(q: _CompdQuantities) -> Optional[_CheckResult]:
    """Check that the concentrations of a compound do not exceed the inner size
       of a plate line (COMPD)
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if not q.compound_concentrations:
        return None
    max_conc = max(q.compound_concentrations)
    if max_conc > q.total_wells_line:
        return _CheckResult(Messages.BLOCK, "COMPD",
            f"COMPD: a compound has {max_conc} concentrations which exceeds the plate capacity "
            f"of {q.total_wells_line} usable wells (after corner deduction).")
    return None

def _check_allow_empty_wells_plaid(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check that there are no empty wells in a plate line (PLAID)
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if not q.allow_empty_wells and q.empty_wells != 0:
        return _CheckResult(Messages.BLOCK, "PLAID",
            f"PLAID: allow_empty_wells=false but {q.empty_wells} empty wells would remain. "
            f"Total wells: {q.total_wells}, plate capacity: {q.inner_plate_size} × {q.num_plates} plate(s).")
    return None

def _check_allow_empty_wells_compd(q: _CompdQuantities) -> Optional[_CheckResult]:
    """Check that there are no empty wells in a plate line (COMPD)
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if not q.allow_empty_wells and q.empty_wells != 0:
        return _CheckResult(Messages.BLOCK, "COMPD",
            f"COMPD: allow_empty_wells=false but {q.empty_wells} empty wells would remain. "
            f"Total wells: {q.total_wells}, plate capacity: {q.total_wells_line} × {q.num_plates_lines} plate(s) "
            f"(corner wells already excluded).")
    return None

def _check_corner_size_compd(q: _CompdQuantities) -> Optional[_CheckResult]:
    """Check that the empty well corners do not overlap (COMPD)
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if q.num_rows_line > 0 and q.num_cols_line > 0:
        if 2 * q.corner_wells > max(q.num_rows_line, q.num_cols_line):
            return _CheckResult(Messages.BLOCK, "COMPD",
                f"COMPD: corner size {q.corner_wells} is too large for the plate dimensions "
                f"(rows_line={q.num_rows_line}, cols_line={q.num_cols_line}). "
                f"Requires 2 × corner ≤ max(rows_line, cols_line).")
    return None

def _check_corner_requires_quadrants_compd(q: _CompdQuantities) -> Optional[_CheckResult]:
    """corners are only valid when quadrant distribution is active
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    use_quadrant = q.num_rows_line > 1 and q.num_cols_line > 1
    if q.corner_wells > 0 and not use_quadrant:
        return _CheckResult(Messages.BLOCK, "COMPD",
            f"COMPD: corner_empty_wells={q.corner_wells} requires quadrant distribution "
            f"(num_rows_line > 1 and num_cols_line > 1), but got "
            f"rows_line={q.num_rows_line}, cols_line={q.num_cols_line}.")
    return None

def _check_same_plate_distribution_plaid(q: _PlaidQuantities) -> Optional[_CheckResult]:
    """Check PLAID assert equivalents when replicates_on_same_plate is set.
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    if not q.replicates_on_same_plate:
        return None
    if q.compounds == 0 or q.inner_plate_size == 0:
        return None

    min_conc = min(q.compound_concentrations) if q.compound_concentrations else 0
    max_conc = max(q.compound_concentrations) if q.compound_concentrations else 0
    total_reps = sum(q.compound_replicates)

    # Heaviest possible plate (all replicates on one plate)
    load = total_reps * min_conc
    if load > q.inner_plate_size:
        return _CheckResult(Messages.BLOCK, "PLAID",
            f"PLAID: replicates_on_same_plate is set but the minimum compound load "
            f"({total_reps} replicates × {min_conc} min concentrations = {load}) "
            f"exceeds plate capacity ({q.inner_plate_size}). "
            f"PLAID cannot distribute compounds evenly.")

    load_e02 = (total_reps - 1) * min_conc + max_conc
    if load_e02 > q.inner_plate_size:
        return _CheckResult(Messages.BLOCK, "PLAID",
            f"PLAID: replicates_on_same_plate is set but compound distribution "
            f"({total_reps - 1} × {min_conc} + {max_conc} = {load_e02}) "
            f"exceeds plate capacity ({q.inner_plate_size}). "
            f"PLAID cannot distribute compounds evenly.")

    return None


def _check_same_plate_distribution_compd(q: _CompdQuantities) -> Optional[_CheckResult]:
    """Replicates_on_same_plate with multiple plates must not overload any single plate.
       It is a rough estimation. A more thorough check is performed by COMPD model itself
       
       Args:
           q: Computed model quantities
           
       Returns:
           Optional[_CheckResult]: if returns None then the check is fully passed,
                                   otherwise it returns a tuple that informs of the error:
                                   (Block/Warn flag, affected model/-s, the error message)
    """
    # Single plate: trivially satisfiable, nothing to check.
    if not (q.replicates_on_same_plate and q.num_plates_lines > 1):
        return None

    if q.compounds == 0 or q.total_wells_line == 0:
        return None

    compounds_per_plate = math.ceil(q.compounds / q.num_plates_lines)
    # Estimate max load: worst case is ceil(compounds/plates) compounds on one plate
    # This is approximate — exact check is item 22 (COMPD-internal)
    per_compound_load = sorted(
        (q.compound_replicates[i] * q.compound_concentrations[i] for i in range(q.compounds)),
        reverse=True
    )
    
    max_load = sum(per_compound_load[:compounds_per_plate])
    
    if max_load > q.total_wells_line:
        return _CheckResult(Messages.WARN, "COMPD",
            f"COMPD: replicates_on_same_plate is set and the estimated maximum compound load "
            f"per plate ({max_load}) may exceed plate capacity ({q.total_wells_line}). "
            f"COMPD will report a definitive error if distribution fails.")
    return None


def validate_model_compatibility(params: DznBuildParams) -> ValidationVerdict:
    """
    Run all model-compatibility checks against both PLAID and COMPD constraint logic.

    Args:
        params: DznBuildParams containing all the parameters from DZN generation form
        
    Returns:
        ValidationVerdict with per-model blocked status and messages.
    """
    plaid_q = _plaid_quantities(params)
    compd_q = _compd_quantities(params)

    plaid_messages: List[str] = []
    compd_messages: List[str] = []

    def record(result: Optional[_CheckResult]) -> None:
        if result is None:
            return
        line = f"{result.severity} [{result.model}]: {result.message}"
        if result.model in ("BOTH", "PLAID"):
            plaid_messages.append(f"{result.severity}: {result.message}")
        if result.model in ("BOTH", "COMPD"):
            compd_messages.append(f"{result.severity}: {result.message}")
        logger.debug(line)

    # Universal checks (BOTH) — use plaid_q (values are identical for these)
    record(_check_compounds_non_negative(plaid_q))
    record(_check_combinations_non_negative(plaid_q))
    record(_check_controls_non_negative(plaid_q))
    record(_check_v_lines_positive(plaid_q))
    record(_check_h_lines_positive(plaid_q))
    record(_check_rows_line_positive(plaid_q))
    record(_check_cols_line_positive(plaid_q))
    record(_check_replicates_not_both(plaid_q))
    record(_check_total_wells_positive(plaid_q))

    # PLAID-only checks
    record(_check_rows_line_even_plaid(plaid_q))
    record(_check_cols_line_even_plaid(plaid_q))
    record(_check_same_plate_distribution_plaid(plaid_q))

    # Per-model checks - called separately with each model's quantities
    record(_check_inner_plate_size_positive_plaid(plaid_q))
    record(_check_inner_plate_size_positive_compd(compd_q))
    record(_check_max_concentrations_fit_plaid(plaid_q))
    record(_check_max_concentrations_fit_compd(compd_q))
    record(_check_allow_empty_wells_plaid(plaid_q))
    record(_check_allow_empty_wells_compd(compd_q))

    # COMPD-only checks
    record(_check_corner_size_compd(compd_q))
    record(_check_corner_requires_quadrants_compd(compd_q))
    record(_check_same_plate_distribution_compd(compd_q))

    plaid_blocked = any(m.startswith(Messages.BLOCK) for m in plaid_messages)
    compd_blocked = any(m.startswith(Messages.BLOCK) for m in compd_messages)

    verdict = ValidationVerdict(
        plaid=ModelVerdict(blocked=plaid_blocked, messages=plaid_messages),
        compd=ModelVerdict(blocked=compd_blocked, messages=compd_messages),
    )
    logger.info(
        f"Model compatibility: PLAID={'BLOCKED' if plaid_blocked else 'OK'}, "
        f"COMPD={'BLOCKED' if compd_blocked else 'OK'}"
    )
    return verdict