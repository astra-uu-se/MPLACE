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
# Description: Controller for MiniZinc model execution.
# Handles running constraint programming models and processing output.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.1
# Last Revision: March 2026
#

import logging
import json
from typing import List, Optional
from models.constants import PathsIni
from models.dto import AppConfig
from core.minizinc_runner import run_model as run_minizinc_model
from core.io_utils import extract_csv_text

logger = logging.getLogger(__name__)


class MiniZincController:
    """
    Handles MiniZinc execution.
    
    This controller runs MiniZinc models and processes their output
    without any UI dependencies.
    """
    
    def __init__(self, app_config: AppConfig):
        """Initialize MiniZinc controller with application configuration.
        
        Args:
            app_config: Configuration loaded from paths.ini containing
                       paths to MiniZinc executable and model files
        """
        self.app_config = app_config
        logger.info("MiniZincController initialized with config")
    
    def run_plaid_model(self, dzn_file: str) -> str:
        """
        Execute PLAID model with configured paths.
        
        Args:
            dzn_file: Path to data file (.dzn)
            
        Returns:
            Raw MiniZinc output as string
            
        Raises:
            RuntimeError: If MiniZinc execution fails
            FileNotFoundError: If any required file is missing
        """
        logger.info(f"Running PLAID model with DZN: {dzn_file}")
        
        return self.run_model(
            minizinc_path=self.app_config.minizinc_path,
            solver_config=self.app_config.plaid_mpc_path,
            model_file=self.app_config.plaid_path,
            dzn_file=dzn_file
        )
    
    def run_compd_model(self, dzn_file: str) -> str:
        """
        Execute COMPD model with configured paths.
        
        Args:
            dzn_file: Path to data file (.dzn)
            
        Returns:
            Raw MiniZinc output as string
            
        Raises:
            RuntimeError: If MiniZinc execution fails
            FileNotFoundError: If any required file is missing
        """
        logger.info(f"Running COMPD model with DZN: {dzn_file}")
        
        return self.run_model(
            minizinc_path=self.app_config.minizinc_path,
            solver_config=self.app_config.compd_mpc_path,
            model_file=self.app_config.compd_path,
            dzn_file=dzn_file
        )
    
    def run_model(
        self,
        minizinc_path: str,
        solver_config: str,
        model_file: str,
        dzn_file: str
    ) -> str:
        """
        Execute MiniZinc model with specified paths.
        
        Args:
            minizinc_path: Path to MiniZinc executable
            solver_config: Path to solver configuration file (.mpc)
            model_file: Path to model file (.mzn)
            dzn_file: Path to data file (.dzn)
            
        Returns:
            Raw MiniZinc output as string
            
        Raises:
            RuntimeError: If MiniZinc execution fails
            FileNotFoundError: If any required file is missing
        """
        logger.info(f"Running MiniZinc model: {model_file}")
        logger.debug(f"MiniZinc path: {minizinc_path}")
        logger.debug(f"Solver config: {solver_config}, DZN: {dzn_file}")
        
        try:
            output = run_minizinc_model(minizinc_path, solver_config, model_file, dzn_file)
            logger.info("MiniZinc execution completed successfully")
            return output
            
        except FileNotFoundError as e:
            logger.error(f"Required file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"MiniZinc execution failed: {e}")
            raise RuntimeError(f"Model execution failed: {e}") from e
    
    def extract_csv_from_output(self, output: str) -> List[str]:
        """
        Extract CSV lines from MiniZinc output.
        
        The MiniZinc output contains various diagnostic information
        along with the CSV data. This method extracts just the CSV lines.
        
        Args:
            output: Raw MiniZinc output
            
        Returns:
            List of CSV lines
            
        Raises:
            ValueError: If no CSV data found in output
        """
        logger.debug("Extracting CSV from MiniZinc output")
        
        try:
            csv_lines = extract_csv_text(output)
            
            if not csv_lines:
                raise ValueError("No CSV data found in MiniZinc output")
            
            logger.info(f"Extracted {len(csv_lines)} CSV lines")
            return csv_lines
            
        except Exception as e:
            logger.error(f"Failed to extract CSV: {e}")
            raise ValueError(f"Could not extract CSV from output: {e}") from e
    
    def get_timeout(self, use_compd: bool) -> Optional[int]:
        """Return timeout in seconds for the selected model."""
        if use_compd:
            return self._parse_timeout_s(self.app_config.compd_mpc_path)
        else:
            return self._parse_timeout_s(self.app_config.plaid_mpc_path)
    
    def _parse_timeout_s(self, mpc_path: str = PathsIni.FILE_ERROR_PLACEHOLDER) -> Optional[int]:
        """Return timeout in seconds from a MiniZinc .mpc file, or None if absent/unreadable."""
        if mpc_path == PathsIni.FILE_ERROR_PLACEHOLDER:
            return None
        try:
            with open(mpc_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            ms = data.get("time-limit")
            return int(ms) // 1000 if ms is not None else None
        except Exception:
            return None