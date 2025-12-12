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
            suggested_name: Suggested filename (without extension)
            
        Returns:
            Path where file was saved, or empty string if cancelled
            
        Raises:
            IOError: If file write fails
        """
        logger.info(f"Exporting PharmBio CSV: {suggested_name}")
        
        try:
            path = write_csv_file(csv_lines, suggested_filename=suggested_name)
            
            if path:
                logger.info(f"PharmBio CSV saved to: {path}")
            else:
                logger.info("PharmBio CSV export cancelled by user")
            
            return path
            
        except Exception as e:
            logger.error(f"Failed to export PharmBio CSV: {e}")
            raise IOError(f"Could not write CSV file: {e}") from e
    
    def export_plater(
        self,
        csv_lines: List[str],
        rows: str,
        cols: str
    ) -> List[str]:
        """
        Export in PLATER CSV format.
        
        PLATER format is a plate-shaped CSV used by the R package 'plater'
        for reading, tidying, and visualizing microtiter plates. Creates
        one file per plate.
        
        Args:
            csv_lines: List of CSV lines in PharmBio format
            rows: Number of plate rows
            cols: Number of plate columns
            
        Returns:
            List of paths where files were saved
            
        Raises:
            ValueError: If conversion fails
            IOError: If file write fails
        """
        logger.info("Exporting PLATER CSV format")
        
        try:
            # Create conversion request
            conversion_input = CSVConversionRequest(
                csv_lines=csv_lines,
                rows=rows,
                cols=cols
            )
            
            # Convert and save
            saved_paths = convert_pharmbio_to_plater(conversion_input)
            
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
