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
# Description:  DZN generation window view for MPLACE application.
# Pure view layer - handles only UI display and user input.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.5
# Last Revision: April 2026
#

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Callable, Optional, Tuple

from controllers.dzn_controller import DznController
from models.dzn_data import DznFormData
from models.constants import (
    PlateDefaults, UI, WindowConfig, MaterialDefaults, 
    FileTypes, Messages
)
from models.dto import ValidationVerdict
from ui.ui_tooltip import CreateToolTip
from ui.ui_validators import numeric_entry_callback

logger = logging.getLogger(__name__)


class DznView:
    """
    DZN generation window UI - pure view layer.
    
    This class handles only the visual presentation and user interactions
    for DZN file generation. All business logic is delegated to DznController.
    
    Attributes:
        parent: Parent Tkinter window
        controller: DZN controller instance
        on_generation_complete: Callback when DZN generation completes
        on_window_closed: Callback when the window is closed
    """
    
    def __init__(
        self,
        parent: tk.Tk,
        controller: DznController,
        on_generation_complete: Callable[[str, str, str, str], None],
        on_window_closed: Optional[Callable[[], None]] = None
    ):
        """
        Initialize DZN generation view.
        
        Args:
            parent: Parent window
            controller: DZN controller instance
            on_generation_complete: Callback(file_path, rows, cols, controls) when done
        """
        self.parent = parent
        self.controller = controller
        self.on_generation_complete = on_generation_complete
        self.on_window_closed = on_window_closed
        
        # Create window
        self.window = tk.Toplevel(self.parent)
        self.window.title(WindowConfig.TITLE_DZN_GENERATOR)
        self.window.resizable(False, False)
        self.window.protocol('WM_DELETE_WINDOW', self._on_close)
        self.window.withdraw()
        
        # Validation command for numeric entries
        self.vcmd = (self.window.register(numeric_entry_callback))
        
        # Initialize UI state variables
        self._init_variables()
        
        # Build UI
        self._setup_ui()
        
        # Initialize with defaults
        self.reset_to_defaults()
        
        logger.info("DZN view initialized")
    
    def _init_variables(self) -> None:
        """Initialize all Tkinter variables."""
        # Flags
        self.flag_allow_empty_wells = tk.BooleanVar()
        self.flag_concentrations_on_different_rows = tk.BooleanVar()
        self.flag_concentrations_on_different_columns = tk.BooleanVar()
        self.flag_replicates_on_different_plates = tk.BooleanVar()
        self.flag_replicates_on_same_plate = tk.BooleanVar()
        
        # Dimensions
        self.num_rows = tk.StringVar(self.window)
        self.num_cols = tk.StringVar(self.window)
        
        # Layout
        self.inner_empty_edge = tk.BooleanVar()
        self.size_empty_edge = tk.StringVar(self.window)
        self.size_corner_empty_wells = tk.StringVar(self.window)
        self.horizontal_cell_lines = tk.StringVar(self.window)
        self.vertical_cell_lines = tk.StringVar(self.window)
        
        # Materials
        self.drugs = tk.StringVar(self.window)
        self.controls = tk.StringVar(self.window)
    
    def _setup_ui(self) -> None:
        """Create all UI widgets."""
        # Main frames
        self.frame_flags = ttk.LabelFrame(self.window, text='Main properties:')
        self.frame_dimensions = ttk.LabelFrame(self.window, text='Plate dimensions:')
        self.frame_layout = ttk.LabelFrame(self.window, text='Layout properties:')
        self.frame_materials = ttk.LabelFrame(self.window, text='Materials:')
        self.button_generate = ttk.Button(
            self.window, 
            state=tk.NORMAL, 
            text='Generate *.dzn file',
            command=self._on_generate
        )
        
        # Setup each section
        self._setup_flags_section()
        self._setup_dimensions_section()
        self._setup_layout_section()
        self._setup_materials_section()
        
        # Place frames
        self._place_frames()
    
    def _setup_flags_section(self) -> None:
        """Create flags section widgets."""
        # Labels
        labels = [
            ('Allow empty wells', 0),
            ('Replicates on different rows', 1),
            ('Replicates on different columns', 2),
            ('Replicates on different plates', 3),
            ('Replicates on the same plate', 4)
        ]
        
        tooltips = [
            'If enabled, the model will check if there are any empty wells within a plate line.\nIf yes, the model will fail.\nIf disabled, then no such check is performed, i.e. a plate line can have empty wells within it.',
            'If enabled, the model will try to force replicates of each drug to be placed on different rows.\nIf there are too many replicates, no such attempt will be made.\nIf the number of replicates per drug is small enough, it will also try to ensure that this drug placement is enforced across multiple plates.\nNOTE: if the model is unsatisfiable try to disable this option',
            'If enabled, the model will try to force replicates of each drug to be placed on different columns.\nIf there are too many replicates, no such attempt will be made.\nIf the number of replicates per drug is small enough, it will also try to ensure that this drug placement is enforced across multiple plates.\nNOTE: if the model is unsatisfiable try to disable this option',
            'If enabled, replicates of a drug can be placed on different microplates.',
            'If enabled, all replicates of a single drug must be placed on the same microplate.'
        ]
        
        variables = [
            self.flag_allow_empty_wells,
            self.flag_concentrations_on_different_rows,
            self.flag_concentrations_on_different_columns,
            self.flag_replicates_on_different_plates,
            self.flag_replicates_on_same_plate
        ]
        
        for (text, row), tooltip, var in zip(labels, tooltips, variables):
            label = tk.Label(self.frame_flags, text=text)
            label.grid(row=row, column=0, sticky="w")
            CreateToolTip(label, text=tooltip)
            
            check = ttk.Checkbutton(self.frame_flags, variable=var, onvalue=True, offvalue=False)
            check.grid(row=row, column=1, sticky="w")
        
        # Special handling for mutually exclusive replicates options
        variables[3].trace_add('write', lambda *args: self._on_replicates_different_changed())
        variables[4].trace_add('write', lambda *args: self._on_replicates_same_changed())
    
    def _setup_dimensions_section(self) -> None:
        """Create dimensions section widgets."""
        dimensions = [
            ('Number of rows', self.num_rows, 'Enter the number of rows of the microplate'),
            ('Number of columns', self.num_cols, 'Enter the number of columns of the microplate')
        ]
        
        for row, (text, var, tooltip) in enumerate(dimensions):
            label = tk.Label(self.frame_dimensions, text=text)
            label.grid(row=row, column=0, sticky="w")
            CreateToolTip(label, text=tooltip)
            
            entry = ttk.Entry(
                self.frame_dimensions, 
                textvariable=var, 
                width=UI.ENTRY_WIDTH_NUMERIC,
                validate='all', 
                validatecommand=(self.vcmd, '%P')
            )
            entry.grid(row=row, column=1, sticky="w")
    
    def _setup_layout_section(self) -> None:
        """Create layout section widgets."""
        # Inner empty edge checkbox
        label = tk.Label(self.frame_layout, text='Inner edge')
        label.grid(row=0, column=0, sticky="w")
        CreateToolTip(label, text='When set to True, each plate line will have an edge of empty wells.\nWhen False, the whole plate will have an outer edge, but not each individual plate line.\nSee Figure 2 of COMPD article.')
        
        check = ttk.Checkbutton(
            self.frame_layout, 
            variable=self.inner_empty_edge, 
            onvalue=True, 
            offvalue=False
        )
        check.grid(row=0, column=1, sticky="w")
        
        # Numeric fields
        fields = [
            ('Empty edge size', self.size_empty_edge, 'How thick the empty edge is. The number must be no less than 0', 1),
            ('Empty corner size', self.size_corner_empty_wells, 'The size of a corner filled with empty wells only. IGNORED by PLAID.\nIf used together with "replicates on different rows/columns" may result in no solutions. The number must be no less than 0', 2),
            ('Number of horizontal lines', self.horizontal_cell_lines, 'How many horizontal plate lines is required? No less than 1', 3),
            ('Number of vertical lines', self.vertical_cell_lines, 'How many vertical plate lines is required? No less than 1', 4)
        ]
        
        for text, var, tooltip, row in fields:
            label = tk.Label(self.frame_layout, text=text)
            label.grid(row=row, column=0, sticky="w")
            CreateToolTip(label, text=tooltip)
            
            entry = ttk.Entry(
                self.frame_layout, 
                textvariable=var, 
                width=UI.ENTRY_WIDTH_NUMERIC,
                validate='all', 
                validatecommand=(self.vcmd, '%P')
            )
            entry.grid(row=row, column=1, sticky="w")
    
    def _setup_materials_section(self) -> None:
        """Create materials section widgets."""
        materials = [
            ('List of compounds \nwith concentrations', self.drugs, 
             "List all the materials and their concentrations.\nWe use the format of Python dictionaries: {'Drug1': [5,'2', 'N/A'], 'Drug2': [10, '0.1', '0.5', '10']},\nwhich means that we will have:\n - Drug1 in concentrations '2' and 'N/A' (5 replicates each) and\n - Drug2 in concentrations 0.1, 0.5 and 10 (10 replicates each).\nI recommend to write down the list of materials in the spreadsheet `Convert the compounds and controls.xlsx`,\navailable at https://github.com/astra-uu-se/MPLACE, and then copy generated text here", 0),
            ('List of controls \nwith concentrations:', self.controls,
             "List all the controls and their concentrations.\nWe use the same format as the list of materials.\nAs an illustration, here is another example, for controls:\n   {'Control1': [5, '2', 'N/A'], 'pos': [10, '100'], 'DMSO': [3, '100']},\nwhere we have three different controls.\nAs you can see, the dictionary format allows us to use various number of drugs/controls,\nwhere each drug/control can have its own number of replicates and/or the list concentrations", 1)
        ]
        
        for text, var, tooltip, row in materials:
            label = tk.Label(self.frame_materials, text=text)
            label.grid(row=row, column=0, sticky="w")
            
            entry = ttk.Entry(
                self.frame_materials, 
                textvariable=var, 
                width=UI.ENTRY_WIDTH_MATERIALS
            )
            entry.grid(row=row, column=1, sticky="w")
            
            help_label = tk.Label(self.frame_materials, text='?', relief='raised')
            help_label.grid(row=row, column=2, sticky="w")
            CreateToolTip(help_label, text=tooltip)
    
    def _place_frames(self) -> None:
        """Place all frames in window."""
        self.frame_flags.grid(
            row=0, column=0, rowspan=2, columnspan=1, 
            sticky="nw", padx=UI.GRID_PADDING, pady=UI.GRID_PADDING
        )
        self.frame_dimensions.grid(
            row=0, column=1, rowspan=1, columnspan=1,
            sticky="nw", padx=UI.GRID_PADDING, pady=UI.GRID_PADDING
        )
        self.frame_layout.grid(
            row=1, column=1, rowspan=1, columnspan=1, 
            sticky="nw", padx=UI.GRID_PADDING, pady=UI.GRID_PADDING
        )
        self.frame_materials.grid(
            row=2, column=0, rowspan=1, columnspan=2,
            sticky="w", padx=UI.GRID_PADDING, pady=UI.GRID_PADDING
        )
        self.button_generate.grid(
            row=3, column=0, rowspan=1, columnspan=2,
            sticky="ew", padx=UI.GRID_PADDING, pady=UI.GRID_PADDING
        )
    
    # Event Handlers
    
    def _on_replicates_different_changed(self) -> None:
        """Handle replicates on different plates checkbox change."""
        if self.flag_replicates_on_different_plates.get():
            self.flag_replicates_on_same_plate.set(False)
    
    def _on_replicates_same_changed(self) -> None:
        """Handle replicates on same plate checkbox change."""
        if self.flag_replicates_on_same_plate.get():
            self.flag_replicates_on_different_plates.set(False)

    def _on_generate(self) -> None:
        """Handle generate button click."""
        logger.info("Generate DZN button clicked")

        # Collect form data
        form_data = DznFormData(
            num_rows=self.num_rows.get(),
            num_cols=self.num_cols.get(),
            inner_empty_edge=self.inner_empty_edge.get(),
            size_empty_edge=self.size_empty_edge.get(),
            size_corner_empty_wells=self.size_corner_empty_wells.get(),
            horizontal_cell_lines=self.horizontal_cell_lines.get(),
            vertical_cell_lines=self.vertical_cell_lines.get(),
            flag_allow_empty_wells=self.flag_allow_empty_wells.get(),
            flag_concentrations_on_different_rows=self.flag_concentrations_on_different_rows.get(),
            flag_concentrations_on_different_columns=self.flag_concentrations_on_different_columns.get(),
            flag_replicates_on_different_plates=self.flag_replicates_on_different_plates.get(),
            flag_replicates_on_same_plate=self.flag_replicates_on_same_plate.get(),
            compounds_dict=self.drugs.get(),
            controls_dict=self.controls.get()
        )
        self.button_generate.config(state=tk.DISABLED, text='Generating...')
        self.window.update_idletasks()

        try:
            # Step 1: UI-level validation
            errors = self.controller.validate_form_data(form_data)
            if errors:
                logger.warning(f"DZN validation failed: {len(errors)} errors")
                error_message = '\n'.join([f"{i+1}. {err}" for i, err in enumerate(errors)])
                messagebox.showerror("Input Validation Error", error_message)
                return

            # Step 2: Model compatibility validation
            verdict = self.controller.validate_model_compat(form_data)

            if verdict.both_blocked():
                msg = _format_verdict_message(verdict)
                messagebox.showerror("Incompatible with All Models", msg)
                return

            if verdict.any_issues():
                msg = _format_verdict_message(verdict)
                proceed = messagebox.askokcancel("Model Compatibility Warnings", msg +
                                                 "\n\nProceed with file generation?")
                if not proceed:
                    return

            # Step 3: Generate and save
            dzn_content, control_names = self.controller.generate_dzn_content(form_data, verdict)
            logger.info(f"DZN content generated: {len(dzn_content)} characters")
    
            # Save via controller
            file_path = self.controller.save_dzn_file(dzn_content)
    
            if file_path:
                logger.info(f"DZN saved successfully: {file_path}")
        
                # Notify callback
                self.on_generation_complete(
                    file_path,
                    form_data.num_rows,
                    form_data.num_cols,
                    str(control_names)
                )
        
                # Hide window
                self.hide()
                self.parent.focus_force()
            else:
                logger.info("DZN save cancelled by user")
    
        except Exception as e:
            logger.error(f"DZN generation failed: {e}")
            messagebox.showerror("Error", f"DZN generation failed:\n{str(e)}")
        finally:
            self.button_generate.config(state=tk.NORMAL, text='Generate *.dzn file')
    
    def _on_close(self) -> None:
        """Handle window close button."""
        self.hide()
        self.parent.focus_force()
    
    # Public Methods
    
    def show(self) -> None:
        """Show the DZN generation window."""
        self.reset_to_defaults()
        self.window.deiconify()
        self.window.grab_set()
        
        # get the coordinates for the window position
        x = self.parent.winfo_rootx() + WindowConfig.DZN_WINDOW_X
        y = self.parent.winfo_rooty() + WindowConfig.DZN_WINDOW_Y
        
        self.window.geometry(f'+{x}+{y}')
        
        logger.debug("DZN window shown")
    
    def hide(self) -> None:
        """Hide the DZN generation window."""
        self.window.withdraw()
        self.window.grab_release()
        if self.on_window_closed:
            self.on_window_closed()
        logger.debug("DZN window hidden")
    
    def reset_to_defaults(self) -> None:
        """Reset all form fields to defaults."""
        self.flag_allow_empty_wells.set(True)
        self.flag_concentrations_on_different_rows.set(True)
        self.flag_concentrations_on_different_columns.set(True)
        self.flag_replicates_on_different_plates.set(False)
        self.flag_replicates_on_same_plate.set(False)
        
        self.num_rows.set(PlateDefaults.ROWS)
        self.num_cols.set(PlateDefaults.COLS)
        
        self.inner_empty_edge.set(True)
        self.size_empty_edge.set(PlateDefaults.EMPTY_EDGE_SIZE)
        self.size_corner_empty_wells.set(PlateDefaults.CORNER_EMPTY_WELLS)
        self.horizontal_cell_lines.set(PlateDefaults.CELL_LINES)
        self.vertical_cell_lines.set(PlateDefaults.CELL_LINES)
        
        self.drugs.set(MaterialDefaults.DEFAULT_DRUGS)
        self.controls.set(MaterialDefaults.DEFAULT_CONTROLS)
        
        logger.debug("DZN form reset to defaults")

def _format_verdict_message(verdict: ValidationVerdict) -> str:
    """Format a ValidationVerdict into a human-readable message for dialogs."""
    lines = []

    if verdict.plaid.blocked:
        lines.append("PLAID: BLOCKED (see reasons below)")
    elif verdict.plaid.messages:
        lines.append("PLAID: WARNINGS (see reasons below)")
    else:
        lines.append("PLAID: Compatible")

    for m in verdict.plaid.messages:
        lines.append(f"  {m}")

    lines.append("")

    if verdict.compd.blocked:
        lines.append("COMPD: BLOCKED (see reasons below)")
    elif verdict.compd.messages:
        lines.append("COMPD: WARNINGS (see reasons below)")
    else:
        lines.append("COMPD: Compatible")

    for m in verdict.compd.messages:
        lines.append(f"  {m}")

    return "\n".join(lines)
