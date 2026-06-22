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
# Version: 1.3.6
# Last Revision: June 2026
#

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot
import logging
from typing import List, Tuple, Optional, Dict, Callable

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
        csv_controller: CsvController,
        on_window_closed: Optional[Callable[[], None]] = None
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
        self.on_window_closed = on_window_closed
        
        # Will be set when window is created
        self.window: Optional[tk.Toplevel] = None
        self.figures_to_save: List[Tuple[Figure, str]] = []
        self.material_scales: List[Figure] = []
        
        # Virtual scrolling state for material scales panel
        self._scale_slots: Dict[int, Optional[dict]] = {}   # index -> {frame, canvas_ref, fig} | None
        self._materials_list: List[str] = []                # ordered material names
        self._scales_canvas: Optional[tk.Canvas] = None     # the tk.Canvas of the panel
        self._scales_viz_state = None                       # viz_state reference for lazy rendering
        
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
            
        except FileNotFoundError as e:
            logger.error(f"CSV file not found: {e}")
            messagebox.showerror("File Not Found", f"The CSV file could not be found:\n\n{str(e)}")
            self._cleanup_and_close()
        
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
        Create scrollable material concentration scales panel with virtual scrolling.
        Only the materials currently visible in the viewport are rendered as matplotlib
        figures; the rest are placeholder slots. Figures are created on scroll and
        destroyed when they move far enough out of view.
        
        Args:
            viz_state: Visualization state with material data
        """
        materials = list(viz_state.material_colors.keys())
        self._materials_list = materials
        self._scale_slots = {i: None for i in range(len(materials))}
        self._scales_viz_state = viz_state

        item_h = Visualization.MATERIAL_SCALE_ITEM_HEIGHT
        total_height = len(materials) * item_h

        # Outer frame
        panel = ttk.Frame(self.window, width=Visualization.MATERIAL_PANEL_WIDTH)

        canvas = tk.Canvas(
            panel,
            width=Visualization.MATERIAL_PANEL_WIDTH,
            height=Visualization.MATERIAL_PANEL_HEIGHT,
            scrollregion=(0, 0, Visualization.MATERIAL_PANEL_WIDTH, total_height)
        )
        canvas.pack(side="left", fill="both", expand=True)
        self._scales_canvas = canvas

        scrollbar = ttk.Scrollbar(panel, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        def _on_scroll(*args):
            canvas.yview(*args)
            self._update_visible_scales()

        scrollbar.configure(command=_on_scroll)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Mouse wheel - Windows/macOS
        canvas.bind("<MouseWheel>", lambda e: (
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
            self._update_visible_scales()
        ))
        # Mouse wheel - Linux
        canvas.bind("<Button-4>", lambda e: (
            canvas.yview_scroll(-1, "units"),
            self._update_visible_scales()
        ))
        canvas.bind("<Button-5>", lambda e: (
            canvas.yview_scroll(1, "units"),
            self._update_visible_scales()
        ))

        panel.grid(row=1, column=1, padx=UI.FRAME_PADDING, pady=UI.SMALL_PADDING)

        # Initial render — populate whatever is visible at startup
        self.window.update_idletasks()
        self._update_visible_scales()

    def _update_visible_scales(self) -> None:
        """
        Render matplotlib figures for slots currently in the viewport,
        and destroy figures that have scrolled far out of view.
        Called on every scroll event and once at panel creation.
        """
        canvas = self._scales_canvas
        if canvas is None or not self._materials_list:
            return

        top_frac, bot_frac = canvas.yview()
        item_h = Visualization.MATERIAL_SCALE_ITEM_HEIGHT
        total_h = len(self._materials_list) * item_h

        top_px = top_frac * total_h
        bot_px = bot_frac * total_h

        buf = Visualization.MATERIAL_SCALE_RENDER_BUFFER
        first_visible = max(0, int(top_px // item_h) - buf)
        last_visible  = min(len(self._materials_list) - 1, int(bot_px // item_h) + buf)

        # Render newly visible slots
        for i in range(first_visible, last_visible + 1):
            if self._scale_slots[i] is None:
                self._render_scale_slot(i)

        # Destroy slots that are far off-screen
        destroy_buffer = buf + 2
        for i, slot in list(self._scale_slots.items()):
            if slot is not None and (i < first_visible - destroy_buffer or i > last_visible + destroy_buffer):
                self._destroy_scale_slot(i)
    
    def _render_scale_slot(self, index: int) -> None:
        """
        Create and embed a matplotlib figure for the material at the given slot index.

        Args:
            index: Slot index into self._materials_list
        """
        canvas = self._scales_canvas
        material_name = self._materials_list[index]
        viz_state = self._scales_viz_state
        item_h = Visualization.MATERIAL_SCALE_ITEM_HEIGHT

        fig = Figure(
            figsize=(Visualization.SCALE_FIGURE_WIDTH, Visualization.SCALE_FIGURE_HEIGHT),
            dpi=FigureProperties.DPI_DISPLAY
        )

        try:
            ax = fig.add_subplot(111)
            self.viz_controller.create_material_scale(ax, material_name, viz_state)

            current_size = fig.get_size_inches()
            fig.set_size_inches(current_size * (100 / FigureProperties.DPI))

            frame = ttk.Frame(canvas)
            mpl_canvas = FigureCanvasTkAgg(fig, master=frame)
            mpl_canvas.draw()

            widget = mpl_canvas.get_tk_widget()
            widget.config(
                width=Visualization.SCALE_CANVAS_WIDTH,
                height=Visualization.SCALE_CANVAS_HEIGHT
            )
            widget.pack(fill='both', expand=True)

            window_id = canvas.create_window(
                0,
                index * item_h + UI.WIDGET_SPACING_LARGE,
                window=frame,
                anchor="nw",
                width=Visualization.MATERIAL_PANEL_WIDTH
            )

            self._scale_slots[index] = {
                'frame': frame,
                'canvas_ref': mpl_canvas,
                'fig': fig,
                'window_id': window_id
            }
            logger.debug(f"Rendered scale slot {index}: {material_name}")

        except Exception as e:
            logger.error(f"Failed to render scale slot {index} ({material_name}): {e}")
            pyplot.close(fig)
            raise
    
    def _destroy_scale_slot(self, index: int) -> None:
        """
        Destroy the matplotlib figure and Tk widgets for the given slot index,
        freeing memory. The slot entry is set back to None.

        Args:
            index: Slot index into self._materials_list
        """
        slot = self._scale_slots.get(index)
        if slot is None:
            return

        try:
            self._scales_canvas.delete(slot['window_id'])
            slot['canvas_ref'].get_tk_widget().destroy()
            pyplot.close(slot['fig'])
            slot['frame'].destroy()
            logger.debug(f"Destroyed scale slot {index}")
        except Exception as e:
            logger.warning(f"Cleanup warning for slot {index}: {e}")
        finally:
            self._scale_slots[index] = None
    
    def _draw_material_scale(
        self,
        parent: tk.Widget,
        material_name: str,
        viz_state: VisualizationState
    ) -> None:
        """
        Draw concentration scale for a material (deprecated).
        
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
            material_scales = self._collect_all_material_scales()
            save_figure_to_path(figure, path, material_scales)
            self._close_temp_export_figs()
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
            material_scales = self._collect_all_material_scales()
            save_figures_to_pdf(self.figures_to_save, path, material_scales)
            self._close_temp_export_figs()
        except (IOError, OSError):
            logger.error("Failed to write PDF file")
            messagebox.showerror(Messages.WRITE_ERROR_TITLE, Messages.WRITE_ERROR_TEXT)
            return

        messagebox.showinfo("Saving Complete", f"Successfully saved layout file: {os.path.basename(path)}")
        logger.info(f"Successfully saved PDF: {path}")
    
    def _collect_all_material_scales(self) -> List[Figure]:
        """
        Render all material scale figures for export (PDF/PNG).
        Figures that are already live in _scale_slots are reused;
        the rest are rendered temporarily and closed after saving.
        Returns an ordered list of matplotlib Figures.
        """
        figures = []
        temp_indices = []

        for i, material_name in enumerate(self._materials_list):
            slot = self._scale_slots[i]
            if slot is not None:
                figures.append(slot['fig'])
            else:
                # Render temporarily
                fig = Figure(
                    figsize=(Visualization.SCALE_FIGURE_WIDTH, Visualization.SCALE_FIGURE_HEIGHT),
                    dpi=FigureProperties.DPI_DISPLAY
                )
                ax = fig.add_subplot(111)
                self.viz_controller.create_material_scale(ax, material_name, self._scales_viz_state)
                figures.append(fig)
                temp_indices.append((i, fig))

        # Store temp figs so caller can close them after saving
        self._temp_export_figs = [fig for _, fig in temp_indices]
        return figures

    def _close_temp_export_figs(self) -> None:
        """Close figures that were temporarily created for export."""
        for fig in getattr(self, '_temp_export_figs', []):
            pyplot.close(fig)
        self._temp_export_figs = []
    
    
    def _cleanup_and_close(self) -> None:
        """Cleanup matplotlib resources and close window."""
        try:
            self._cleanup_canvas_widgets(self.window)
            # Destroy any live scale slots explicitly
            for i in list(self._scale_slots.keys()):
                self._destroy_scale_slot(i)
            self._scale_slots = {}
            self._materials_list = []
            self._scales_canvas = None
            self._scales_viz_state = None
            self._close_temp_export_figs()
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
            if self.on_window_closed:
                self.on_window_closed()
    
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
