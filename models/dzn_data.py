# Copyright 2025 Ramiz Gindullin.
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
# Description: Data models for DZN file generation.
# Represents the form data needed to generate a DZN file.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.2
# Last Revision: December 2025
#

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class DznFormData:
    """
    Data structure for DZN generation form.
    
    This represents all the user inputs from the DZN generation window.
    All fields are kept as strings or their direct form types to match
    the UI layer without conversion logic.
    
    Attributes:
        num_rows: Number of plate rows
        num_cols: Number of plate columns
        inner_empty_edge: Whether to have inner empty edge
        size_empty_edge: Size of empty edge (as string)
        size_corner_empty_wells: Size of corner empty wells (as string)
        horizontal_cell_lines: Horizontal cell line positions (as string)
        vertical_cell_lines: Vertical cell line positions (as string)
        flag_allow_empty_wells: Allow empty wells in layout
        flag_concentrations_on_different_rows: Force concentrations on different rows
        flag_concentrations_on_different_columns: Force concentrations on different columns
        flag_replicates_on_different_plates: Force replicates on different plates
        flag_replicates_on_same_plate: Force replicates on same plate
        compounds_dict: Dictionary of compounds and their concentrations
        controls_dict: Dictionary of controls and their concentrations
    """
    num_rows: str
    num_cols: str
    inner_empty_edge: bool
    size_empty_edge: str
    size_corner_empty_wells: str
    horizontal_cell_lines: str
    vertical_cell_lines: str
    flag_allow_empty_wells: bool
    flag_concentrations_on_different_rows: bool
    flag_concentrations_on_different_columns: bool
    flag_replicates_on_different_plates: bool
    flag_replicates_on_same_plate: bool
    compounds_dict: str
    controls_dict: str


@dataclass
class DznBuildParams:
    """Parameters for building DZN file content."""
    num_rows: str
    num_cols: str
    inner_empty_edge: bool
    size_empty_edge: str
    size_corner_empty_wells: str
    horizontal_cell_lines: str
    vertical_cell_lines: str
    flag_allow_empty_wells: bool
    flag_concentrations_on_different_rows: bool
    flag_concentrations_on_different_columns: bool
    flag_replicates_on_different_plates: bool
    flag_replicates_on_same_plate: bool
    compounds_dict: Dict[str, List[Any]]
    controls_dict: Dict[str, List[Any]]
    
    def get_num_rows_int(self) -> int:
        """Convert num_rows to integer."""
        return int(self.num_rows)
    
    def get_num_cols_int(self) -> int:
        """Convert num_cols to integer."""
        return int(self.num_cols)
