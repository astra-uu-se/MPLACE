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
# Description: Controller for DZN file generation.
# Handles validation and generation of DZN files.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.4
# Last Revision: March 2026
#

import logging
from typing import List, Tuple
from tkinter import filedialog

from models.dzn_data import DznFormData
from models.constants import FileTypes
from models.dto import ValidationVerdict, DznBuildParams
from core.validators import (
    parse_materials_dict,
    validate_materials_schema,
    validate_plate_dimensions
)
from core.dzn_writer import build_dzn_text
from core.model_validator import validate_model_compatibility


logger = logging.getLogger(__name__)


class DznController:
    """
    Controller for DZN file generation.
    
    Handles validation and generation of DZN files for MiniZinc models.
    """
    
    def __init__(self):
        """Initialize DZN controller."""
        logger.info("DznController initialized")
    
    def validate_form_data(self, data: DznFormData) -> List[str]:
        """
        Validate DZN form data.
        
        Performs comprehensive validation matching the original validation logic.
        
        Args:
            data: Form data to validate
            
        Returns:
            List of error messages (empty if valid)
        """
        logger.debug("Validating DZN form data")
        errors = []
        
        # Check for empty fields
        if (data.num_cols == '' or data.num_rows == '' or data.size_empty_edge == '' 
            or data.size_corner_empty_wells == '' or data.horizontal_cell_lines == '' 
            or data.vertical_cell_lines == '' or data.compounds_dict == '' or data.controls_dict == ''):
            errors.append("All fields must be filled in")
        
        # Validate plate dimensions
        if data.num_cols != '' and data.num_rows != '':
            dim_errors = validate_plate_dimensions(data.num_rows, data.num_cols)
            errors.extend(dim_errors)
        
        # Parse and validate compounds - initialize to empty dict
        compounds_dict, parsing_errors = parse_materials_dict(data.compounds_dict)
        errors.extend(parsing_errors)
        
        if not parsing_errors:  # Only validate schema if parsing succeeded
            schema_errors = validate_materials_schema(compounds_dict, "compounds")
            errors.extend(schema_errors)
        
        # Parse and validate controls - initialize to empty dict
        controls_dict, control_parsing_errors = parse_materials_dict(data.controls_dict)
        errors.extend(control_parsing_errors)
        
        if not control_parsing_errors:  # Only validate schema if parsing succeeded
            control_schema_errors = validate_materials_schema(controls_dict, "controls")
            errors.extend(control_schema_errors)
        
        # Validate that at least one material exists
        # Only check if parsing didn't fail
        if not parsing_errors and not control_parsing_errors:
            if not compounds_dict and not controls_dict:
                errors.append("Must specify at least one compound or control")
        
        if errors:
            logger.warning(f"Validation failed with {len(errors)} errors")
        else:
            logger.debug("Validation passed")
        
        return errors
    
    def generate_dzn_content(self, data: DznFormData, verdict: ValidationVerdict) -> Tuple[str, List[str]]:
        """
        Generate DZN file content from form data.
        
        Args:
            data: Validated form data
            verdict: a list of messages pertaning on whether this file is compatible with various models
            
        Returns:
            Tuple of (dzn_text, control_names_list)
            
        Raises:
            ValueError: If data is invalid or generation fails
        """
        logger.info("Generating DZN content")
        
        # Create build parameters
        try:
            dzn_text, control_names = build_dzn_text(self._build_params(data), verdict)
            logger.info(f"DZN content generated successfully with {len(control_names)} controls")
            return dzn_text, control_names
            
        except Exception as e:
            logger.error(f"Failed to generate DZN content: {e}")
            raise ValueError(f"DZN generation failed: {e}") from e
    
    def save_dzn_file(self, content: str, suggested_name: str = 'layout.dzn') -> str:
        """
        Save DZN content to file via dialog.
        
        Args:
            content: DZN file content
            suggested_name: Suggested filename
            
        Returns:
            Path to saved file, or empty string if cancelled
            
        Raises:
            IOError: If file write fails
        """
        path = filedialog.asksaveasfilename(
            defaultextension=".dzn",
            filetypes=FileTypes.DZN_FILES,
            initialfile=suggested_name
        )
        
        if not path:
            logger.info("DZN save cancelled by user")
            return ''
        
        try:
            with open(path, "w", encoding="utf-8") as dzn_file:
                dzn_file.write(content)
            
            logger.info(f"DZN file saved: {path}, {len(content)} characters")
            return path
            
        except (IOError, OSError) as e:
            logger.error(f"DZN write failed: {path}, error: {e}")
            raise IOError(f"Failed to write DZN file: {str(e)}") from e

    def validate_model_compat(self, data: DznFormData) -> ValidationVerdict:
        """
        Run model-compatibility checks against PLAID and COMPD constraint logic.

        Must be called after validate_form_data() passes, as it assumes
        all fields are parseable.

        Args:
            data: Validated form data

        Returns:
            ValidationVerdict with per-model blocked status and messages
        """
        logger.debug("Running model compatibility validation")

        verdict = validate_model_compatibility(self._build_params(data))
        logger.info(
            f"Model compat: PLAID={'BLOCKED' if verdict.plaid.blocked else 'OK'}, "
            f"COMPD={'BLOCKED' if verdict.compd.blocked else 'OK'}"
        )
        return verdict
    
    def _build_params(self, data: DznFormData) -> DznBuildParams:
        """
        Build a DznBuildParams from validated form data.

        Must only be called after validate_form_data() has passed, as it
        assumes all fields are parseable.

        Args:
            data: Validated form data

        Returns:
            DznBuildParams ready for DZN generation or model compatibility checks
        """
        compounds_dict, _ = parse_materials_dict(data.compounds_dict)
        controls_dict, _  = parse_materials_dict(data.controls_dict)

        return DznBuildParams(
            num_rows=data.num_rows,
            num_cols=data.num_cols,
            inner_empty_edge=data.inner_empty_edge,
            size_empty_edge=data.size_empty_edge,
            size_corner_empty_wells=data.size_corner_empty_wells,
            horizontal_cell_lines=data.horizontal_cell_lines,
            vertical_cell_lines=data.vertical_cell_lines,
            flag_allow_empty_wells=data.flag_allow_empty_wells,
            flag_concentrations_on_different_rows=data.flag_concentrations_on_different_rows,
            flag_concentrations_on_different_columns=data.flag_concentrations_on_different_columns,
            flag_replicates_on_different_plates=data.flag_replicates_on_different_plates,
            flag_replicates_on_same_plate=data.flag_replicates_on_same_plate,
            compounds_dict=compounds_dict,
            controls_dict=controls_dict
        )