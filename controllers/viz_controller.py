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
# Description: Controller for visualization operations.
# Orchestrates data preparation and figure generation for plate layouts.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.2
# Last Revision: December 2025
#

import logging
import ast
from typing import List, Dict, Any, Tuple
from models.csv_data import VisualizationState
from core.io_utils import read_csv_file
from core.layout_utils import find_all_plates_concentrations
from core.layout_utils import transform_concentrations_to_alphas
from models.constants import Visualization

logger = logging.getLogger(__name__)


class VisualizationController:
    """
    Orchestrates visualization logic.
    
    This controller prepares data for visualization and coordinates
    figure export operations without direct matplotlib manipulation.
    """
    
    def __init__(self):
        """Initialize visualization controller."""
        logger.info("VisualizationController initialized")
    
    def prepare_visualization(
        self,
        csv_path: str,
        template: str,
        rows: str,
        cols: str,
        controls: str
    ) -> VisualizationState:
        """
        Prepare visualization data from CSV file.
        
        This loads the CSV, parses layouts, precomputes alpha mappings
        and material colors, then returns a complete visualization state.
        
        Args:
            csv_path: Path to CSV file
            template: Template for naming figures
            rows: Number of plate rows (as string)
            cols: Number of plate columns (as string)
            controls: String representation of control names list
            
        Returns:
            VisualizationState ready for rendering
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        logger.info(f"Preparing visualization from: {csv_path}")
        
        try:
            # Read CSV
            text_array = read_csv_file(csv_path)
            
            # Parse layouts and concentrations
            layouts_dict, concentrations_list = find_all_plates_concentrations(text_array)
            
            logger.info(f"Found {len(layouts_dict)} layouts with {len(concentrations_list)} materials")
            
            # Precompute alpha mappings for performance
            alpha_mappings = {}
            for material, concentrations in concentrations_list.items():
                alpha_mappings[material] = transform_concentrations_to_alphas(concentrations)
            
            # Generate material colors
            material_colors = self._generate_colors(concentrations_list)
            
            # Parse control names
            try:
                control_list = ast.literal_eval(controls) if controls else []
            except Exception as e:
                logger.warning(f"Failed to parse control names, using empty list: {e}")
                control_list = []
            
            # Create visualization state
            state = VisualizationState(
                file_path=csv_path,
                figure_name_template=template,
                num_rows=int(rows),
                num_cols=int(cols),
                control_names=control_list
            )
            
            logger.info("Visualization state prepared successfully")
            return state
            
        except FileNotFoundError as e:
            logger.error(f"CSV file not found: {csv_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to prepare visualization: {e}")
            raise ValueError(f"Invalid CSV or visualization parameters: {e}") from e
    
    def _generate_colors(self, concentrations_list: Dict[str, List[Any]]) -> Dict[str, Any]:
        """
        Generate color mappings for materials.
        
        Args:
            concentrations_list: Dictionary of materials to concentrations
            
        Returns:
            Dictionary mapping materials to colors
        """
        from matplotlib import pyplot as plt
        
        material_colors = {}
        colormap = plt.get_cmap('tab20')
        num_colors = Visualization.NUM_COLORS_TAB20
        
        for idx, material in enumerate(concentrations_list.keys()):
            color_idx = idx % num_colors
            material_colors[material] = colormap(color_idx)
        
        logger.debug(f"Generated colors for {len(material_colors)} materials")
        return material_colors
    
    def get_export_format_choice(self, num_figures: int) -> str:
        """
        Determine appropriate export format based on number of figures.
        
        Args:
            num_figures: Number of figures to export
            
        Returns:
            'single' for one figure, 'multiple' for many
        """
        return 'single' if num_figures == 1 else 'multiple'
