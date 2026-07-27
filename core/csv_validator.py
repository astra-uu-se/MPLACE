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
# Description:  Validation of CSV files on loading
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.7
# Last Revision: August 2026
#
import logging
from typing import List, Optional
from dataclasses import dataclass

from core.layout_utils import transform_coordinate, find_all_plates_concentrations

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CsvDiagnostics:
    """
    Results of a CSV consistency check against the currently loaded plate parameters.

    Attributes:
        out_of_bounds_count: Number of wells whose coordinates exceed the expected dimensions
        csv_rows: Maximum row index inferred from CSV (1-indexed)
        csv_cols: Maximum column index inferred from CSV (1-indexed)
        warnings: Human-readable warning messages, empty if no issues were found
    """
    out_of_bounds_count: int
    csv_rows: int
    csv_cols: int
    warnings: List[str]

    def has_warnings(self) -> bool:
        return bool(self.warnings)


def check_csv_consistency(
    csv_lines: List[str],
    expected_rows: int,
    expected_cols: int,
) -> CsvDiagnostics:
    """
    Scan loaded CSV lines for dimensional and structural inconsistencies.

    Checks whether any well coordinates exceed the expected plate dimensions,
    and whether the number of plates in the CSV is greater than 1 (a soft warning).
    Does not check control names — the CSV format does not encode control semantics.

    Args:
        csv_lines: Data lines in PharmBio format (header already stripped),
                   each formatted as 'plateID,well,cmpdname,CONCuM,cmpdnum,VOLuL'
        expected_rows: Number of rows configured in the UI (from DZN or manual entry)
        expected_cols: Number of columns configured in the UI (from DZN or manual entry)

    Returns:
        CsvDiagnostics with inferred dimensions, plate count, and any warning messages
    """
    layouts_dict, _ = find_all_plates_concentrations(csv_lines)

    max_row = 0
    max_col = 0
    out_of_bounds = 0

    for plate_lines in layouts_dict.values():
        for entry in plate_lines:
            well = entry[0]
            try:
                row, col = transform_coordinate(well)
                row += 1 # convert from 0-indexed max to actual count
                col += 1
            except ValueError:
                logger.warning(f"Could not parse well coordinate: '{well}' — skipping")
                continue

            if row > max_row:
                max_row = row
            if col > max_col:
                max_col = col

            if row > expected_rows or col > expected_cols:
                out_of_bounds += 1

    warnings: List[str] = []

    if out_of_bounds > 0:
        warnings.append(
            f"{out_of_bounds} well(s) lie outside of the current bounds. "
            f"CSV file suggests at least {max_row} \u00d7 {max_col} dimensions "
            f"instead of the current {expected_rows} \u00d7 {expected_cols}."
        )

    logger.debug(
        f"CSV consistency check:"
        f"inferred {max_row}\u00d7{max_col}, "
        f"{out_of_bounds} out-of-bounds well(s)"
    )

    return CsvDiagnostics(
        out_of_bounds_count=out_of_bounds,
        csv_rows=max_row,
        csv_cols=max_col,
        warnings=warnings
    )