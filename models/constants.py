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
# Description: Constants for the MPLACE application
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.5
# Last Revision: April 2026
#


"""
Constants module for MPLACE application.

This module centralizes all magic numbers, default values, and string constants
used throughout the application to improve maintainability and consistency.
"""

import os
from typing import List


class PlateDefaults:
    """Default values for microplate configurations."""
    ROWS = '16'
    COLS = '24'
    EMPTY_EDGE_SIZE = '0'
    CORNER_EMPTY_WELLS = '0'
    CELL_LINES = '1'
    CONTROL_NAMES = '[]'
    

class UI:
    """User interface layout constants."""
    # Widget dimensions
    BUTTON_WIDTH_STANDARD = 13
    ENTRY_WIDTH_NUMERIC = 6
    ENTRY_WIDTH_MATERIALS = 33
    
    # Padding and spacing
    FRAME_PADDING = 10
    GRID_PADDING = 3
    SMALL_PADDING = 2
    WIDGET_SPACING = 1
    WIDGET_SPACING_LARGE = 5
    
    # Grid weights
    GRID_WEIGHT = 1
    
    # Model selection
    SELECT_PLAID = False
    SELECT_COMPD = True


class Alphabet:
    """Letter sequences used for well-coordinate encoding and display.

    Well rows are addressed with capital letters first (A–Z), then two-letter
    combinations where the first letter is capital and the second is lowercase
    (Aa, Ab, …, Az, Ba, …).  Keeping the two sequences as separate lists
    (rather than a single string) lets transform_coordinate and transform_index
    call .index() on each list independently without slicing.
    """
    LETTERS_CAPITAL: List[str] = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K",
                                  "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    LETTERS_LOWERCASE: List[str] = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
                                    "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]


class Visualization:
    """Constants for visualization components."""
    # Panel dimensions
    PLATE_CANVAS_WIDTH = 800
    PLATE_CANVAS_HEIGHT = 500
    MATERIAL_PANEL_WIDTH = 400
    MATERIAL_PANEL_HEIGHT = 500
    
    # Plot settings
    WELL_COORDINATE_OFFSET = 0.5
    
    # Figure dimensions
    SCALE_FIGURE_WIDTH = 4
    SCALE_FIGURE_HEIGHT = 0.6
    
    # Alpha transparency range
    ALPHA_MIN = 0.3
    ALPHA_MAX = 1.0
    
    # Concentration markers range
    CONCENTRATION_SIZE_MIN = 20
    CONCENTRATION_SIZE_MAX = 100
    
    # Add explicit canvas display sizes (in pixels)
    SCALE_CANVAS_WIDTH = 400   # Constrain scale canvas width  
    SCALE_CANVAS_HEIGHT = 117  # Constrain scale canvas height


class Performance:
    """Performance-related constants."""
    COORDINATE_CACHE_SIZE = 2048
    COLORMAP_COLOR_LIMIT = 20


class MainMenu:
    """List of main menu fields' titles."""
    LOAD_DZN  = "Load DZN"
    LOAD_CSV  = "Load CSV"
    GEN_DZN   = "Generate DZN"
    RUN_MZN   = "Run MiniZinc"
    VISUALIZE = "Visualize"
    RESET     = "Reset"
    RCNT_DZN  = "Recent DZN files"
    RCNT_CSV  = "Recent CSV files"


class PathsIni:
    """Configuration file parsing constants."""
    # Configuration keys and prefixes
    MINIZINC_PREFIX = 'minizinc_path'
    PLAID_PREFIX = 'plaid_path'
    COMPD_PREFIX = 'compd_path'
    PLAID_MPC_PREFIX = 'plaid_mpc_path'
    COMPD_MPC_PREFIX = 'compd_mpc_path'
    FILE_ERROR_PLACEHOLDER = 'invalid data'
    
    # Default paths (update these to match your system)
    MINIZINC = 'minizinc'  # Assumes minizinc is in PATH
    PLAID = './mzn/plate-design.mzn'
    PLAID_MPC = './mzn/plaid_default.mpc'
    COMPD = './mzn/plate-optimizer.mzn'
    COMPD_MPC = './mzn/compd_default.mpc'


class Messages:
    """User interface messages and labels."""
    # Status messages
    NO_DZN_LOADED = 'No *.dzn file is loaded'
    NO_CSV_LOADED = 'No *.csv file is loaded'
    
    # Dialog titles and labels
    FRAME_TITLE_DZN = 'Step 1 - Generate OR load the *.dzn file:'
    FRAME_TITLE_CSV = 'Step 2 - Generate OR load the layout (*.csv):'
    FRAME_TITLE_VIZ = 'Step 3 - Visualize the layout (*.csv):'
    
    BUTTON_GENERATE_DZN = 'Generate *.dzn file'
    BUTTON_LOAD_DZN = 'Load *.dzn file'
    BUTTON_RUN_MODEL = 'Run a model'
    BUTTON_LOAD_CSV = 'Load *.csv file'
    BUTTON_VISUALIZE = 'Visualize *.csv'
    BUTTON_RESET = 'Reset all'
    BUTTON_SAVE_LAYOUT = 'Save the layout'
    BUTTON_SAVE_LAYOUTS = 'Save layouts'
    
    # Label texts
    LABEL_ROWS = 'nb rows:'
    LABEL_COLS = 'nb cols:'
    
    # Model types
    MODEL_PLAID = 'PLAID'
    MODEL_COMPD = 'COMPD'
    MODEL_OTHER = 'Other'
    
    # File saving error messages
    WRITE_ERROR_TITLE = "File Write Error"
    WRITE_ERROR_TEXT = "Failed to save the file. Check disk space and permissions."
    
    # DZN file validation messages
    BLOCK = "BLOCK"
    WARN  = "WARN"
    
    # MiniZinc exit codes
    MINIZINC_EXIT_CODE_HINTS = {
        1: "MiniZinc reported an error while parsing or solving the model.",
        2: "No solution exists for the current model and input data.",
        4: "Search finished without a conclusive result (often timeout or interrupted search).",
        5: "The model appears to be unbounded.",
        255: "MiniZinc or the solver ran out of memory."
    }


class WindowConfig:
    """Window positioning and titles."""
    # Window titles
    TITLE_MAIN = "MPLACE"
    TITLE_DZN_GENERATOR = "Generate *.dzn file"
    TITLE_VISUALIZER = "Layout Visualization"
    
    # Window positions (x, y offsets)
    DZN_WINDOW_X = 30
    DZN_WINDOW_Y = 30
    VIZ_WINDOW_X = 10
    VIZ_WINDOW_Y = 10


class MaterialDefaults:
    """Default material configurations for DZN generation."""
    # Default compound dictionary
    DEFAULT_DRUGS = "{'Drug1': [5,'0.1', '0.3'], 'Drug2': [5, '1']}"
    
    # Default control dictionary  
    DEFAULT_CONTROLS = "{'pos': [10, '100']}"


class FileTypes:
    """File type constants for dialogs."""
    DZN_FILES = [('dzn file', '*.dzn')]
    CSV_FILES = [('csv file', '*.csv')]
    PDF_FILES = [('pdf file', '*.pdf')]
    PNG_FILES = [('png file', '*.png')]
    FIG_FILES = [('png file', '*.png'),('pdf file', '*.pdf')]
    PHARMBIO_LABEL = 'CSV (PharmBio) - default MPLACE format'
    PLATER_LABEL = 'CSV (PLATER) - plate-shaped format for R package'
    CSV_PLATER = 'plater'
    PHARMBIO = 'pharmbio'
    PLATER = 'plater'
    PDF_LABEL = '*.PDF (all layouts in one file)'
    PNG_LABEL = '*.PNG (one layout per file)'
    CSV = 'csv'
    PDF = 'pdf'
    PNG = 'png'

class PlaterFormat:
    """String constants for saving and reading Plater files."""
    DRUGS_LABEL = "Drug"
    CONCENTRATIONS_LABEL = "Concentration"

class FigureProperties:
    """DPI and scaling constants for figure rendering and export."""
    DPI = 300           # DPI for saving layouts to file
    DPI_DISPLAY = 105   # Reference DPI for on-screen display (original design target)
    DPI_MPL_DEFAULT = 100  # Default DPI when matplotlib creates a figure
    # Scale factor to convert between display DPI and matplotlib default DPI:
    DPI_RATIO = DPI_DISPLAY / DPI_MPL_DEFAULT

class Validation:
    """Input validation constants."""
    MATERIAL_NAME_MAX_LENGTH = 100
    PATH_DISPLAY_MAX_LENGTH = 20
    RECENT_PATH_DISPLAY_MAX_LENGTH = 80
    PATH_TRUNCATION_PREFIX = '...'

class System:
    """System-related constants."""
    # Platform detection
    WINDOWS_PLATFORM_PREFIX = 'win'
    
    # Encoding
    WINDOWS_CODEPAGE_UTF8 = 'chcp 65001'
    
    # Time delays
    UI_UPDATE_DELAY = 0  # seconds

class RecentFiles:
    """Recent files configuration"""
    MAX_RECENT = 7
    RECENT_DZN_PATH = os.path.join(os.path.expanduser("~"), ".mplace_recent_dzn.json")
    RECENT_CSV_PATH = os.path.join(os.path.expanduser("~"), ".mplace_recent_csv.json")
    