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
# Description: Main controller for MPLACE application.
# Orchestrates main window operations and coordinates other controllers.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.2
# Last Revision: December 2025
#

import logging
from typing import List, Optional, Tuple
from config.loader import load_config
from models.application_state import ApplicationState
from models.dto import AppConfig
from core.dzn_parser import scan_dzn
from core.io_utils import read_csv_file
from controllers.dzn_controller import DznController
from controllers.csv_controller import CsvController
from controllers.minizinc_controller import MiniZincController
from controllers.viz_controller import VisualizationController

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
        self.dzn_controller = DznController()
        self.csv_controller = CsvController()
        self.minizinc_controller = MiniZincController(self.app_config)
        self.viz_controller = VisualizationController()
        
        logger.info("MainController initialized")
    
    def load_dzn_file(self, path: str) -> None:
        """
        Load DZN file and update application state.
        
        This scans the DZN file to extract plate dimensions and control names,
        then updates the application state accordingly.
        
        Args:
            path: Path to DZN file to load
            
        Raises:
            FileNotFoundError: If DZN file doesn't exist
            ValueError: If DZN file format is invalid
        """
        logger.info(f"Loading DZN file: {path}")
        
        try:
            # Scan DZN file for metadata
            cols, rows, controls = scan_dzn(path)
            
            # Update state
            self.state.dzn_file_path = path
            self.state.num_cols = cols
            self.state.num_rows = rows
            self.state.control_names = controls
            
            # Add to recent files
            self.state.add_recent_dzn(path)
            
            logger.info(f"DZN loaded successfully: {rows}x{cols} plate with controls {controls}")
            
        except FileNotFoundError as e:
            logger.error(f"DZN file not found: {path}")
            raise FileNotFoundError(f"Could not find DZN file: {path}") from e
        except Exception as e:
            logger.error(f"Failed to load DZN file: {e}")
            raise ValueError(f"Invalid DZN file format: {e}") from e
    
    def parse_dzn_file(self, path: str) -> Tuple[str, str, str]:
        """
        Parse DZN file to extract plate dimensions and controls.
    
        This is a lightweight operation that extracts metadata and then
        updates the application state. Used when loading DZN from disk.
    
        Args:
            path: Path to DZN file
        
        Returns:
            Tuple of (num_cols, num_rows, control_names) as strings
        
        Raises:
            FileNotFoundError: If DZN file doesn't exist
            ValueError: If DZN file format is invalid
        """
        logger.debug(f"Parsing DZN file: {path}")
        try:
            cols, rows, controls = scan_dzn(path)
            self.state.num_cols = cols
            self.state.num_rows = rows
            self.state.control_names = controls
            self.state.dzn_file_path = path
            return (cols, rows, controls)
        except FileNotFoundError as e:
            logger.error(f"DZN file not found: {path}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse DZN file: {e}")
            raise ValueError(f"Invalid DZN file format: {e}") from e
    
    def load_csv_file(self, path: str) -> None:
        """
        Load CSV file and update application state.
        
        This validates that the CSV file can be read and contains data,
        then updates the application state.
        
        Args:
            path: Path to CSV file to load
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV file is empty or invalid
        """
        logger.info(f"Loading CSV file: {path}")
        
        try:
            # Read and validate CSV
            csv_data = read_csv_file(path)
            
            if not csv_data or len(csv_data) == 0:
                raise ValueError("CSV file is empty")
            
            # Update state
            self.state.csv_file_path = path
            
            # Add to recent files
            self.state.add_recent_csv(path)
            
            logger.info(f"CSV loaded successfully: {len(csv_data)} rows")
            
        except FileNotFoundError as e:
            logger.error(f"CSV file not found: {path}")
            raise FileNotFoundError(f"Could not find CSV file: {path}") from e
        except Exception as e:
            logger.error(f"Failed to load CSV file: {e}")
            raise ValueError(f"Invalid CSV file: {e}") from e
    
    def reset_state(self) -> None:
        """
        Reset application to default state.
        
        Clears all loaded files and resets configuration to defaults.
        """
        logger.info("Resetting application state")
        self.state.reset_file_state()
        logger.debug("Application state reset complete")
    
    def can_run_model(self) -> bool:
        """
        Check if MiniZinc model can be executed.
        
        Returns:
            True if a DZN file is loaded, False otherwise
        """
        return self.state.can_run_model()
    
    def can_visualize(self) -> bool:
        """
        Check if visualization can be performed.
        
        Returns:
            True if a CSV file is loaded, False otherwise
        """
        return self.state.can_visualize()
    
    def get_recent_dzn_files(self) -> List[str]:
        """
        Get list of recently opened DZN files.
        
        Returns:
            List of file paths
        """
        return self.state.recent_dzn.copy()
    
    def get_recent_csv_files(self) -> List[str]:
        """
        Get list of recently opened CSV files.
        
        Returns:
            List of file paths
        """
        return self.state.recent_csv.copy()
    
    def get_plate_dimensions(self) -> Tuple[str, str]:
        """
        Get current plate dimensions.
        
        Returns:
            Tuple of (num_rows, num_cols) as strings
        """
        return (self.state.num_rows, self.state.num_cols)
    
    def get_control_names(self) -> str:
        """
        Get control names as string.
        
        Returns:
            String representation of control names list
        """
        return self.state.control_names
    
    def is_using_compd(self) -> bool:
        """
        Check if COMPD model is selected.
        
        Returns:
            True if using COMPD, False if using PLAID
        """
        return self.state.use_compd
    
    def set_model_choice(self, use_compd: bool) -> None:
        """
        Set which model to use (COMPD or PLAID).
        
        Args:
            use_compd: True for COMPD, False for PLAID
        """
        self.state.use_compd = use_compd
        logger.info(f"Model selection changed to: {'COMPD' if use_compd else 'PLAID'}")
