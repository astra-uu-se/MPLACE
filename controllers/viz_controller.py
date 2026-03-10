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
# Description: Controller for visualization operations.
# Orchestrates data preparation and figure generation for plate layouts.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.0
# Last Revision: January 2026
#

import logging
import ast
import math
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from typing import List, Dict, Any, Union

from models.csv_data import VisualizationState
from core.io_utils import read_csv_file
from core.layout_utils import find_all_plates_concentrations
from core.layout_utils import transform_concentrations_to_alphas
from models.constants import Visualization, Performance, FigureProperties

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
        
        self._COLORMAPS = [
            mpl.colormaps['tab20'],
            mpl.colormaps['tab20b'],
            mpl.colormaps['tab20c'],
        ]
        
        # Assert bounds
        assert Visualization.CONCENTRATION_SIZE_MIN < Visualization.CONCENTRATION_SIZE_MAX
        assert FigureProperties.DPI > 0
    
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
                num_rows=rows_int,
                num_cols=cols_int,
                control_names=control_list,
                plates = layouts_dict,
                concentrations = concentrations_list,
                alpha_mappings = alpha_mappings,
                material_colors = material_colors
            )
        
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
            ax.set_xticks(np.arange(0.5, num_rows, 1), labels=[str(i + 1) for i in range(num_rows)], minor=True, fontsize = 8/FigureProperties.DPI_RATIO)
            ax.set_yticks(np.arange(0.5, num_cols, 1), labels=[transform_index(i) for i in range(num_cols)], minor=True, fontsize = 8/FigureProperties.DPI_RATIO)
        else:
            ax.set_xticks(np.arange(0.5, num_rows, 1), labels=[transform_index(i) for i in range(num_rows)], minor=True, fontsize = 8/FigureProperties.DPI_RATIO)
            ax.set_yticks(np.arange(0.5, num_cols, 1), labels=[str(i + 1) for i in range(num_cols)], minor=True, fontsize = 8/FigureProperties.DPI_RATIO)
    
        ax.tick_params(axis='both', which='minor', length=0)  # Hide minor tick marks
        ax.set_xlim(0, num_rows)
        ax.set_ylim(0, num_cols)
        ax.invert_yaxis()
    
        logger.debug(f"Prepared axes for {num_rows}x{num_cols} plate")


    def plot_plate_wells(self, ax, plate_data: List, viz_state: VisualizationState) -> None:
        """Plot all wells on a plate with concentration encoded as marker size.
        
        Each well is displayed with:
        - Color: Material identity (60 distinct colors available)
        - Size: Concentration level (small to large)
        - Marker shape: Controls (circles) vs materials (squares)
        
        Args:
            ax: Matplotlib axes object
            plate_data: List of CSV rows [well_coord, material, concentration]
            viz_state: Visualization state with color and concentration mappings
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
                materials[material].append(line[:])
            else:
                materials[material] = [line[:]]
    
        # Plot each material
        for material in materials:
            # Use circles for controls, squares for other materials
            marker = self._select_marker(material, viz_state)
        
            # Get concentration mapping for this material
            alpha_mapping = viz_state.alpha_mappings.get(material, {})
        
            x_coords: List[float] = []
            y_coords: List[float] = []
            sizes: List[float] = []
        
            for well in materials[material]:
                if is_switched:
                    [y_coord, x_coord] = transform_coordinate(well[0])
                else:
                    [x_coord, y_coord] = transform_coordinate(well[0])
            
                x_coords.append(x_coord + Visualization.WELL_COORDINATE_OFFSET)
                y_coords.append(y_coord + Visualization.WELL_COORDINATE_OFFSET)
            
                # Map concentration to size
                concentration = well[2]
                size = self._concentration_to_size(
                    to_number_if_possible(concentration),
                    alpha_mapping,
                    num_rows,
                    num_cols
                )
                sizes.append(size / FigureProperties.DPI_RATIO)
        
            # Get color for this material
            color = viz_state.material_colors.get(material, np.array([0.5, 0.5, 0.5]))
        
            # Plot wells with size encoding (no alpha variation)
            ax.scatter(
                x_coords,
                y_coords,
                marker=marker,
                linewidths=0.5/FigureProperties.DPI_RATIO,
                c=[color],
                s=sizes,
                edgecolor='black',
                alpha=1.0
            )
    
        logger.debug(f"Plotted {len(plate_data)} wells grouped into {len(materials)} materials "
                    f"with size encoding for concentration")


    def create_material_scale(
        self,
        ax,
        material_name: str,
        viz_state: VisualizationState
    ) -> None:
        """Create concentration scale legend showing size encoding.
        
        Creates a visual representation of how concentration maps to marker size
        for a specific material.
    
        Args:
            ax: Matplotlib axes object for the legend
            material_name: Name of the material to show scale for
            viz_state: Visualization state with concentration data
        """
        # Get data for this material
        alpha_mapping = viz_state.alpha_mappings.get(material_name, {})
        color = viz_state.material_colors.get(material_name, np.array([0.5, 0.5, 0.5]))
        
        num_rows = viz_state.num_rows
        num_cols = viz_state.num_cols
    
        if not alpha_mapping:
            logger.warning(f"No concentration data for material {material_name}")
            return
    
        # Get sorted concentrations
        concentrations = sorted(alpha_mapping.keys())
        num_conc = len(concentrations)
        
        # Calculate relative sizes based on concentration ratios
        # All sizes are relative to max, then scaled by SIZE_MAX for consistency
        sizes = [self._concentration_to_size(
                    concentration,
                    alpha_mapping,
                    num_rows,
                    num_cols
                ) for concentration in concentrations]
        # Create scatter plot showing size gradient with consistent proportions
        if num_conc == 1:
            x_positions = np.arange(1) + 0.5
        else:
            x_positions = np.arange(start = 0.1, stop = 0.90001, step = 0.8 / (num_conc - 1))
        y_positions = np.ones(num_conc) * 0.5
        
        marker = self._select_marker(material_name, viz_state)
        
        ax.scatter(
            x_positions,
            y_positions,
            marker=marker,
            linewidths=0.5 / FigureProperties.DPI_RATIO,
            s=sizes,
            c=[color],
            edgecolor='black',
            alpha=1.0
        )
        ax.set_aspect('equal')
        
        # Set title and labels
        ax.set_title(material_name, fontsize=9/FigureProperties.DPI_RATIO, fontweight='bold', pad=2/FigureProperties.DPI_RATIO)
        ax.set_xticks(x_positions)
        ax.set_xticklabels([str(c) for c in concentrations], fontsize=6/FigureProperties.DPI_RATIO)
        ax.set_xlabel('Concentrations', fontsize=8/FigureProperties.DPI_RATIO)
        ax.set_yticks([])
        
        ax.set_ylim(0.45, 0.55)
        ax.set_xlim(0, 1)
        ax.grid(axis='x', alpha=0.3)
        
        logger.debug(f"Created size-encoding scale for {material_name} with {num_conc} concentrations")

    
    def _concentration_to_size(
        self,
        concentration: Union[int,float],
        alpha_mapping: Dict[Any, float],
        plate_num_rows: int,
        plate_num_cols: int
    ) -> float:
        """Convert concentration value to marker size.
        
        Maps concentration values to marker sizes in range [SIZE_MIN, SIZE_MAX].
        Uses the precomputed alpha mapping to determine the concentration range.
        
        Args:
            concentration: Concentration value (numeric or string)
            alpha_mapping: Dictionary mapping concentrations to alpha values
            plate_num_rows: Number of rows in plate (for context)
            plate_num_cols: Number of columns in plate (for context)
        
        Returns:
            Marker size for scatter plot (typically 50-400)
        """
        from core.layout_utils import to_number_if_possible
        
        # if the plate differs from 16x24 then we need to readjust the size ranges
        # We do not increase more than 1 / 0.7 to keep the marker size reasonable
        if plate_num_cols > plate_num_rows:
            plate_num_rows, plate_num_cols = plate_num_cols, plate_num_rows
        ratio = max(0.7, plate_num_rows / 24, plate_num_cols / 16)
        
        # Get size range from constants
        size_min = math.floor(Visualization.CONCENTRATION_SIZE_MIN / ratio)
        size_max = math.floor(Visualization.CONCENTRATION_SIZE_MAX / ratio)
        
        # Handle empty mapping
        if not alpha_mapping:
            return (size_min + size_max) / 2
        
        try:
            # Find max concentration in mapping
            max_conc = max(float(k) if isinstance(k, str) else k for k in alpha_mapping.keys())
            
            # Handle zero max concentration
            if max_conc <= 0:
                return (size_min + size_max) / 2
            
            # Normalize concentration to [0, 1]
            normalized = float(concentration) / float(max_conc)
            
            # Clamp to valid range
            normalized = max(0.0, min(1.0, normalized))
            
        except (ValueError, TypeError, KeyError):
            # If conversion fails, use middle size
            logger.debug(f"Could not map concentration {concentration} to size, using default")
            return (size_min + size_max) / 2
        
        # Scale to size range
        size = size_min + (normalized * (size_max - size_min))
        
        return size
    
    def _select_marker(self, 
                       material_name: str,
                       viz_state: VisualizationState
                       ) -> str:
        """Marker selection based on the material.
           Use circles for controls, squares for other materials
        """
        if material_name in viz_state.control_names:
            return 'o'
        else:
            return 's'
    
    def _generate_colors(self, concentrations_list: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Generate color mappings for each material.
        
        Uses matplotlib's tab20 colormaps, cycling through available colors
        to ensure consistent material representation across all plates.
        
        Args:
            concentrations_list: Dictionary mapping material names to concentration lists.
        
        Returns:
            Dictionary mapping material names to RGBA color values for visualization.
        """
        material_colors = {}
        
        # Get the three tab20 variant colormaps
        colormaps = self._COLORMAPS
        num_colors = Performance.COLORMAP_COLOR_LIMIT
        
        for idx, material in enumerate(concentrations_list.keys()):
            map_idx = (idx // num_colors) % len(colormaps)
            colormap = colormaps[map_idx]
            color_idx = idx % num_colors 
            material_colors[material] = colormap(color_idx)
        
        logger.debug(f"Generated colors for {len(concentrations_list)} materials using "
                    f"{min(3, (len(concentrations_list) + num_colors - 1) // num_colors)} extended tab20 colormaps")
        return material_colors
    