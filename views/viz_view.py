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
# Description:  Visualization window view for MPLACE application.
# Pure view layer - handles only UI display and matplotlib visualization.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.3
# Last Revision: March 2026
#

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot
import logging
from typing import List, Tuple, Optional, Dict

from controllers.viz_controller import VisualizationController
from controllers.csv_controller import CsvController
from models.csv_data import VisualizationState
from models.constants import (
    Visualization, UI, WindowConfig, Messages, FileTypes, FigureProperties
)
from core.io_utils import save_figure_to_path, save_figures_to_pdf, path_truncate
from ui.layout_format_dialog import ask_layout_export_format

logger = logging.getLogger(__name__)


class VizView:
    """
    Visualization window UI - pure view layer.
    
    This class handles matplotlib visualization display and user interactions.
    All data preparation and business logic is delegated to VisualizationController.
    
    Attributes:
        parent: Parent Tkinter window
        viz_controller: Visualization controller instance
        csv_controller: CSV controller instance
    """
    
    def __init__(
        self,
        parent: tk.Toplevel,
        viz_controller: VisualizationController,
        csv_controller: CsvController
    ):
        """
        Initialize visualization view.
        
        Args:
            parent: Parent window
            viz_controller: Visualization controller instance
            csv_controller: CSV controller instance
        """
        self.parent = parent
        self.viz_controller = viz_controller
        self.csv_controller = csv_controller
        
        # Will be set when window is created
        self.window: Optional[tk.Toplevel] = None
        self.figures_to_save: List[Tuple[Figure, str]] = []
        self.material_scales: List[Figure] = []
        
        logger.info("VizView initialized")
    
    def show(
        self, 
        file_path: str, 
        figure_name_template: str,
        rows: str, 
        cols: str, 
        control_names: str
    ) -> None:
        """
        Show visualization window with data from file.
        
        Args:
            file_path: Path to CSV data file
            figure_name_template: Template for saved figure names
            rows: Number of rows as string
            cols: Number of columns as string
            control_names: JSON string of control names
        """
        logger.info(f"Opening visualization window for: {file_path}")
        
        # Create window
        self.window = tk.Toplevel(self.parent)
        self.window.grab_set()
        
        self.window.title(WindowConfig.TITLE_VISUALIZER)
        self.window.resizable(False, False)
        self.window.protocol('WM_DELETE_WINDOW', self._cleanup_and_close)
        
        # Reset storage
        self.figures_to_save = []
        self.material_scales = []
        
        # Create save button
        self.save_button = ttk.Button(
            self.window, 
            text=Messages.BUTTON_SAVE_LAYOUT, 
            state=tk.NORMAL,
            command=self._on_save_figures
        )
        self.save_button.grid(row=0, column=0, columnspan=2)
        
        try:
            # Prepare visualization data via controller
            viz_state = self.viz_controller.prepare_visualization(
                csv_path=file_path,
                template=figure_name_template,
                rows=rows,
                cols=cols,
                controls=control_names
            )
            
            # Draw visualizations
            self._draw_all_plates(viz_state, figure_name_template)
            
            # Check if any figures were created
            if not self.figures_to_save:
                logger.info(f"No layouts in file: {file_path}")
                messagebox.showinfo(
                    "No layouts", 
                    f"File {path_truncate(file_path)} contains no layouts to display. Closing the visualization window"
                )
                self._cleanup_and_close()
                return
            
            # Update button text if multiple figures
            if len(self.figures_to_save) > 1:
                self.save_button.configure(text=Messages.BUTTON_SAVE_LAYOUTS)
            
            # Set window position and start
            x = self.parent.winfo_rootx() + WindowConfig.DZN_WINDOW_X
            y = self.parent.winfo_rooty() + WindowConfig.DZN_WINDOW_Y
            
            self.window.geometry(f'+{x}+{y}')
            logger.debug("Entering visualization window mainloop")
            
            self.parent.wait_window(self.window)
            
        except Exception as e:
            logger.error(f"Visualization error: {e}")
            messagebox.showerror("Error", f"Visualization failed:\n{str(e)}")
            self._cleanup_and_close()
    
    def _draw_all_plates(
        self, 
        viz_state: VisualizationState,
        figure_name_template: str
    ) -> None:
        """
        Draw all plate visualizations and material scales.
        
        Args:
            viz_state: Prepared visualization state from controller
            figure_name_template: Template for figure names
        """
        # Create plate tabs notebook
        tab_control = ttk.Notebook(self.window)
        
        # Draw each plate
        for plate_id, plate_data in viz_state.plates.items():
            self._draw_single_plate(
                tab_control,
                figure_name_template,
                plate_id,
                plate_data,
                viz_state
            )
        
        tab_control.grid(row=1, column=0, padx=UI.FRAME_PADDING, pady=UI.SMALL_PADDING)
        
        # Create material scales panel
        self._create_material_scales_panel(viz_state)
    
    def _draw_single_plate(
        self,
        parent: ttk.Notebook,
        figure_name_template: str,
        plate_id: str,
        plate_data: List,
        viz_state: VisualizationState
    ) -> None:
        """
        Draw a single plate visualization.
        
        Args:
            parent: Parent notebook widget
            figure_name_template: Template for figure name
            plate_id: Plate identifier
            plate_data: Plate layout data
            viz_state: Visualization state
        """
        fig = Figure(dpi=FigureProperties.DPI_DISPLAY)
        
        try:
            ax = fig.add_subplot(111)
            
            # Use controller to prepare plot
            self.viz_controller.prepare_plate_axes(
                ax, 
                viz_state.num_rows, 
                viz_state.num_cols
            )
            
            # Plot wells using controller
            self.viz_controller.plot_plate_wells(
                ax,
                plate_data,
                viz_state
            )
            
            # Store figure for saving
            png_path = f"{figure_name_template}{plate_id}.png"
            self.figures_to_save.append((fig, png_path))
            
            # Create tab with canvas
            tab = ttk.Frame(parent)
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas.draw()
            
            # CONSTRAIN the canvas widget size
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.config(width=Visualization.PLATE_CANVAS_WIDTH, height=Visualization.PLATE_CANVAS_HEIGHT)

            canvas_widget.pack(fill=tk.BOTH, expand=True)
            parent.add(tab, text=plate_id)
            
            # Store canvas reference for cleanup
            tab.canvas_ref = canvas
            logger.debug(f"Plate visualization created: {plate_id}")
            
        except Exception as e:
            logger.error(f"Failed to draw plate {plate_id}: {e}")
            pyplot.close(fig)
            raise
    
    def _create_material_scales_panel(self, viz_state: VisualizationState) -> None:
        """
        Create scrollable material concentration scales panel.
        
        Args:
            viz_state: Visualization state with material data
        """
        # Create frame with scrollbar
        panel = ttk.Frame(self.window, width=Visualization.MATERIAL_PANEL_WIDTH)
        canvas = tk.Canvas(
            panel, 
            width=Visualization.MATERIAL_PANEL_WIDTH, 
            height=Visualization.MATERIAL_PANEL_HEIGHT
        )
        canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Draw each material scale
        for material in viz_state.material_colors:
            self._draw_material_scale(
                scrollable_frame,
                material,
                viz_state
            )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        panel.grid(row=1, column=1, padx=UI.FRAME_PADDING, pady=UI.SMALL_PADDING)
    
    def _draw_material_scale(
        self,
        parent: tk.Widget,
        material_name: str,
        viz_state: VisualizationState
    ) -> None:
        """
        Draw concentration scale for a material.
        
        Args:
            parent: Parent widget
            material_name: Name of material
            viz_state: Visualization state
        """
        fig = Figure(
            figsize=(Visualization.SCALE_FIGURE_WIDTH, Visualization.SCALE_FIGURE_HEIGHT),
            dpi=FigureProperties.DPI_DISPLAY
        )
        
        try:
            ax = fig.add_subplot(111)
            
            # Use controller to create scale visualization
            self.viz_controller.create_material_scale(
                ax,
                material_name,
                viz_state
            )
            
            # Store for PDF export
            self.material_scales.append(fig)
            
            # Create canvas
            tab = ttk.Frame(parent)
            canvas = FigureCanvasTkAgg(fig, master=tab)
            
            current_size = fig.get_size_inches()
            fig.set_size_inches(current_size * (100 / FigureProperties.DPI))  # Scale down
            
            canvas.draw()
            
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.config(width=Visualization.SCALE_CANVAS_WIDTH, height=Visualization.SCALE_CANVAS_HEIGHT)
            
            canvas_widget.pack(fill='both', expand=True)
            tab.pack(fill="both", expand=True, padx=UI.WIDGET_SPACING, pady=UI.WIDGET_SPACING_LARGE)
            
            # Store canvas reference
            tab.canvas_ref = canvas
            logger.debug(f"Material scale created: {material_name}")
            
        except Exception as e:
            logger.error(f"Failed to create material scale for {material_name}: {e}")
            pyplot.close(fig)
            raise
    
    def _on_save_figures(self) -> None:
        """Handle save button click."""
        if not self.figures_to_save:
            messagebox.showinfo("No Figures", "No figures available to save.")
            logger.warning("Save attempted but no figures available")
            return
        
        # Single figure - ask for format
        if len(self.figures_to_save) == 1:
            self._save_single_figure()
        # Multiple figures - ask PNG or PDF
        else:
            self._save_multiple_figures()
    
    
    def _save_single_figure(self) -> None:
        """Save single figure with format choice."""
        figure, filename_template = self.figures_to_save[0]

        base = os.path.splitext(os.path.basename(filename_template))[0]
        path = filedialog.asksaveasfilename(
            defaultextension='.png',
            filetypes=FileTypes.FIG_FILES,
            initialfile=base + '.png'
        )
        if not path:
            logger.info("User cancelled figure save")
            return

        try:
            save_figure_to_path(figure, path, self.material_scales)
        except (IOError, OSError):
            logger.error("Failed to write figure file")
            messagebox.showerror(Messages.WRITE_ERROR_TITLE, Messages.WRITE_ERROR_TEXT)
            return

        messagebox.showinfo("Saving Complete", f"Successfully saved layout file: {os.path.basename(path)}")
        logger.info(f"Successfully saved layout file: {path}")
    
    def _save_multiple_figures(self) -> None:
        """Save multiple figures as PNG or PDF."""
        # Ask format
        file_format = ask_layout_export_format(
            self.window, 
            file_formats=[
                (FileTypes.PDF, FileTypes.PDF_LABEL),
                (FileTypes.PNG, FileTypes.PNG_LABEL)
            ]
        )
        
        if not file_format:
            logger.info("User cancelled format selection")
            return
        
        if file_format == FileTypes.PNG:
            self._save_as_multiple_png()
        elif file_format == FileTypes.PDF:
            self._save_as_single_pdf()
        
    def _save_as_multiple_png(self) -> None:
        """Save each figure as a separate PNG."""
        saved_paths = []
        n = len(self.figures_to_save)

        for i, (figure, filename_template) in enumerate(self.figures_to_save):
            base = os.path.splitext(os.path.basename(filename_template))[0]
            path = filedialog.asksaveasfilename(
                title=f"Save plate {i + 1} of {n}",
                defaultextension='.png',
                filetypes=FileTypes.PNG_FILES,
                initialfile=base + '.png'
            )
            if not path:
                messagebox.showwarning("Warning", f"User cancelled saving on plate {i+1} out of {n}")
                logger.info(f"User cancelled saving on plate {i+1}/{n}")
                return

            try:
                save_figure_to_path(figure, path)
            except (IOError, OSError):
                logger.error("Failed to write figure file")
                messagebox.showerror(Messages.WRITE_ERROR_TITLE, Messages.WRITE_ERROR_TEXT)
                return

            saved_paths.append(os.path.basename(path))

        file_list = '\n'.join(f"• {p}" for p in saved_paths)
        messagebox.showinfo(
            "Saving Complete",
            f"Successfully saved {n} layout files:\n\n{file_list}\n\n"
        )
        logger.info(f"Multi-file layout export completed: {n} files")
    
    
    def _save_as_single_pdf(self) -> None:
        """Save all figures in a single PDF."""
        _, template = self.figures_to_save[0]
        base = os.path.splitext(os.path.basename(template))[0]

        path = filedialog.asksaveasfilename(
            defaultextension='.pdf',
            filetypes=FileTypes.PDF_FILES,
            initialfile=base + '.pdf'
        )
        if not path:
            logger.info("User cancelled PDF save")
            return

        try:
            save_figures_to_pdf(self.figures_to_save, path, self.material_scales)
        except (IOError, OSError):
            logger.error("Failed to write PDF file")
            messagebox.showerror(Messages.WRITE_ERROR_TITLE, Messages.WRITE_ERROR_TEXT)
            return

        messagebox.showinfo("Saving Complete", f"Successfully saved layout file: {os.path.basename(path)}")
        logger.info(f"Successfully saved PDF: {path}")
    
    
    def _cleanup_and_close(self) -> None:
        """Cleanup matplotlib resources and close window."""
        try:
            self._cleanup_canvas_widgets(self.window)
            pyplot.close('all')
            logger.debug("Matplotlib cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
        finally:
            if self.window:
                logger.info("Visualization window closed")
                self.window.destroy()
                self.window = None
                self.parent.focus_force()
    
    def _cleanup_canvas_widgets(self, widget: tk.Misc) -> None:
        """
        Recursively cleanup matplotlib canvases.
        
        Args:
            widget: Root widget to start cleanup from
        """
        if hasattr(widget, 'canvas_ref'):
            try:
                canvas = widget.canvas_ref
                fig = canvas.figure
                canvas.get_tk_widget().destroy()
                pyplot.close(fig)
                del widget.canvas_ref
                logger.debug("Canvas cleaned up")
            except (AttributeError, tk.TclError):
                pass
        
        # Check children
        try:
            for child in widget.winfo_children():
                self._cleanup_canvas_widgets(child)
        except (AttributeError, tk.TclError):
            pass
