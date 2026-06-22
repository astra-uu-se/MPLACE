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
# Description: CSV import/export controller for MPLACE layout data.
# Manages conversion and export between different CSV formats:
# - PharmBio: Default MPLACE format for visualization and post-processing
# - PLATER: Plate-shaped format compatible with R's plater package
# Coordinates file selection and writing through native dialog interfaces.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.6
# Last Revision: June 2026
#

import logging
from tkinter import filedialog, messagebox
from typing import List, Optional

from models.dto import CSVConversionRequest
from models.constants import FileTypes
from core.io_utils import save_csv_to_path, convert_pharmbio_to_plater

logger = logging.getLogger(__name__)


class CsvController:
    """CSV import/export controller for MPLACE layout data.
    
    Manages conversion and export between different CSV formats:
    - PharmBio: Default MPLACE format for visualization and post-processing
    - PLATER: Plate-shaped format compatible with R's plater package
    
    Coordinates file selection and writing through native dialog interfaces.
    """
    
    def __init__(self):
        """Initialize CSV controller."""
        logger.info("CsvController initialized")
    
    def export_pharmbio(self, csv_lines: List[str], suggested_name: str = '') -> Optional[str]:
        """
        Export in PharmBio CSV format.
    
        This is the default MPLACE format used for visualization
        and post-processing.
    
        Args:
            csv_lines: List of CSV lines to write
            suggested_name: Suggested filename (can include or exclude .csv extension)
        
        Returns:
            Path where file was saved, or None if the user cancelled the dialog
        
        Raises:
            IOError: If file write fails
        """
        if not csv_lines:
            raise ValueError("CSV lines cannot be empty")
        
        logger.info(f"Exporting PharmBio CSV with suggested name: {suggested_name}")
    
        # Ensure suggested_name must not have .csv extension
        if suggested_name.endswith('.'+FileTypes.CSV):
            suggested_name = suggested_name[:-4]
        
        path = filedialog.asksaveasfilename(
                    defaultextension='.'+FileTypes.CSV,
                    filetypes=FileTypes.CSV_FILES,
                    initialfile=suggested_name
                )
        
        if not path:
            logger.info("PharmBio CSV export cancelled by user")
            return None
        
        try:
            save_csv_to_path(csv_lines, path)
            logger.info(f"PharmBio CSV saved to: {path}")
            return path
        except (IOError, OSError) as e:
            logger.error(f"Failed to export PharmBio CSV: {e}")
            raise IOError(f"Could not write CSV file: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during export: {e}")
            raise RuntimeError(f"Unexpected error: {e}") from e
        
    
    def export_plater(self, csv_lines: List[str], rows: str, cols: str) -> Optional[List[str]]:
        """Export in PLATER CSV format.
    
        PLATER format is a plate-shaped CSV used by the R package plater for reading,
        tidying, and visualizing microtiter plates. Creates one file per plate.
    
        Args:
            csv_lines: List of CSV data lines in PharmBio format, *excluding* the header row
            rows: Number of plate rows
            cols: Number of plate columns
        
        Returns:
            List of paths where files were saved, or None if cancelled
        
        Raises:
            ValueError: If conversion fails
            IOError: If file write fails
        """
        if not csv_lines:
            raise ValueError("CSV lines cannot be empty")
            
        logger.info("Exporting PLATER CSV format")
        
        if csv_lines and csv_lines[0].startswith('plateID'):
            logger.warning("export_plater received a header row — stripping it automatically")
            csv_lines = csv_lines[1:]
    
        # Create conversion request
        conversion_input = CSVConversionRequest(
            csv_lines=csv_lines,
            rows=rows,
            cols=cols
        )
        
        # Convert - this returns list of CSV CONTENT strings, not paths!
        plater_data_list = convert_pharmbio_to_plater(conversion_input)
        n = len(plater_data_list)
        logger.info(f"Generated {n} plates to convert and save.")
        
        saved_paths = []
        
        # Save each PLATER CSV file with user dialog
        for i, plater_csv_content in enumerate(plater_data_list):
            # Generate suggested filename
            if len(plater_data_list) == 1:
                suggested_name = "plate_plater.csv"
            else:
                suggested_name = f"layout_plater_{i+1}.csv"
            
            # Save with dialog
            path = filedialog.asksaveasfilename(
                title=f"Save plate {i + 1} of {n}",
                defaultextension='.'+FileTypes.CSV,
                filetypes=FileTypes.CSV_FILES,
                initialfile=suggested_name
            )
            
            if not path:
                # Format the CSV content (ensure proper line endings)
                logger.info(f"User cancelled PLATER save on plate {i+1}/{len(plater_data_list)}")
                if i == 0:
                    return None   # cancelled before saving anything
                else:
                    logger.warning(f"Export stopped after {i+1} of {n} plates; already saved files were kept.")
                    messagebox.showwarning("Warning", f"User cancelled saving on plate {i+1} out of {n}")
                    break         # partial save — return what was saved so far
                                    
            if isinstance(plater_csv_content, str):
                formatted_lines = [line + '\n' if not line.endswith('\n') else line 
                                   for line in plater_csv_content.splitlines()]
            else:
                formatted_lines = plater_csv_content

            try:
                save_csv_to_path(formatted_lines, path)
            except (IOError, OSError) as e:
                logger.error(f"Failed to write PLATER CSV file {i+1}: {e}")
                raise IOError(f"File write error: {e}") from e
            
            saved_paths.append(path)
            logger.info(f"PLATER CSV {i+1}/{len(plater_data_list)} saved: {path}")
        
        logger.info(f"PLATER CSV export completed: {len(saved_paths)} files saved")
        return saved_paths
    