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
# Last Revision: January 2026
#

import logging
import ast
import numpy as np
from typing import List, Dict, Any, Tuple
from models.csv_data import VisualizationState
from core.io_utils import read_csv_file
from core.layout_utils import find_all_plates_concentrations
from core.layout_utils import transform_concentrations_to_alphas
from models.constants import Visualization, Performance

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
            except (SyntaxError, ValueError) as e:
                logger.warning(f"Invalid control names format: {e}. Using empty list")
                control_list = []
            except Exception as e:
                logger.error(f"Unexpected error parsing controls: {e}")
                raise
            
            try:
                rows_int = int(rows)
                cols_int = int(cols)
                if rows_int <= 0 or cols_int <= 0:
                    raise ValueError("Plate dimensions must be positive integers")
            except ValueError as e:
                logger.error(f"Invalid plate dimensions: {e}")
                raise ValueError(f"Invalid plate dimensions - rows: {rows}, cols: {cols}") from e
            
            # Create visualization state
            state = VisualizationState(
                file_path=csv_path,
                figure_name_template=template,
                num_rows=int(rows),
                num_cols=int(cols),
                control_names=control_list
            )
        
            state.plates = layouts_dict
            state.concentrations = concentrations_list
            state.alpha_mappings = alpha_mappings
            state.material_colors = material_colors
        
            logger.info("Visualization state prepared successfully")
            return state
        
        except FileNotFoundError as e:
            logger.error(f"CSV file not found: {csv_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to prepare visualization: {e}")
            raise ValueError(f"Invalid CSV or visualization parameters: {e}") from e

    def prepare_plate_axes(self, ax, num_rows: int, num_cols: int) -> None:
        """
        Configure axes for plate visualization matching legacy exactly.
    
        Args:
            ax: Matplotlib axes object
            num_rows: Number of rows in plate
            num_cols: Number of columns in plate
        """
        from core.layout_utils import transform_index
    
        # Ensure consistent orientation (wider dimension is horizontal)
        if num_cols > num_rows:
            num_rows, num_cols = num_cols, num_rows
            is_switched = True
        else:
            is_switched = False
    
        ax.grid(True)
        ax.set_xticks(np.arange(0, num_rows + 1, 1), labels=['' for _ in range(num_rows + 1)])
        ax.set_yticks(np.arange(0, num_cols + 1, 1), labels=['' for _ in range(num_cols + 1)])
        ax.set_aspect('equal')
    
        if is_switched:
            ax.set_xticks(np.arange(0.5, num_rows, 1), labels=[str(i + 1) for i in range(num_rows)], minor=True)
            ax.set_yticks(np.arange(0.5, num_cols, 1), labels=[transform_index(i) for i in range(num_cols)], minor=True)
        else:
            ax.set_xticks(np.arange(0.5, num_rows, 1), labels=[transform_index(i) for i in range(num_rows)], minor=True)
            ax.set_yticks(np.arange(0.5, num_cols, 1), labels=[str(i + 1) for i in range(num_cols)], minor=True)
    
        ax.tick_params(axis='both', which='minor', length=0)  # Hide minor tick marks
        ax.set_xlim(0, num_rows)
        ax.set_ylim(0, num_cols)
        ax.invert_yaxis()
    
        logger.debug(f"Prepared axes for {num_rows}x{num_cols} plate")


    def plot_plate_wells(self, ax, plate_data: List, viz_state: VisualizationState) -> None:
        """
        Plot all wells on a plate matching legacy code exactly.
    
        Args:
            ax: Matplotlib axes object
            plate_data: List of CSV rows [well_coord, material, concentration]
            viz_state: Visualization state with color/alpha mappings
        """
        from models.constants import Visualization
        from core.layout_utils import transform_coordinate, to_number_if_possible
    
        # Determine if orientation is switched
        num_rows = viz_state.num_rows
        num_cols = viz_state.num_cols
        if num_cols > num_rows:
            is_switched = True
        else:
            is_switched = False
    
        # Group wells by material
        materials: Dict[str, List[List[str]]] = {}
        for line in plate_data:
            if len(line) < 3:
                continue
            material = line[1]
            if material in materials:
                materials[material].append([line[0]] + line[1:])
            else:
                materials[material] = [[line[0]] + line[1:]]
    
        # Plot each material
        for material in materials:
            # Use circles for controls, squares for other materials
            if material in viz_state.control_names:
                marker = 'o'
            else:
                marker = 's'
        
            # Use precomputed alpha values
            alpha_values = viz_state.alpha_mappings.get(material, {})
        
            x_coords: List[float] = []
            y_coords: List[float] = []
            alphas: List[float] = []
        
            for well in materials[material]:
                if is_switched:
                    [y_coord, x_coord] = transform_coordinate(well[0])
                else:
                    [x_coord, y_coord] = transform_coordinate(well[0])
            
                x_coords.append(x_coord + Visualization.WELL_COORDINATE_OFFSET)
                y_coords.append(y_coord + Visualization.WELL_COORDINATE_OFFSET)
            
                try:
                    alphas.append(alpha_values[to_number_if_possible(well[2])])
                except (KeyError, IndexError):
                    alphas.append(alpha_values.get(well[2], 0.5))
        
            # Get color as array matching legacy
            color = viz_state.material_colors.get(material, np.array([0.5, 0.5, 0.5]))
            colors = [color for _ in range(len(x_coords))]
        
            ax.scatter(x_coords, y_coords, marker=marker, c=colors, 
                      s=Visualization.SCATTER_MARKER_SIZE,
                      edgecolor='black', alpha=alphas)
    
        logger.debug(f"Plotted {len(plate_data)} wells grouped into {len(materials)} materials")


    def create_material_scale(self, ax, material_name: str, viz_state: VisualizationState) -> None:
        """
        Create concentration scale legend for a material matching legacy code exactly.
    
        Args:
            ax: Matplotlib axes object
            material_name: Name of the material
            viz_state: Visualization state with concentration data
        """    
        # Get data for this material
        alpha_mapping = viz_state.alpha_mappings.get(material_name, {})
        color = viz_state.material_colors.get(material_name, np.array([0.5, 0.5, 0.5]))
    
        if not alpha_mapping:
            return
    
        # Use precomputed alpha values
        alphas = [alpha_mapping[x] for x in alpha_mapping]
    
        rgba_colors = np.zeros((1, len(alpha_mapping), 4))
        rgba_colors[:, :, 0] = color[0]
        rgba_colors[:, :, 1] = color[1]
        rgba_colors[:, :, 2] = color[2]
        rgba_colors[:, :, 3] = alphas  # Set alpha channel
    
        ax.imshow(rgba_colors, extent=[0, len(alpha_mapping), 0, 1], aspect='auto')
        ax.set_title(material_name)
    
        x_ticks = np.linspace(0, len(alpha_mapping), len(alpha_mapping))
        x_labels = [str(i) for i in alpha_mapping]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels)
        ax.set_yticks([])  # Hide y-axis ticks
    
        logger.debug(f"Created scale for {material_name} with {len(alpha_mapping)} concentrations")
    
    
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
        num_colors = Performance.COLORMAP_COLOR_LIMIT
        
        for idx, material in enumerate(concentrations_list.keys()):
            color_idx = idx % num_colors
            material_colors[material] = colormap(color_idx)
        
        logger.debug(f"Generated colors for {len(material_colors)} materials")
        return material_colors