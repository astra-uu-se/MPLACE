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
# Version: 1.3.0
# Last Revision: March 2026
#

import os
import json
import logging
from dataclasses import dataclass, field
from typing import List

from models.constants import PlateDefaults

logger = logging.getLogger(__name__)

# Recent files configuration
MAX_RECENT = 7
RECENT_DZN_PATH = os.path.join(os.path.expanduser("~"), ".mplace_recent_dzn.json")
RECENT_CSV_PATH = os.path.join(os.path.expanduser("~"), ".mplace_recent_csv.json")


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
    recent_dzn: List[str] = field(default_factory=list, init=False)
    recent_csv: List[str] = field(default_factory=list, init=False)
    
    def __post_init__(self) -> None:
        """Load persisted recent files from disk on startup."""
        self.recent_dzn = self._load_recent(RECENT_DZN_PATH)
        self.recent_csv = self._load_recent(RECENT_CSV_PATH)
        logger.debug(f"Loaded {len(self.recent_dzn)} recent DZN, {len(self.recent_csv)} recent CSV")
    
    def add_recent_dzn(self, path: str) -> None:
        """Add a DZN file path to the recent list and persist to disk."""
        self.recent_dzn = self._push_recent(path, self.recent_dzn)
        self._save_recent(RECENT_DZN_PATH, self.recent_dzn)

    def add_recent_csv(self, path: str) -> None:
        """Add a CSV file path to the recent list and persist to disk."""
        self.recent_csv = self._push_recent(path, self.recent_csv)
        self._save_recent(RECENT_CSV_PATH, self.recent_csv)

    def clear_recent_dzn(self) -> None:
        """Clear the DZN recent list and persist the empty state."""
        self.recent_dzn = []
        self._save_recent(RECENT_DZN_PATH, self.recent_dzn)

    def clear_recent_csv(self) -> None:
        """Clear the CSV recent list and persist the empty state."""
        self.recent_csv = []
        self._save_recent(RECENT_CSV_PATH, self.recent_csv)

    def remove_recent_dzn(self, path: str) -> None:
        """Remove a single stale DZN entry and persist."""
        if path in self.recent_dzn:
            self.recent_dzn = [p for p in self.recent_dzn if p != path]
            self._save_recent(RECENT_DZN_PATH, self.recent_dzn)

    def remove_recent_csv(self, path: str) -> None:
        """Remove a single stale CSV entry and persist."""
        if path in self.recent_csv:
            self.recent_csv = [p for p in self.recent_csv if p != path]
            self._save_recent(RECENT_CSV_PATH, self.recent_csv)
    
    def reset_file_state(self) -> None:
        """Reset file paths to empty state."""
        self.dzn_file_path = ''
        self.csv_file_path = ''
    
    @staticmethod
    def _push_recent(path: str, lst: List[str]) -> List[str]:
        """Return a new list with path moved to front, capped at MAX_RECENT."""
        path = os.path.abspath(path)
        updated = [p for p in lst if p != path]
        updated.insert(0, path)
        return updated[:MAX_RECENT]

    @staticmethod
    def _load_recent(json_path: str) -> List[str]:
        """Load and validate a recent-files JSON list from disk."""
        if not os.path.exists(json_path):
            return []
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                resolved = [os.path.abspath(str(p)) for p in data]
                return [p for p in resolved if os.path.exists(p)][:MAX_RECENT]
        except Exception as e:
            logger.warning(f"Could not load recent files from {json_path}: {e}")
        return []

    @staticmethod
    def _save_recent(json_path: str, lst: List[str]) -> None:
        """Persist a recent-files list to disk as JSON."""
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(lst, f, indent=1, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not save recent files to {json_path}: {e}")
