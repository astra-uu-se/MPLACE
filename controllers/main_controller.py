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
# Description: Main controller for MPLACE application.
# Orchestrates main window operations and coordinates other controllers.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.5
# Last Revision: April 2026
#

import logging
from typing import List, Optional, Tuple
from config.loader import load_config
from models.application_state import ApplicationState
from models.dto import AppConfig
from core.dzn_parser import scan_dzn
from core.io_utils import read_csv_file
from core.csv_validator import check_csv_consistency, CsvDiagnostics
from controllers.minizinc_controller import MiniZincController

logger = logging.getLogger(__name__)


class MainController:
    """
    Orchestrates main window operations.
    
    This controller manages the overall application flow, coordinating
    between DZN generation, MiniZinc execution, and CSV handling.
    
    Attributes:
        state: Central application state
    """
    
    def __init__(self, state: ApplicationState):
        """
        Initialize main controller.
        
        Args:
            state: Application state to manage
        """
        self.state = state
        
        # Load configuration from paths.ini
        try:
            self.app_config: AppConfig = load_config()
            logger.info("Configuration loaded successfully")
        except FileNotFoundError as e:
            logger.error(f"Configuration loading failed: {e}")
            raise
        
        # Initialize child controllers (they'll receive config as needed)
        self.minizinc_controller = MiniZincController(self.app_config)
        
        logger.info("MainController initialized")
    
    def parse_dzn_file(self, path: str) -> Tuple[str, str, str]:
        """
        Parse DZN file to extract plate dimensions and controls.
    
        This is a lightweight operation that extracts metadata and then
        updates the application state. Used when loading DZN from disk.
    
        Args:
            path: Path to DZN file
        
        Returns:
            Tuple of (num_rows, num_cols, control_names) as strings (in this specific order)
        
        Raises:
            FileNotFoundError: If DZN file doesn't exist
            ValueError: If DZN file format is invalid
        """
        logger.debug(f"Parsing DZN file: {path}")
        try:
            rows, cols, controls = scan_dzn(path)
            self.state.num_rows = rows
            self.state.num_cols = cols
            self.state.control_names = controls
            self.state.dzn_file_path = path
            return (rows, cols, controls)
        except FileNotFoundError as e:
            logger.error(f"DZN file not found: {path}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse DZN file: {e}")
            raise ValueError(f"Invalid DZN file format: {e}") from e
    
    def load_csv_file(self, path: str) -> Optional[CsvDiagnostics]:
        """
        Load CSV file and update application state, and return consistency diagnostics.
        
        The caller is responsible for surfacing any warnings in diagnostics to the user.
        A non-empty diagnostics.warnings list does not prevent loading — the file is
        always committed to state if it is structurally valid.
        
        Args:
            path: Path to CSV file to load
        
        Returns:
            CsvDiagnostics or None
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV file is empty or invalid
        """
        logger.info(f"Loading CSV file: {path}")
        
        try:
            # Read and validate CSV
            csv_data = read_csv_file(path)
            
            if not csv_data:
                raise ValueError("CSV file is empty")
            
            # Run consistency check only if plate dimensions are known
            diagnostics: Optional[CsvDiagnostics] = None
            try:
                expected_rows = int(self.state.num_rows)
                expected_cols = int(self.state.num_cols)
                if expected_rows > 0 and expected_cols > 0:
                    diagnostics = check_csv_consistency(csv_data, expected_rows, expected_cols)
            except ValueError:
                pass  # dimensions not set or not yet numeric — skip check silently
            
            # Update state
            self.state.csv_file_path = path
            
            # Add to recent files
            self.state.add_recent_csv(path)
            
            logger.info(f"CSV loaded successfully: {len(csv_data)} rows")
            
            return diagnostics
            
        except FileNotFoundError as e:
            logger.error(f"CSV file not found: {path}")
            raise
        except Exception as e:
            logger.error(f"Failed to load CSV file: {e}")
            raise ValueError(f"Invalid CSV file: {e}") from e
