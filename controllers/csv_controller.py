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
# Description: Controller for CSV import/export operations.
# Handles CSV file format conversions and exports.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.2
# Last Revision: December 2025
#

import logging
from typing import List
from models.dto import CSVConversionRequest
from core.io_utils import write_csv_file, convert_pharmbio_to_plater

logger = logging.getLogger(__name__)


class CsvController:
    """
    Handles CSV import/export operations.
    
    This controller manages different CSV formats (PharmBio, PLATER)
    and handles file writing operations.
    """
    
    def __init__(self):
        """Initialize CSV controller."""
        logger.info("CsvController initialized")
    
    def export_pharmbio(self, csv_lines: List[str], suggested_name: str = '') -> str:
        """
        Export in PharmBio CSV format.
    
        This is the default MPLACE format used for visualization
        and post-processing.
    
        Args:
            csv_lines: List of CSV lines to write
            suggested_name: Suggested filename (can include or exclude .csv extension)
        
        Returns:
            Path where file was saved, or empty string if cancelled, or '-2' if write failed
        
        Raises:
            IOError: If file write fails
        """
        logger.info(f"Exporting PharmBio CSV with suggested name: {suggested_name}")
    
        # Ensure suggested_name doesn't have .csv extension (write_csv_file adds it)
        if suggested_name.endswith('.csv'):
            suggested_name = suggested_name[:-4]
    
        try:
            # write_csv_file returns: path (string), -1 (cancelled), or -2 (error)
            result = write_csv_file(csv_lines, suggested_filename=suggested_name)
        
            if result == -1:
                logger.info("PharmBio CSV export cancelled by user")
                return ""
            elif result == -2:
                logger.error("Failed to write PharmBio CSV file")
                return "-2"
            else:
                logger.info(f"PharmBio CSV saved to: {result}")
                return result
            
        except Exception as e:
            logger.error(f"Failed to export PharmBio CSV: {e}")
            raise IOError(f"Could not write CSV file: {e}") from e
    
    def export_plater(self, csvlines: List[str], rows: str, cols: str) -> List[str]:
        """Export in PLATER CSV format.
    
        PLATER format is a plate-shaped CSV used by the R package plater for reading,
        tidying, and visualizing microtiter plates. Creates one file per plate.
    
        Args:
            csvlines: List of CSV lines in PharmBio format
            rows: Number of plate rows
            cols: Number of plate columns
        
        Returns:
            List of paths where files were saved (empty list if cancelled)
        
        Raises:
            ValueError: If conversion fails
            IOError: If file write fails
        """
        from models.dto import CSVConversionRequest
        from core.io_utils import convert_pharmbio_to_plater, write_csv_file
        import os
    
        logger.info("Exporting PLATER CSV format")
    
        try:
            # Create conversion request
            conversion_input = CSVConversionRequest(
                csv_lines=csvlines,
                rows=rows,
                cols=cols
            )
        
            # Convert - this returns list of CSV CONTENT strings, not paths!
            plater_data_list = convert_pharmbio_to_plater(conversion_input)
            logger.info(f"Generated {len(plater_data_list)} plates to convert and save.")
        
            saved_paths = []
        
            # Save each PLATER CSV file with user dialog
            for i, plater_csv_content in enumerate(plater_data_list):
                # Format the CSV content (ensure proper line endings)
                if isinstance(plater_csv_content, str):
                    csv_lines = [line + '\n' if not line.endswith('\n') else line 
                               for line in plater_csv_content.splitlines()]
                else:
                    csv_lines = plater_csv_content
            
                # Generate suggested filename
                if len(plater_data_list) == 1:
                    suggested_name = "plate_plater.csv"
                else:
                    suggested_name = f"plate_{i+1}_plater.csv"
            
                # Save with dialog
                path = write_csv_file(csv_lines, suggested_filename=suggested_name)
            
                if path == -1:  # User cancelled
                    logger.info(f"User cancelled PLATER save on plate {i+1}/{len(plater_data_list)}")
                    if i == 0:
                        return []  # Cancel everything if first file cancelled
                    else:
                        break  # Stop saving remaining files
                elif path == -2:  # Write error
                    logger.error(f"Failed to write PLATER CSV file {i+1}")
                    return []
            
                saved_paths.append(path)
                logger.info(f"PLATER CSV {i+1}/{len(plater_data_list)} saved: {path}")
        
            logger.info(f"PLATER CSV export completed: {len(saved_paths)} files saved")
            return saved_paths
        
        except ValueError as e:
            logger.error(f"PLATER conversion failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to export PLATER CSV: {e}")
            raise IOError(f"Could not write PLATER files: {e}") from e
    
    def validate_csv_lines(self, csv_lines: List[str]) -> bool:
        """
        Validate that CSV lines are properly formatted.
        
        Args:
            csv_lines: CSV lines to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not csv_lines:
            logger.warning("CSV validation failed: empty lines")
            return False
        
        if len(csv_lines) < 2:  # Need at least header + 1 data row
            logger.warning("CSV validation failed: insufficient rows")
            return False
        
        logger.debug("CSV validation passed")
        return True
