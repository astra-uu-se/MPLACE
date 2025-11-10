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
# Description:  Various supplementary utilities related to running MiniZinc models
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.0
# Last Revision: October 2025
#


import sys
import time
import logging
import subprocess

from typing import List, Dict, Tuple, Union, Sequence

from models.constants import PathsIni


logger = logging.getLogger(__name__)


def run_model(minizinc_path: str, solver_config: str, model_file: str, data_file: str) -> str:
    """Execute MiniZinc command and return output.
    
    Args:
        minizinc_path: Path to MiniZinc executable
        solver_config: Solver configuration file path
        model_file: Model file path (.mzn)
        data_file: Data file path (.dzn)
        
    Returns:
        Command output as string
        
    Raises:
        RuntimeError: If MiniZinc command execution fails
    """
    if solver_config == PathsIni.FILE_ERROR_PLACEHOLDER:
        solver_config = ' --solver gecode'
        logger.info('Using Gecode, 1 thread')
    else:
        solver_config = ' --param-file-no-push ' + solver_config
    
    if sys.platform.startswith('win'):
        cmd = [minizinc_path, solver_config, model_file, data_file]
    else:
        cmd = [minizinc_path + solver_config + ' ' + model_file + ' ' + data_file]
    
    print('command:', cmd)
    logger.info(f"Executing MiniZinc: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    
    start_time = time.time()
    
    try:
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = process.communicate()
        output = output.decode('utf-8').strip()
        errors = errors.decode('utf-8').strip()
        process.kill()
    except (subprocess.SubprocessError, OSError) as e:
        logger.error(f"MiniZinc execution failed: {e}")
        raise RuntimeError(f"Failed to execute MiniZinc command: {e}") from e

    elapsed = time.time() - start_time
    
    # Check process return code
    if process.returncode != 0:
        error_msg = f"MiniZinc failed with exit code {process.returncode}"
        if errors:
            error_msg += f": {errors.strip()}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    if errors:
        print(errors)  # User sees warnings/errors
        logger.warning(f"MiniZinc stderr: {errors}")
    if output:
        print(output)  # User sees output
        logger.debug(f"MiniZinc stdout: {output}")

    print(f'MiniZinc completed in {elapsed:.1f} seconds')
    logger.info(f"MiniZinc execution completed in {elapsed:.1f} seconds")

    return output
