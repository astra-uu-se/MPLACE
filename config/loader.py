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
# Description:  Various supplementary utilities related to reading the config file
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.1
# Last Revision: November 2025
#


import os
import logging

from pathlib import Path
from typing import Tuple, List

from models.constants import Performance, Validation, PathsIni, Visualization
from models.dto import AppConfig


logger = logging.getLogger(__name__)


def load_config() -> AppConfig:
    """Read and parse paths.ini configuration file.
    
    Returns:
        Validated AppConfig object
        
    Raises:
        FileNotFoundError: If paths.ini file cannot be read
    """
    logger.debug("Loading configuration from paths.ini")
    try:
        with open('config/paths.ini', 'r') as file:
            paths_array = file.readlines()
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Cannot read paths.ini file: {e}")
        raise FileNotFoundError("Could not read paths.ini file. Please ensure it exists and is readable.") from e
    
    # Initialize variables with defaults
    minizinc_path = plaid_path = compd_path = plaid_mpc_path = compd_mpc_path = ""
    
    for line in paths_array:
        line_clean = line.strip()
        if len(line_clean) == 0:
            pass
        elif line_clean[0] == "#":
            pass
        else:
            try:
                [left_side, right_side] = line_clean.split('=')
                left_side = left_side.strip()
                right_side = right_side.strip()
            except:
                raise ValueError(line_clean)
            
            if left_side == PathsIni.MINIZINC_PREFIX:
                minizinc_path = right_side.strip()[1:-1]
            elif left_side == PathsIni.PLAID_PREFIX:
                plaid_path = right_side.strip()[1:-1]
            elif left_side == PathsIni.COMPD_PREFIX:
                compd_path = right_side.strip()[1:-1]
            elif left_side == PathsIni.PLAID_MPC_PREFIX:
                plaid_mpc_path = right_side.strip()[1:-1]
            elif left_side == PathsIni.COMPD_MPC_PREFIX:
                compd_mpc_path = right_side.strip()[1:-1]
        
    # CONFIG VALIDATION:
    # Validate configuration and, if necessary, upload empty strings to signify missing functionality
    validation_errors: List[str] = []
    
    # Validate MiniZinc path (must be executable)
    if not minizinc_path or not minizinc_path.strip():
        validation_errors.append("MiniZinc path is empty or not set")
        minizinc_path = PathsIni.FILE_ERROR_PLACEHOLDER
    elif not path_exists(minizinc_path):
        validation_errors.append(f"MiniZinc executable not found at: '{minizinc_path}'")
        minizinc_path = PathsIni.FILE_ERROR_PLACEHOLDER
    elif not is_executable(minizinc_path):
        validation_errors.append(f"MiniZinc path exists but is not executable: '{minizinc_path}'")
        minizinc_path = PathsIni.FILE_ERROR_PLACEHOLDER
    print(validation_errors)
    
    # Validate model and config files (must exist and be readable)
    validation_errors, plaid_path = file_check(validation_errors, "PLAID model file", plaid_path)
    validation_errors, compd_path = file_check(validation_errors, "COMPD model file", compd_path)
    validation_errors, plaid_mpc_path = file_check(validation_errors, "PLAID solver config", plaid_mpc_path)
    validation_errors, compd_mpc_path = file_check(validation_errors, "COMPD solver config", compd_mpc_path)
    
    if validation_errors:
        # Format user-friendly error message
        numbered_errors = '\n'.join(f"  {i+1}. {error}" for i, error in enumerate(validation_errors))
        error_msg = (
            "Configuration validation failed:\n\n"
            f"{numbered_errors}\n\n"
            "Please check your config/paths.ini file and ensure all paths are correct.\n"
            "Common solutions:\n"
            "  • Install MiniZinc and update the path\n"
            "  • Check that all .mzn and .mpc files exist\n"
            "  • Verify file permissions are readable"
        )
        
    app_config = AppConfig(minizinc_path= minizinc_path,
                           plaid_path = plaid_path,
                           compd_path = compd_path,
                           plaid_mpc_path = plaid_mpc_path,
                           compd_mpc_path = compd_mpc_path)
    
    logger.info("Configuration loaded successfully from paths.ini")
    
    return app_config


def path_exists(path_str: str) -> bool:
    """Helper function for file existence checks
    
    Args:
        file path
    
    Returns:
        Boolean flag denoting the existing of a path
    """
    if not path_str or not path_str.strip():
        return False
    try:
        return Path(path_str).exists()
    except (OSError, ValueError):
        return False


def is_executable(path_str: str) -> bool:
    """Helper function for file being an executable checks
    
    Args:
        file path
    
    Returns:
        Boolean flag denoting the existing of whether or not the file is an executable
    """
    if not path_exists(path_str):
        return False
    try:
        path_obj = Path(path_str)
        # On Windows, check if it's a .exe file or has executable permission
        if os.name == 'nt':
            return path_obj.suffix.lower() in ['.exe', '.bat', '.cmd'] or os.access(path_obj, os.X_OK)
        else:
            return os.access(path_obj, os.X_OK)
    except (OSError, ValueError):
        return False


def file_check(errors: List[str], file_desc: str, file_path: str) -> Tuple[List[str], str]:
    """Helper function for througuhly checking a file path and, if failed, updating the error list
    
    Args:
        initial error list, file path
        file description (for printing errors)
        file path
    
    Returns:
        an updated error list
        an updated file path
    """
    if not file_path or not file_path.strip():
        return errors + [f"{file_desc} path is empty or not set"], PathsIni.FILE_ERROR_PLACEHOLDER
    elif not path_exists(file_path):
        return errors + [f"{file_desc} not found at: '{file_path}'"], PathsIni.FILE_ERROR_PLACEHOLDER
    # Optional: check if file is readable
    elif not os.access(Path(file_path), os.R_OK):
        return errors + [f"{file_desc} exists but is not readable: '{file_path}'"], PathsIni.FILE_ERROR_PLACEHOLDER
    return errors, file_path