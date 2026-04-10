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
# Description: Data Transfer Objects for MPLACE application
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.5
# Last Revision: April 2026
#


"""
Data Transfer Objects (DTOs) for MPLACE application.

DTOs are simple data containers that carry information between different layers
of the application (UI, core logic, models). They help reduce parameter sprawl,
make interfaces explicit, and improve code maintainability.
"""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass(frozen=True)
class AppConfig:
    """Contains all configuration fields (paths) the app relies on
    """
    minizinc_path: str
    plaid_path: str
    compd_path: str
    plaid_mpc_path: str
    compd_mpc_path: str


@dataclass(frozen=True)
class DznGenerationResult:
    """Result of DZN file generation operation.
    
    Carries data from DZN generation logic back to the main UI window
    for integration and callback coordination.
    """
    file_path: str
    rows: str
    cols: str
    control_names: str  # Stringified list for UI callback compatibility


@dataclass(frozen=True)
class MiniZincRunRequest:
    """Request to execute a MiniZinc model.
    
    Encapsulates all parameters needed to run a MiniZinc subprocess,
    making the interface between UI and execution logic explicit.
    """
    minizinc_path: str
    solver_config: str
    model_file: str
    data_file: str


@dataclass(frozen=True)
class MiniZincRunResult:
    """Result of MiniZinc model execution.
    
    Contains both successful output and error information,
    allowing calling code to handle different scenarios appropriately.
    """
    stdout_text: str
    stderr_text: str
    exit_code: int
    success: bool


@dataclass(frozen=True)
class CsvVisualizationRequest:
    """Request to visualize CSV layout data.
    
    Bundles the parameters needed for visualization into a single object,
    reducing parameter passing complexity between UI and visualization logic.
    """
    csv_path: str
    figure_name_template: str
    rows: str
    cols: str
    control_names: str

@dataclass(frozen=True)
class CSVConversionRequest:
    """Request to convert CSV from PharmBio format to Plater format
    
    Bundles the parameters needed for the conversion into a single object.
    """
    rows: str
    cols: str
    csv_lines: List[str]


@dataclass(frozen=True)
class DznBuildParams:
    """Parameters for building DZN file content."""
    num_rows: str
    num_cols: str
    
    # Layout configuration
    inner_empty_edge: bool
    size_empty_edge: str
    size_corner_empty_wells: str
    horizontal_cell_lines: str
    vertical_cell_lines: str
    
    # Constraint flags
    flag_allow_empty_wells: bool
    flag_concentrations_on_different_rows: bool
    flag_concentrations_on_different_columns: bool
    flag_replicates_on_different_plates: bool
    flag_replicates_on_same_plate: bool
    compounds_dict: Dict[str, List[Any]]  # {'Drug': [replicates, 'conc1', 'conc2', ...]}
    controls_dict: Dict[str, List[Any]]   # {'Control': [replicates, 'conc1', ...]}
    
    def get_num_rows_int(self) -> int:
        """Convert num_rows to integer."""
        return int(self.num_rows)
    
    def get_num_cols_int(self) -> int:
        """Convert num_cols to integer."""
        return int(self.num_cols)
    
    def get_size_empty_edge_int(self) -> int:
        return int(self.size_empty_edge)

    def get_size_corner_empty_wells_int(self) -> int:
        return int(self.size_corner_empty_wells)

    def get_horizontal_cell_lines_int(self) -> int:
        return int(self.horizontal_cell_lines)

    def get_vertical_cell_lines_int(self) -> int:
        return int(self.vertical_cell_lines)
    
@dataclass(frozen=True)
class ModelVerdict:
    """Validation result for a single MiniZinc model.
    """
    blocked: bool
    messages: List[str]  # each prefixed with "BLOCK: " or "WARN: "

@dataclass(frozen=True)
class ValidationVerdict:
    """Returns the validation verdicts (blocked flags and messages) for both models
    """
    plaid: ModelVerdict
    compd: ModelVerdict
    
    def both_blocked(self) -> bool:
        return self.plaid.blocked and self.compd.blocked
    
    def any_issues(self) -> bool:
        return bool(self.plaid.messages or self.compd.messages)
