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
# Description:  Various supplementary utilities related to running MiniZinc models
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.4
# Last Revision: March 2026
#


import sys
import time
import logging
import subprocess
import typing

from models.constants import PathsIni, Messages

logger = logging.getLogger(__name__)

def _build_command(minizinc_path: str, solver_config: str, model_file: str, data_file: str):
    """Build the platform-appropriate MiniZinc shell command.

    On Windows, arguments are passed as a proper list so that subprocess can
    quote paths correctly.  On all other platforms the arguments are
    concatenated into a single string, which is required because the solver
    config is embedded as a flag string (e.g. ' --solver gecode') rather than
    a standalone path, and subprocess with shell=True on POSIX expects a single
    string in that case.

    If solver_config equals PathsIni.FILE_ERROR_PLACEHOLDER (i.e. no .mpc file
    was found), the function falls back to Gecode with a single thread.

    Args:
        minizinc_path: Path to the MiniZinc executable (or 'minizinc' if on PATH)
        solver_config: Path to a .mpc solver configuration file, or
                       PathsIni.FILE_ERROR_PLACEHOLDER to use the Gecode default
        model_file: Path to the .mzn model file
        data_file: Path to the .dzn data file

    Returns:
        A list suitable for passing to subprocess.Popen with shell=True:
        - On Windows: [minizinc_path, solver_flags, model_file, data_file]
        - On POSIX:   [full_command_string]
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
    
    return cmd


def run_model(minizinc_path: str, solver_config: str, model_file: str, data_file: str) -> str:
    """Execute MiniZinc command and return stdout text.
    
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
    cmd = _build_command(minizinc_path, solver_config, model_file, data_file)
    logger.info(f"Executing MiniZinc: {' '.join(cmd) if isinstance(cmd, list) else cmd}")

    start_time = time.time()

    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output, errors = process.communicate()

    except FileNotFoundError as e:
        logger.error("MiniZinc executable not found: %s", minizinc_path)
        raise FileNotFoundError(
            f"MiniZinc executable not found: {minizinc_path}. "
            f"Check paths.ini and ensure MiniZinc is installed."
        ) from e
    except (subprocess.SubprocessError, OSError) as e:
        logger.error("MiniZinc execution failed: %s", e)
        raise RuntimeError(f"Failed to execute MiniZinc command: {e}") from e

    elapsed = time.time() - start_time
    output = output.strip()
    errors = errors.strip()

    if process.returncode != 0:
        hint = Messages.MINIZINC_EXIT_CODE_HINTS.get(process.returncode, "No additional diagnostic hint available.")
        message_parts = [
            f"MiniZinc failed with exit code {process.returncode}.",
            hint
        ]
        if errors:
            message_parts.append(f"stderr: {errors}")
        if output:
            message_parts.append(f"stdout: {output}")
        error_msg = "\n".join(message_parts)

        logger.error(error_msg)
        raise RuntimeError(error_msg)

    if errors:
        logger.warning("MiniZinc stderr: %s", errors)

    logger.info("MiniZinc execution completed in %.1f seconds", elapsed)
    return output
