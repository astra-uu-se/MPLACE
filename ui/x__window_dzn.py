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
# Description:  GUI for generating MiniZinc files for PLAID and other similar models
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.0
# Last Revision: October 2025
#


import tkinter as tk
from tkinter import ttk, VERTICAL, RIGHT, Y, LEFT, BOTH, SOLID, filedialog, messagebox
from typing import Dict, Any, List, Tuple, Callable, Optional
from dataclasses import dataclass
import logging

import ast
import re

from models.dto import DznBuildParams, DznGenerationResult
from models.constants import PlateDefaults, UI, WindowConfig, MaterialDefaults, FileTypes
from core.validators import (parse_materials_dict, validate_materials_schema,
                             validate_plate_dimensions, format_validation_errors)
from core.dzn_writer import build_dzn_text
from ui.ui_tooltip import CreateToolTip
from ui.ui_validators import numeric_entry_callback

# Configure logging for DZN generation module
logger = logging.getLogger(__name__)


# Callback function for communicating with main window
completion_callback: Optional[Callable[[DznGenerationResult], None]] = None


def set_completion_callback(callback: Callable[[DznGenerationResult], None]) -> None:
    """Set callback function to be called when DZN generation is complete.
    
    Args:
        callback: Function to call with DznGenerationResult when generation completes
    """
    global completion_callback
    completion_callback = callback
    logger.debug("DZN completion callback registered")


def generate_dzn_file() -> None:
    """Generate DZN file from user input parameters with comprehensive validation."""
    logger.info("Starting DZN file generation with validation")
    
    # Collect all validation errors before showing any dialogs
    all_errors = []
    
    # Step 0 - Basic field validation
    if (num_cols.get() == '' or num_rows.get() == '' or size_empty_edge.get() == '' 
        or size_corner_empty_wells.get() == '' or horizontal_cell_lines.get() == '' 
        or vertical_cell_lines.get() == '' or drugs.get() == '' or controls.get() == ''):
        all_errors.append("All fields must be filled in")
    
    # Validate plate dimensions
    dimension_errors = validate_plate_dimensions(num_rows.get(), num_cols.get())
    all_errors.extend(dimension_errors)
    
    # Parse and validate compounds
    compounds_dict, parsing_errors = parse_materials_dict(drugs.get())
    all_errors.extend(parsing_errors)
    
    if not parsing_errors:  # Only validate schema if parsing succeeded
        schema_errors = validate_materials_schema(compounds_dict, "compounds")
        all_errors.extend(schema_errors)
    
    # Parse and validate controls
    controls_dict, control_parsing_errors = parse_materials_dict(controls.get())
    all_errors.extend(control_parsing_errors)
    
    if not control_parsing_errors:  # Only validate schema if parsing succeeded
        control_schema_errors = validate_materials_schema(controls_dict, "controls")
        all_errors.extend(control_schema_errors)
    
    # If any validation errors, show them all and abort
    if all_errors:
        error_message = format_validation_errors(all_errors)
        print("Input validation failed - check your entries")
        logger.error(f"DZN generation validation failed: {len(all_errors)} errors")
        tk.messagebox.showerror("Input Validation Error", error_message)
        return
    
    # All validation passed - show summary and proceed
    total_compound_wells = sum(compounds_dict[name][0] * len(compounds_dict[name][1:]) for name in compounds_dict)
    total_control_wells = sum(controls_dict[name][0] * len(controls_dict[name][1:]) for name in controls_dict)
    
    print(f"Validated: {len(compounds_dict)} compounds ({total_compound_wells} wells), {len(controls_dict)} controls ({total_control_wells} wells); {num_rows.get()}x{num_cols.get()} plate")
    logger.info(f"Input validation passed: compounds={len(compounds_dict)}({total_compound_wells}), controls={len(controls_dict)}({total_control_wells}), plate={num_rows.get()}x{num_cols.get()}")

    # Step 1 - Generate DZN content using DTO
    params = DznBuildParams(
        num_rows=num_rows.get(),
        num_cols=num_cols.get(),
        inner_empty_edge=inner_empty_edge.get(),
        size_empty_edge=size_empty_edge.get(),
        size_corner_empty_wells=size_corner_empty_wells.get(),
        horizontal_cell_lines=horizontal_cell_lines.get(),
        vertical_cell_lines=vertical_cell_lines.get(),
        flag_allow_empty_wells=flag_allow_empty_wells.get(),
        flag_concentrations_on_different_rows=flag_concentrations_on_different_rows.get(),
        flag_concentrations_on_different_columns=flag_concentrations_on_different_columns.get(),
        flag_replicates_on_different_plates=flag_replicates_on_different_plates.get(),
        flag_replicates_on_same_plate=flag_replicates_on_same_plate.get(),
        compounds_dict=compounds_dict,
        controls_dict=controls_dict,
    )
    
    dzn_txt, control_names_list = build_dzn_text(params)
    logger.debug(f"DZN content generated via DTO: {len(dzn_txt)} characters")

    # Step 2 - Save the results
    path = tk.filedialog.asksaveasfilename(
        defaultextension=".dzn", filetypes=FileTypes.DZN_FILES)

    if path is None or path == '':
        logger.info("DZN save cancelled by user")
        return

    print(f"Saving DZN to: {path}")
    logger.info(f"User selected DZN save path: {path}")

    # Use context manager for file writing
    try:
        with open(path, "w") as dzn_file:
            dzn_file.write(dzn_txt)
        
        print(f"DZN saved successfully: {path}")
        logger.info(f"DZN file saved: {path}, {len(dzn_txt)} characters")
    except (IOError, OSError) as e:
        logger.error(f"DZN write failed: {path}, error: {e}")
        tk.messagebox.showerror("Error", f"Failed to write DZN file: {str(e)}")
        return

    # Notify main window through callback using DTO
    if completion_callback:
        result = DznGenerationResult(
            file_path=path,
            rows=params.num_rows,  # Use DTO field instead of UI state
            cols=params.num_cols,  # Use DTO field instead of UI state
            control_names=str(control_names_list)  # Use returned list
        )
        completion_callback(result)
        logger.debug("DZN completion callback invoked with DTO result")
    else:
        logger.warning("No completion callback registered - main window not updated")

    logger.info("DZN generation completed successfully")
    window.withdraw()


def reset_dzn() -> None:
    """Reset all DZN generation form fields to defaults."""
    flag_allow_empty_wells.set(True)
    flag_concentrations_on_different_rows.set(True)
    flag_concentrations_on_different_columns.set(True)
    flag_replicates_on_different_plates.set(False)
    flag_replicates_on_same_plate.set(False)

    num_rows.set(PlateDefaults.ROWS)
    num_cols.set(PlateDefaults.COLS)

    inner_empty_edge.set(True)
    size_empty_edge.set(PlateDefaults.EMPTY_EDGE_SIZE)
    size_corner_empty_wells.set(PlateDefaults.CORNER_EMPTY_WELLS)
    horizontal_cell_lines.set(PlateDefaults.CELL_LINES)
    vertical_cell_lines.set(PlateDefaults.CELL_LINES)

    drugs.set(MaterialDefaults.DEFAULT_DRUGS)
    controls.set(MaterialDefaults.DEFAULT_CONTROLS)
    
    logger.debug("DZN form reset to defaults")


def gen_dzn_show() -> None:
    """Show the DZN generation window."""
    window.deiconify()
    logger.debug("DZN generation window shown")


def check_replicates_on_different_plates() -> None:
    """Ensure mutually exclusive replicate placement options."""
    if flag_replicates_on_different_plates.get() == True:
        flag_replicates_on_same_plate.set(False)


def check_replicates_on_same_plate() -> None:
    """Ensure mutually exclusive replicate placement options."""
    if flag_replicates_on_same_plate.get() == True:
        flag_replicates_on_different_plates.set(False)


# Main window setup
window: tk.Tk = tk.Tk()
window.title(WindowConfig.TITLE_DZN_GENERATOR)
window.resizable(False, False)
window.geometry(f'+{WindowConfig.DZN_WINDOW_X}+{WindowConfig.DZN_WINDOW_Y}')
window.protocol('WM_DELETE_WINDOW', window.withdraw)
window.withdraw()

menu_bar = tk.Menu(window)

# Local variables
vcmd: Tuple = (window.register(numeric_entry_callback))

flag_allow_empty_wells: tk.BooleanVar = tk.BooleanVar()
flag_concentrations_on_different_rows: tk.BooleanVar = tk.BooleanVar()
flag_concentrations_on_different_columns: tk.BooleanVar = tk.BooleanVar()
flag_replicates_on_different_plates: tk.BooleanVar = tk.BooleanVar()
flag_replicates_on_same_plate: tk.BooleanVar = tk.BooleanVar()

num_rows: tk.StringVar = tk.StringVar(window)
num_cols: tk.StringVar = tk.StringVar(window)

inner_empty_edge: tk.BooleanVar = tk.BooleanVar()
size_empty_edge: tk.StringVar = tk.StringVar(window)
size_corner_empty_wells: tk.StringVar = tk.StringVar(window)
horizontal_cell_lines: tk.StringVar = tk.StringVar(window)
vertical_cell_lines: tk.StringVar = tk.StringVar(window)

drugs: tk.StringVar = tk.StringVar(window)
controls: tk.StringVar = tk.StringVar(window)

# UI elements
frame_flags: ttk.LabelFrame = ttk.LabelFrame(window, text='Main properties:')
frame_dimensions: ttk.LabelFrame = ttk.LabelFrame(window, text='Plate dimensions:')
frame_layout: ttk.LabelFrame = ttk.LabelFrame(window, text='Layout properties:')
frame_materials: ttk.LabelFrame = ttk.LabelFrame(window, text='Materials:')
button_generate: ttk.Button = ttk.Button(window, state=tk.NORMAL, text='Generate *.dzn file')

# Flags section
label_flag_allow_empty_wells: tk.Label = tk.Label(frame_flags, text='Allow empty wells')
label_flag_concentrations_on_different_rows: tk.Label = tk.Label(
    frame_flags, text='Replicates on different rows')
label_flag_concentrations_on_different_columns: tk.Label = tk.Label(
    frame_flags, text='Replicates on different columns')
label_flag_replicates_on_different_plates: tk.Label = tk.Label(
    frame_flags, text='Replicates on different plates')
label_flag_replicates_on_same_plate: tk.Label = tk.Label(
    frame_flags, text='Replicates on the same plate')

check_flag_allow_empty_wells: ttk.Checkbutton = ttk.Checkbutton(
    frame_flags, variable=flag_allow_empty_wells, onvalue=True, offvalue=False)
check_flag_concentrations_on_different_rows: ttk.Checkbutton = ttk.Checkbutton(
    frame_flags, variable=flag_concentrations_on_different_rows, onvalue=True, offvalue=False)
check_flag_concentrations_on_different_columns: ttk.Checkbutton = ttk.Checkbutton(
    frame_flags, variable=flag_concentrations_on_different_columns, onvalue=True, offvalue=False)
check_flag_replicates_on_different_plates: ttk.Checkbutton = ttk.Checkbutton(
    frame_flags, variable=flag_replicates_on_different_plates, onvalue=True, offvalue=False)
check_flag_replicates_on_same_plate: ttk.Checkbutton = ttk.Checkbutton(
    frame_flags, variable=flag_replicates_on_same_plate, onvalue=True, offvalue=False)

# Dimensions section
label_rows: tk.Label = tk.Label(frame_dimensions, text='Number of rows')
label_cols: tk.Label = tk.Label(frame_dimensions, text='Number of columns')

entry_rows: ttk.Entry = ttk.Entry(frame_dimensions, textvariable=num_rows, width=UI.ENTRY_WIDTH_NUMERIC,
                       validate='all', validatecommand=(vcmd, '%P'))
entry_cols: ttk.Entry = ttk.Entry(frame_dimensions, textvariable=num_cols, width=UI.ENTRY_WIDTH_NUMERIC,
                       validate='all', validatecommand=(vcmd, '%P'))

# Layout section
label_inner_empty_edge: tk.Label = tk.Label(frame_layout, text='Inner edge')
label_size_empty_edge: tk.Label = tk.Label(frame_layout, text='Empty edge size')
label_corner_empty_wells: tk.Label = tk.Label(frame_layout, text='Empty corner size')
label_horizontal_cell_lines: tk.Label = tk.Label(frame_layout, text='Number of horizontal lines')
label_vertical_cell_lines: tk.Label = tk.Label(frame_layout, text='Number of vertical lines')

check_inner_empty_edge: ttk.Checkbutton = ttk.Checkbutton(
    frame_layout, variable=inner_empty_edge, onvalue=True, offvalue=False)
entry_size_empty_edge: ttk.Entry = ttk.Entry(frame_layout, textvariable=size_empty_edge, width=UI.ENTRY_WIDTH_NUMERIC,
                                  validate='all', validatecommand=(vcmd, '%P'))
entry_corner_empty_wells: ttk.Entry = ttk.Entry(frame_layout, textvariable=size_corner_empty_wells, width=UI.ENTRY_WIDTH_NUMERIC,
                                     validate='all', validatecommand=(vcmd, '%P'))
entry_horizontal_cell_lines: ttk.Entry = ttk.Entry(frame_layout, textvariable=horizontal_cell_lines, width=UI.ENTRY_WIDTH_NUMERIC,
                                        validate='all', validatecommand=(vcmd, '%P'))
entry_vertical_cell_lines: ttk.Entry = ttk.Entry(frame_layout, textvariable=vertical_cell_lines, width=UI.ENTRY_WIDTH_NUMERIC,
                                      validate='all', validatecommand=(vcmd, '%P'))

# Materials section
label_drugs: tk.Label = tk.Label(frame_materials, text='List of compounds \nwith concentrations')
label_controls: tk.Label = tk.Label(frame_materials, text='List of controls \nwith concentrations:')
entry_drugs: ttk.Entry = ttk.Entry(frame_materials, textvariable=drugs, width=UI.ENTRY_WIDTH_MATERIALS)
entry_controls: ttk.Entry = ttk.Entry(frame_materials, textvariable=controls, width=UI.ENTRY_WIDTH_MATERIALS)
help_drugs: tk.Label = tk.Label(frame_materials, text='?', relief='raised')
help_controls: tk.Label = tk.Label(frame_materials, text='?', relief='raised')

# UI placement
frame_flags.grid(row=0, column=0, rowspan=2, columnspan=1, sticky="nw", padx=UI.GRID_PADDING, pady=UI.GRID_PADDING)
frame_dimensions.grid(row=0, column=1, rowspan=1, columnspan=1,
                      sticky="nw", padx=UI.GRID_PADDING, pady=UI.GRID_PADDING)
frame_layout.grid(row=1, column=1, rowspan=1, columnspan=1, sticky="nw", padx=UI.GRID_PADDING, pady=UI.GRID_PADDING)
frame_materials.grid(row=2, column=0, rowspan=1, columnspan=2,
                     sticky="w", padx=UI.GRID_PADDING, pady=UI.GRID_PADDING)
button_generate.grid(row=3, column=0, rowspan=1, columnspan=2,
                     sticky="ew", padx=UI.GRID_PADDING, pady=UI.GRID_PADDING)

# Flags placement
label_flag_allow_empty_wells.grid(row=0, column=0, columnspan=1, sticky="w")
label_flag_concentrations_on_different_rows.grid(
    row=1, column=0, columnspan=1, sticky="w")
label_flag_concentrations_on_different_columns.grid(
    row=2, column=0, columnspan=1, sticky="w")
label_flag_replicates_on_different_plates.grid(
    row=3, column=0, columnspan=1, sticky="w")
label_flag_replicates_on_same_plate.grid(row=4, column=0, columnspan=1, sticky="w")
check_flag_allow_empty_wells.grid(row=0, column=1, columnspan=1, sticky="w")
check_flag_concentrations_on_different_rows.grid(
    row=1, column=1, columnspan=1, sticky="w")
check_flag_concentrations_on_different_columns.grid(
    row=2, column=1, columnspan=1, sticky="w")
check_flag_replicates_on_different_plates.grid(
    row=3, column=1, columnspan=1, sticky="w")
check_flag_replicates_on_same_plate.grid(row=4, column=1, columnspan=1, sticky="w")

# Dimensions placement
label_rows.grid(row=0, column=0, columnspan=1, sticky="w")
entry_rows.grid(row=0, column=1, columnspan=1, sticky="w")
label_cols.grid(row=1, column=0, columnspan=1, sticky="w")
entry_cols.grid(row=1, column=1, columnspan=1, sticky="w")

# Layout placement
label_inner_empty_edge.grid(row=0, column=0, columnspan=1, sticky="w")
label_size_empty_edge.grid(row=1, column=0, columnspan=1, sticky="w")
label_corner_empty_wells.grid(row=2, column=0, columnspan=1, sticky="w")
label_horizontal_cell_lines.grid(row=3, column=0, columnspan=1, sticky="w")
label_vertical_cell_lines.grid(row=4, column=0, columnspan=1, sticky="w")
check_inner_empty_edge.grid(row=0, column=1, columnspan=1, sticky="w")
entry_size_empty_edge.grid(row=1, column=1, columnspan=1, sticky="w")
entry_corner_empty_wells.grid(row=2, column=1, columnspan=1, sticky="w")
entry_horizontal_cell_lines.grid(row=3, column=1, columnspan=1, sticky="w")
entry_vertical_cell_lines.grid(row=4, column=1, columnspan=1, sticky="w")

# Materials placement
label_drugs.grid(row=0, column=0, columnspan=1, sticky="w")
label_controls.grid(row=1, column=0, columnspan=1, sticky="w")
entry_drugs.grid(row=0, column=1, columnspan=1, sticky="w")
entry_controls.grid(row=1, column=1, columnspan=1, sticky="w")
help_drugs.grid(row=0, column=2, columnspan=1, sticky="w")
help_controls.grid(row=1, column=2, columnspan=1, sticky="w")

# UI events and tooltips
CreateToolTip(label_flag_allow_empty_wells,
              text='If enabled, the model will check if there are any empty wells within a plate line.\nIf yes, the model will fail.\nIf disabled, then no such check is performed, i.e. a plate line can have empty wells within it.')
CreateToolTip(label_flag_concentrations_on_different_rows, 
              text='If enabled, the model will try to force replicates of each drug to be placed on different rows.\nIf there are too many replicates, no such attempt will be made.\nIf the number of replicates per drug is small enough, it will also try to ensure that this drug placement is enforced across multiple plates.\nNOTE: if the model is unsatisfiable try to disable this option')
CreateToolTip(label_flag_concentrations_on_different_columns, 
              text='If enabled, the model will try to force replicates of each drug to be placed on different columns.\nIf there are too many replicates, no such attempt will be made.\nIf the number of replicates per drug is small enough, it will also try to ensure that this drug placement is enforced across multiple plates.\nNOTE: if the model is unsatisfiable try to disable this option')
CreateToolTip(label_flag_replicates_on_different_plates,
              text='If enabled, replicates of a drug can be placed on different microplates.')
CreateToolTip(label_flag_replicates_on_same_plate,
              text='If enabled, all replicates of a single drug must be placed on the same microplate.')

CreateToolTip(label_rows, text='Enter the number of rows of the microplate')
CreateToolTip(label_cols, text='Enter the number of columns of the microplate')

CreateToolTip(label_inner_empty_edge, 
              text='When set to True, each plate line will have an edge of empty wells.\nWhen False, the whole plate will have an outer edge, but not each individual plate line.\nSee Figure 2 of COMPD article.')
CreateToolTip(label_size_empty_edge,
              text='How thick the empty edge is. The number must be no less than 0')
CreateToolTip(label_corner_empty_wells, 
              text='The size of a corner filled with empty wells only. IGNORED by PLAID.\nIf used together with "replicates on different rows/columns" may result in no solutions. The number must be no less than 0')
CreateToolTip(label_horizontal_cell_lines,
              text='How many horizontal plate lines is required? No less than 1')
CreateToolTip(label_vertical_cell_lines,
              text='How many vertical plate lines is required? No less than 1')

CreateToolTip(
    help_drugs, text="List all the materials and their concentrations.\nWe use the format of Python dictionaries: {'Drug1': [5,'2', 'N/A'], 'Drug2': [10, '0.1', '0.5, '10']},\nwhich means that we will have:\n - Drug1 in concentrations '2' and 'N/A' (5 replicates each) and\n - Drug2 in concentrations 0.1, 0.5 and 10 (10 replicates each).\nI recommend to write down the list of materials in the spreadsheet `Convert the compounds and controls.xlsx`,\navailable at https://github.com/astra-uu-se/MPLACE, and then copy generated text here")
CreateToolTip(
    help_controls, text="List all the controls and their concentrations.\nWe use the same format as the list of materials.\nAs an illustration, here is another example, for controls:\n   {'Control1': [5, '2', 'N/A'], 'pos': [10, '100'], 'DMSO': [3, '100']},\nwhere we have three different controls.\nAs you can see, the dictionary format allows us to use various number of drugs/controls,\nwhere each drug/control can have its own number of replicates and/or the list concentrations")

# Event bindings
check_flag_replicates_on_different_plates.configure(
    command=lambda: check_replicates_on_different_plates())
check_flag_replicates_on_same_plate.configure(
    command=lambda: check_replicates_on_same_plate())
button_generate.configure(command=lambda: generate_dzn_file())

# Initialize with defaults
reset_dzn()
logger.debug("DZN generation window initialized")