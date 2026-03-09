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
# Description: Application state models for MPLACE.
# Centralizes all application state that was previously scattered across tk.StringVar variables.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.2.6
# Last Revision: March 2026
#

from dataclasses import dataclass, field
from typing import List

from models.constants import PlateDefaults


@dataclass
class ApplicationState:
    """
    Central application state - replaces scattered tk.StringVar variables.
    
    This class holds all the application's runtime state in a single,
    testable structure without any Tkinter dependencies.
    
    Attributes:
        dzn_file_path: Path to the currently loaded DZN file
        csv_file_path: Path to the currently loaded CSV file
        num_rows: Number of rows in the microplate (as string for form compatibility)
        num_cols: Number of columns in the microplate (as string for form compatibility)
        control_names: String representation of control names list
        use_compd: Whether to use COMPD model (True) or PLAID model (False)
        recent_dzn: List of recently opened DZN file paths
        recent_csv: List of recently opened CSV file paths
    """
    
    # File paths
    dzn_file_path: str = ''
    csv_file_path: str = ''
    
    # Plate configuration
    num_rows: str = PlateDefaults.ROWS
    num_cols: str = PlateDefaults.COLS
    control_names: str = '[]'
    
    # Model selection
    use_compd: bool = False
    
    # Recent files
    recent_dzn: List[str] = field(default_factory=list)
    recent_csv: List[str] = field(default_factory=list)
    
    def reset_file_state(self) -> None:
        """Reset file paths to empty state."""
        self.dzn_file_path = ''
        self.csv_file_path = ''
    
    def has_dzn_loaded(self) -> bool:
        """Check if a DZN file is currently loaded."""
        return bool(self.dzn_file_path)
    
    def has_csv_loaded(self) -> bool:
        """Check if a CSV file is currently loaded."""
        return bool(self.csv_file_path)
    
    def can_run_model(self) -> bool:
        """Check if model can be run (DZN file loaded)."""
        return self.has_dzn_loaded()
    
    def can_visualize(self) -> bool:
        """Check if visualization can be performed (CSV file loaded)."""
        return self.has_csv_loaded()
    
    def add_recent_dzn(self, path: str, max_recent: int = 10) -> None:
        """
        Add a DZN file to recent files list.
        
        Args:
            path: File path to add
            max_recent: Maximum number of recent files to keep
        """
        if path in self.recent_dzn:
            self.recent_dzn.remove(path)
        self.recent_dzn.insert(0, path)
        self.recent_dzn = self.recent_dzn[:max_recent]
    
    def add_recent_csv(self, path: str, max_recent: int = 10) -> None:
        """
        Add a CSV file to recent files list.
        
        Args:
            path: File path to add
            max_recent: Maximum number of recent files to keep
        """
        if path in self.recent_csv:
            self.recent_csv.remove(path)
        self.recent_csv.insert(0, path)
        self.recent_csv = self.recent_csv[:max_recent]
