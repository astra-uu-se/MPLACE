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
# Description:  GUI for displaying microplate layouts
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.1
# Last Revision: November 2025
#


import matplotlib as mpl
from matplotlib import pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import numpy as np
import logging

import tkinter as tk
from tkinter import ttk, VERTICAL, RIGHT, Y, LEFT, BOTH

import ast
from typing import List, Dict, Union, Tuple

from core.layout_utils import transform_coordinate, transform_index, transform_concentrations_to_alphas, to_number_if_possible, find_all_plates_concentrations
from core.io_utils import read_csv_file, write_figure, write_figures_in_pdf, path_truncate
from models.constants import Visualization, Performance, PlateDefaults, UI, WindowConfig, Messages, FileTypes
from ui.layout_format_dialog import ask_layout_export_format


# Cache colormap at module level for performance optimization
COLORMAP_TAB20 = pyplot.get_cmap('tab20')

# Configure logging for visualization module
logger = logging.getLogger(__name__)


def draw_plates(parent: tk.Widget, figure_name_template: str, text_array: List[str], 
                num_rows: int = PlateDefaults.ROWS_INT, num_cols: int = PlateDefaults.COLS_INT,
                control_names: List[str] = [], figures_to_save: List[Tuple[Figure, str]] = [], material_scales: List[Figure] = []) -> None:
    """Load CSV data, analyze it, split into layouts, and draw plates with material scales.
    
    Args:
        parent: Parent tkinter widget
        figure_name_template: Template for saved figure names
        text_array: List of CSV lines to process
        num_rows: Number of rows in microplate
        num_cols: Number of columns in microplate  
        control_names: List of control material names
        figures_to_save: List to store (figure, suggested_name) tuples for later saving
    """
    layouts_dict, concentrations_list = find_all_plates_concentrations(text_array)
            
    # Sort concentrations for each material
    for material in concentrations_list:
        try:
            concentrations_list[material] = sorted(concentrations_list[material])
        except TypeError:
            # Handle mixed types by converting to strings and sorting
            concentrations_list[material] = [str(x) for x in concentrations_list[material]]
            concentrations_list[material] = sorted(concentrations_list[material])
            logger.warning(f"Mixed-type concentrations for {material}, converted to strings")

    # Log data processing summary
    total_wells = sum(len(layouts_dict[layout]) for layout in layouts_dict)
    print(f"Processing {len(concentrations_list)} materials, {total_wells} wells across {len(layouts_dict)} layouts")
    logger.info(f"Visualization data: {len(concentrations_list)} materials, {total_wells} wells, {len(layouts_dict)} layouts")

    # Precompute alpha mappings once for all materials for performance optimization
    alpha_mappings: Dict[str, Dict[Union[str, float, int], float]] = {}
    for material in concentrations_list:
        alpha_mappings[material] = transform_concentrations_to_alphas(concentrations_list[material])
    logger.debug(f"Precomputed alpha mappings for {len(alpha_mappings)} materials")

    # Generate colors for materials using cached tab20 colormap
    color_index = 0
    material_colors: Dict[str, np.ndarray] = {}
    for material in sorted(concentrations_list.keys()):
        material_colors[material] = np.array(COLORMAP_TAB20(color_index)[:3])
        color_index += 1
        if color_index >= Performance.COLORMAP_COLOR_LIMIT:
            color_index = 0

    # Create main plate visualization tabs
    tab_control = ttk.Notebook(parent)
    for layout in layouts_dict:
        draw_plate(tab_control, figure_name_template, layout,
                   layouts_dict[layout], material_colors, alpha_mappings, 
                   num_rows, num_cols, control_names, figures_to_save)
    tab_control.grid(row=1, column=0, padx=UI.FRAME_PADDING, pady=UI.SMALL_PADDING)

    # Create scrollable material scale panel
    tab_control2 = ttk.Frame(parent, width=Visualization.MATERIAL_PANEL_WIDTH)
    canvas_right = tk.Canvas(tab_control2, width=Visualization.MATERIAL_PANEL_WIDTH, height=Visualization.MATERIAL_PANEL_HEIGHT)
    canvas_right.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(tab_control2, orient="vertical",
                              command=canvas_right.yview)
    scrollbar.pack(side="right", fill="y")

    canvas_right.configure(yscrollcommand=scrollbar.set)
    scrollable_frame = ttk.Frame(canvas_right)

    scrollable_frame.bind(
        "<Configure>", lambda event: update_scroll_region(event, canvas_right))

    # Draw material concentration scales using precomputed alpha mappings
    for material in material_colors:
        material_color = material_colors[material]
        concentration_material = concentrations_list[material]
        draw_material_scale(scrollable_frame, material,
                            material_color, concentration_material, alpha_mappings[material], material_scales)

    canvas_right.create_window((0, 0), window=scrollable_frame, anchor="nw")
    tab_control2.grid(row=1, column=1, padx=UI.FRAME_PADDING, pady=UI.SMALL_PADDING)


def update_scroll_region(event: tk.Event, canvas: tk.Canvas) -> None:
    """Update canvas scroll region when content changes.
    
    Args:
        event: Tkinter event object
        canvas: Canvas widget to update
    """
    canvas.configure(scrollregion=canvas.bbox("all"))


def draw_plate(parent: ttk.Notebook, figure_name_template: str, layout: str, layout_array: List[List[str]],
               material_colors: Dict[str, np.ndarray], alpha_mappings: Dict[str, Dict[Union[str, float, int], float]],
               num_rows: int = PlateDefaults.ROWS_INT, num_cols: int = PlateDefaults.COLS_INT,
               control_names: List[str] = [], figures_to_save: List[Tuple[Figure, str]] = []) -> None:
    """Draw a single microplate layout visualization.
    
    Args:
        parent: Parent tkinter widget
        figure_name_template: Template for saved figure name
        layout: Layout identifier/name
        layout_array: Array of layout data
        material_colors: Dictionary mapping materials to colors
        alpha_mappings: Precomputed dictionary mapping materials to their concentration alpha values
        num_rows: Number of rows in microplate
        num_cols: Number of columns in microplate
        control_names: List of control material names (shown as circles)
        figures_to_save: List to store (figure, suggested_name) tuples for later saving
    """
    # Create figure
    fig = Figure()
    try:
        ax = fig.add_subplot(111)

        # Ensure consistent orientation (wider dimension is horizontal)
        if num_cols > num_rows:
            num_rows, num_cols = num_cols, num_rows
            is_switched = True
        else:
            is_switched = False

        ax.grid(True)
        ax.set_xticks(np.arange(0, num_rows + 1, 1),labels=['' for _ in range(num_rows + 1)])
        ax.set_yticks(np.arange(0, num_cols + 1, 1),labels=['' for _ in range(num_cols + 1)])
        ax.set_aspect('equal')
        
        if is_switched:
            ax.set_xticks(np.arange(0.5, num_rows, 1),labels=[str(i + 1) for i in range(num_rows)],minor=True)
            ax.set_yticks(np.arange(0.5, num_cols, 1),labels=[transform_index(i) for i in range(num_cols)],minor=True)
        else:
            ax.set_xticks(np.arange(0.5, num_rows, 1),labels=[transform_index(i) for i in range(num_rows)],minor=True)
            ax.set_yticks(np.arange(0.5, num_cols, 1),labels=[str(i + 1) for i in range(num_cols)],minor=True)
        
        ax.tick_params(axis='both', which='minor', length=0)  # Hide minor tick marks
        
        # Group wells by material
        materials: Dict[str, List[List[str]]] = {}
        for line in layout_array:
            if line[1] in materials:
                materials[line[1]].append([line[0]] + line[1:])
            else:
                materials[line[1]] = [[line[0]] + line[1:]]

        # Plot each material using precomputed alpha values
        for material in materials:
            # Use circles for controls, squares for other materials
            if material in control_names:
                marker = 'o'
            else:
                marker = 's'

            # Use precomputed alpha values for performance
            alpha_values = alpha_mappings[material]

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
                    # Handle missing concentration data gracefully
                    alphas.append(alpha_values[well[2]])

            colors = [material_colors[material] for i in range(len(x_coords))]
            ax.scatter(x_coords, y_coords, marker=marker, c=colors, s=Visualization.SCATTER_MARKER_SIZE,
                       edgecolor='black', alpha=alphas)

        ax.set_xlim(0, num_rows)
        ax.set_ylim(0, num_cols)
        
        ax.invert_yaxis()

        # Save figure with user-visible path confirmation
        png_path = figure_name_template + layout + '.png'
        figures_to_save.append((fig,png_path))
        #fig.savefig(png_path)
        #print(f"Saved visualization: {png_path}")
        #logger.info(f"PNG saved: {png_path}")

        # Create tab and canvas
        tab = ttk.Frame(parent)
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        parent.add(tab, text=layout)

        # Store canvas reference for cleanup
        tab.canvas_ref = canvas
        logger.debug(f"Matplotlib canvas created for layout: {layout}")

    except Exception as e:
        logger.error(f"Failed to draw plate {layout}: {e}")
        # Ensure figure resources are freed if plotting fails
        try:
            pyplot.close(fig)
        except Exception:
            pass
        raise


def draw_material_scale(parent: tk.Widget, material_name: str, color: np.ndarray, 
                        concentrations: List[Union[str, float, int]],
                        alpha_mapping: Dict[Union[str, float, int], float],
                        material_scales: List[Figure]) -> None:
    """Draw a concentration scale for a specific material.
    
    Args:
        parent: Parent tkinter widget
        material_name: Name of the material
        color: RGB color array for the material
        concentrations: List of concentration values
        alpha_mapping: Precomputed mapping of concentrations to alpha values
    """
    # Use precomputed alpha values for performance
    alphas = [alpha_mapping[x] for x in alpha_mapping]

    rgba_colors = np.zeros((1, len(concentrations), 4))
    rgba_colors[:, :, 0] = color[0]
    rgba_colors[:, :, 1] = color[1]
    rgba_colors[:, :, 2] = color[2]
    rgba_colors[:, :, 3] = alphas  # Set alpha for the alpha channel

    # Create Figure
    fig = Figure(figsize=(Visualization.SCALE_FIGURE_WIDTH, Visualization.SCALE_FIGURE_HEIGHT))
    try:
        ax = fig.add_subplot(111)

        ax.imshow(rgba_colors, extent=[0, len(concentrations), 0, 1], aspect='auto')
        ax.set_title(material_name)

        x_ticks = np.linspace(0, len(concentrations), len(concentrations))
        x_labels = [str(i) for i in alpha_mapping]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels)
        ax.set_yticks([])  # Hide y-axis ticks as it's a 1D spectrum
        material_scales.append(fig)

        tab2 = ttk.Frame(parent)
        canvas = FigureCanvasTkAgg(fig, master=tab2)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        tab2.pack(fill="both", expand=True, padx=UI.WIDGET_SPACING, pady=UI.WIDGET_SPACING_LARGE)

        # Store canvas reference for cleanup
        tab2.canvas_ref = canvas
        logger.debug(f"Material scale created: {material_name}, {len(concentrations)} concentrations")

    except Exception as e:
        logger.error(f"Failed to create material scale for {material_name}: {e}")
        # Ensure figure resources are freed if scale creation fails
        try:
            pyplot.close(fig)
        except Exception:
            pass
        raise


def visualize(file_path: str, figure_name_template: str, rows: str, cols: str, 
              control_names: List[str] = PlateDefaults.CONTROL_NAMES) -> None:
    """Main visualization window for microplate layouts.
    
    Args:
        file_path: Path to CSV data file
        figure_name_template: Template for saved figure names
        rows: Number of rows as string
        cols: Number of columns as string
        control_names: JSON string of control names (default: '[]')
    """    
    # Storage for figures to be saved on user command
    # (generated by Perplexity AI)
    figures_to_save: List[Tuple[Figure, str]] = []
    material_scales: List[Figure] = []
    def save_all_figures() -> None:
        """Save all plate figures to PNG or PDF files on user command."""
        if not figures_to_save:
            # TODO: redo it as if when there are no figures, then make the button inactive
            tk.messagebox.showinfo("No Figures", "No figures available to save.")
            logger.warning("Save attempted but no figures were prepared")
            return
        elif len(figures_to_save) == 1:
            figure, filename_template = figures_to_save[0]
            path = write_figure(figure, FileTypes.FIG_FILES, filename_template, material_scales)
            if path == -1:
                logger.info("User cancelled figure save")
                return
            elif path == -2:
                logger.error("Failed to write the figure file")
                tk.messagebox.showerror(Messages.WRITE_ERROR_TITLE, Messages.WRITE_ERROR_TEXT)
                return
            tk.messagebox.showinfo("Saving Complete",f"Successfully saved layout file: {path}")
            logger.info(f"Successfully saved layout file: {path}")
            return
        elif len(figures_to_save) > 1:
            file_format = ask_layout_export_format(window, [(FileTypes.PDF, FileTypes.PDF_LABEL),
                                                            (FileTypes.PNG, FileTypes.PNG_LABEL)])
            # format selection dialogue
            # if png -> save 1-by-1
            if file_format == FileTypes.PNG:
                tk.messagebox.showinfo("Information",f"There are {len(figures_to_save)} plates. For each plate there will be a corresponding save file dialogue.")
                saved_paths = []
                for i in range(len(figures_to_save)):
                    figure, filename_template = figures_to_save[i]
                    path = write_figure(figure, FileTypes.PNG_FILES, filename_template)
                    if path == -1:
                        if i == 0:
                            logger.info("User cancelled figures save")
                            return
                        else:
                            logger.info(f"User cancelled saving on plate {i+1}/{len(figures_to_save)}")
                            return
                    elif path == -2:
                        logger.error("Failed to write the figure file")
                        tk.messagebox.showerror(Messages.WRITE_ERROR_TITLE, Messages.WRITE_ERROR_TEXT)
                        return
                    saved_paths.append(path)
                file_list = '\n'.join(f"• {p}" for p in saved_paths)
                tk.messagebox.showinfo("Saving Complete",f"Successfully saved {len(figures_to_save)} layout files:\n\n{file_list}\n\n")
                logger.info(f"Multi-file layout figures export completed: {len(figures_to_save)} files saved")
                return
            elif file_format == FileTypes.PDF:
                path = write_figures_in_pdf(figures_to_save, figure_name_template, material_scales)
                if path == -1:
                    logger.info("User cancelled figure save")
                    return
                elif path == -2:
                    logger.error("Failed to write the figure file")
                    tk.messagebox.showerror(Messages.WRITE_ERROR_TITLE, Messages.WRITE_ERROR_TEXT)
                    return
                tk.messagebox.showinfo("Saving Complete",f"Successfully saved layout file: {path}")
                logger.info(f"Successfully saved layout file: {path}")
                return
    
    def cleanup_and_close() -> None:
        """Properly cleanup all matplotlib resources before closing."""
        try:
            # Find and cleanup all canvas references
            cleanup_canvas_widgets(window)
            pyplot.close('all')  # Close any remaining pyplot figures
            logger.debug("Matplotlib cleanup completed")
        except Exception as e:
            print(f"Warning during cleanup: {e}")
            logger.warning(f"Cleanup warning: {e}")
        finally:
            logger.info("Visualization window closed")
            window.destroy()

    logger.info("Opening visualization window")
    window: tk.Tk = tk.Tk()
    window.title(WindowConfig.TITLE_VISUALIZER)
    window.protocol('WM_DELETE_WINDOW', cleanup_and_close)  # Handle window X button

    # Add save button
    save_button: ttk.Button = ttk.Button(window, text=Messages.BUTTON_SAVE_LAYOUT, state=tk.NORMAL)
    save_button.grid(row=0, column=0, columnspan=2)
    save_button.configure(command=save_all_figures)

    try:
        draw_plates(window, figure_name_template, read_csv_file(file_path),
                    num_rows=int(rows), num_cols=int(cols), 
                    control_names=ast.literal_eval(control_names),
                    figures_to_save=figures_to_save,
                    material_scales = material_scales)
        if not figures_to_save:
            save_button.configure(state=tk.DISABLED)
            logger.info(f"File {file_path} contains no layouts. Visualization window is closed")
            tk.messagebox.showinfo("No layouts", f"File {path_truncate(file_path)} contains no layouts to display. Closing the visualization window")
            cleanup_and_close()
            return
        if len(figures_to_save) > 1:
            save_button.configure(text=Messages.BUTTON_SAVE_LAYOUTS)
        window.geometry(f'+{WindowConfig.VIZ_WINDOW_X}+{WindowConfig.VIZ_WINDOW_Y}')
        logger.debug("Visualization window geometry set, entering mainloop")
        window.mainloop()
    except Exception as e:
        logger.error(f"Visualization error: {e}")
        print(f"Error in visualization: {e}")
        cleanup_and_close()


def cleanup_canvas_widgets(widget: tk.Misc) -> None:
    """Recursively cleanup matplotlib canvases in widget tree.
    
    Args:
        widget: Root widget to start cleanup from
    """
    if hasattr(widget, 'canvas_ref'):
        try:
            canvas = widget.canvas_ref
            fig = canvas.figure
            canvas.get_tk_widget().destroy()
            # Close the figure explicitly to free memory from backend
            pyplot.close(fig)
            del canvas
            logger.debug("Canvas and figure cleaned up")
        except (AttributeError, tk.TclError):
            # Canvas might already be destroyed
            pass

    # Recursively check children
    try:
        for child in widget.winfo_children():
            cleanup_canvas_widgets(child)
    except (AttributeError, tk.TclError):
        # Widget might be destroyed during iteration
        pass
