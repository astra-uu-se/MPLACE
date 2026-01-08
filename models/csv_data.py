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
# Description: Data models for CSV layouts and visualization.
# Represents parsed CSV data and visualization state.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.2
# Last Revision: January 2026
#

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
import matplotlib.figure as mpl_figure


@dataclass
class LayoutData:
    """
    Parsed CSV layout data.
    
    This represents the structured data extracted from a CSV file
    containing plate layouts.
    
    Attributes:
        layouts_dict: Dictionary mapping layout names to plate grids
        concentrations_list: Dictionary mapping materials to their concentrations
        material_colors: Dictionary mapping materials to matplotlib colors
        alpha_mappings: Dictionary mapping materials to alpha (transparency) values
    """
    
    layouts_dict: Dict[str, List[List[str]]]
    concentrations_list: Dict[str, List[Any]]
    material_colors: Dict[str, Any]
    alpha_mappings: Dict[str, Dict[Any, float]]


@dataclass
class VisualizationState:
    """
    State for visualization window.
    
    This holds all the data needed to render and export plate visualizations.
    
    Attributes:
        figures_to_save: List of (figure, filename_template) tuples for export
        material_scales: List of material scale figures (legends)
        file_path: Path to the source CSV file
        figure_name_template: Template for naming exported figures
        num_rows: Number of rows in the plate
        num_cols: Number of columns in the plate
        control_names: List of control material names
        plates: Dictionary of plate layouts
        concentrations: Dictionary of material concentrations
        alpha_mappings: Alpha transparency mappings
        material_colors: Color mappings for materials
    """
    figures_to_save: List[Tuple[mpl_figure.Figure, str]] = field(default_factory=list)
    material_scales: List[mpl_figure.Figure] = field(default_factory=list)
    file_path: str = ''
    figure_name_template: str = ''
    num_rows: int = 16
    num_cols: int = 24
    control_names: List[str] = field(default_factory=list)
    plates: Dict[str, List] = field(default_factory=dict)
    concentrations: Dict[str, List[Any]] = field(default_factory=dict)
    alpha_mappings: Dict[str, Dict[Any, float]] = field(default_factory=dict)
    material_colors: Dict[str, Any] = field(default_factory=dict)
    
    # ... rest of methods unchanged

    
    def has_figures(self) -> bool:
        """Check if there are figures ready to save."""
        return len(self.figures_to_save) > 0
    
    def is_single_figure(self) -> bool:
        """Check if there is only one figure to save."""
        return len(self.figures_to_save) == 1
    
    def is_multiple_figures(self) -> bool:
        """Check if there are multiple figures to save."""
        return len(self.figures_to_save) > 1
    
    def clear_figures(self) -> None:
        """Clear all stored figures and scales."""
        self.figures_to_save.clear()
        self.material_scales.clear()
