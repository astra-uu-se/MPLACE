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
# Description: Controller for DZN file generation.
# Handles validation and generation of DZN files.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.2
# Last Revision: December 2025
#

import logging
from typing import List, Tuple
from models.dzn_data import DznFormData
from models.dto import DznBuildParams, DznGenerationResult
from core.validators import (
    validate_plate_dimensions,
    parse_materials_dict,
    validate_materials_schema,
    format_validation_errors
)
from core.dzn_writer import build_dzn_text

logger = logging.getLogger(__name__)


class DznController:
    """
    Handles DZN generation logic.
    
    This controller validates form data and generates DZN file content
    without any direct UI manipulation.
    """
    
    def __init__(self):
        """Initialize DZN controller."""
        logger.info("DznController initialized")
    
    def validate_form_data(self, data: DznFormData) -> List[str]:
        """
        Validate DZN form data.
        
        Performs comprehensive validation of all form inputs including
        plate dimensions, materials dictionaries, and constraint flags.
        
        Args:
            data: Form data to validate
            
        Returns:
            List of error messages (empty if valid)
        """
        logger.debug("Validating DZN form data")
        errors = []
        
        # Validate plate dimensions
        dim_errors = validate_plate_dimensions(data.num_rows, data.num_cols)
        errors.extend(dim_errors)
        
        # Validate compounds
        compounds, parse_errors = parse_materials_dict(data.compounds_dict)
        errors.extend(parse_errors)
        
        if not parse_errors:
            schema_errors = validate_materials_schema(compounds, "compounds")
            errors.extend(schema_errors)
        
        # Validate controls
        controls, parse_errors = parse_materials_dict(data.controls_dict)
        errors.extend(parse_errors)
        
        if not parse_errors:
            schema_errors = validate_materials_schema(controls, "controls")
            errors.extend(schema_errors)
        
        # Validate that at least one material exists
        if not compounds and not controls:
            errors.append("Must specify at least one compound or control")
        
        # Validate conflicting flags
        if data.flag_replicates_on_different_plates and data.flag_replicates_on_same_plate:
            errors.append("Cannot have replicates on both different plates AND same plate")
        
        if data.flag_concentrations_on_different_rows and data.flag_concentrations_on_different_columns:
            errors.append("Cannot have concentrations on both different rows AND different columns")
        
        if errors:
            logger.warning(f"Validation failed with {len(errors)} errors")
        else:
            logger.debug("Validation passed")
        
        return errors
    
    def generate_dzn_content(self, data: DznFormData) -> Tuple[str, List[str]]:
        """
        Generate DZN file content from form data.
        
        Args:
            data: Validated form data
            
        Returns:
            Tuple of (dzn_text, control_names_list)
            
        Raises:
            ValueError: If data is invalid or generation fails
        """
        logger.info("Generating DZN content")
        
        # Create build parameters
        params = DznBuildParams(
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
            compounds_dict=data.compounds_dict,
            controls_dict=data.controls_dict
        )
        
        try:
            dzn_text, control_names = build_dzn_text(params)
            logger.info(f"DZN content generated successfully with {len(control_names)} controls")
            return dzn_text, control_names
            
        except Exception as e:
            logger.error(f"Failed to generate DZN content: {e}")
            raise ValueError(f"DZN generation failed: {e}") from e
    
    def create_generation_result(
        self,
        file_path: str,
        rows: str,
        cols: str,
        control_names: List[str]
    ) -> DznGenerationResult:
        """
        Create a DZN generation result object.
        
        Args:
            file_path: Path where DZN was saved
            rows: Number of rows
            cols: Number of columns
            control_names: List of control names
            
        Returns:
            DznGenerationResult object
        """
        return DznGenerationResult(
            file_path=file_path,
            rows=rows,
            cols=cols,
            control_names=str(control_names)
        )
