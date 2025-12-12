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
# Description: Constants for the MPLACE application
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.1
# Last Revision: November 2025
#


"""
Constants module for MPLACE application.

This module centralizes all magic numbers, default values, and string constants
used throughout the application to improve maintainability and consistency.
"""

from typing import List


class PlateDefaults:
    """Default values for microplate configurations."""
    ROWS = '16'
    COLS = '24'
    EMPTY_EDGE_SIZE = '0'
    CORNER_EMPTY_WELLS = '0'
    CELL_LINES = '1'
    CONTROL_NAMES = '[]'
    
    # Numeric versions for calculations
    ROWS_INT = 16
    COLS_INT = 24


class UI:
    """User interface layout constants."""
    # Widget dimensions
    BUTTON_WIDTH = 13
    BUTTON_WIDTH_STANDARD = 13
    ENTRY_WIDTH_NUMERIC = 6
    ENTRY_WIDTH_MATERIALS = 33
    
    # Padding and spacing
    PADDING_FRAME = 10
    PADDING_LABELFRAME = 10
    PADDING_BETWEEN_FRAMES = 5
    PADDING_BUTTON = 5
    PADDING_LABEL = 5
    PADDING_RADIOBUTTON = 10
    
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
    # Constants for coordinate transformation
    LETTERS_CAPITAL: List[str] = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K",
                                  "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    LETTERS_LOWERCASE: List[str] = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
                                    "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]


class Visualization:
    """Constants for visualization components."""
    # Panel dimensions
    MATERIAL_PANEL_WIDTH = 400
    MATERIAL_PANEL_HEIGHT = 500
    
    # Plot settings
    WELL_COORDINATE_OFFSET = 0.5
    SCATTER_MARKER_SIZE = 80
    
    # Figure dimensions
    SCALE_FIGURE_WIDTH = 4
    SCALE_FIGURE_HEIGHT = 2
    
    # Alpha transparency range
    ALPHA_MIN = 0.3
    ALPHA_MAX = 1.0


class Performance:
    """Performance-related constants."""
    COORDINATE_CACHE_SIZE = 2048
    COLORMAP_COLOR_LIMIT = 20


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
    NO_FILE_LOADED = 'No file is loaded'
    LOAD_DZN_FIRST = 'Load DZN file first'
    NO_DZN_LOADED = 'No *.dzn file is loaded'
    NO_CSV_LOADED = 'No *.csv file is loaded'
    
    # Dialog titles and labels
    FRAME_TITLE_DZN = 'Step 1 - Generate OR load the *.dzn file:'
    FRAME_TITLE_MODEL = 'Step 2 - Run model'
    FRAME_TITLE_CSV = 'Step 3 - Generate OR load the layout (*.csv):'
    FRAME_TITLE_VIZ = 'Step 4 - Visualize the layout (*.csv):'
    
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


class WindowConfig:
    """Window positioning and titles."""
    # Window titles
    TITLE_MAIN = "MPLACE"
    TITLE_DZN_GENERATOR = "Generate *.dzn file"
    TITLE_VISUALIZER = "Visualize GUI"
    
    # Window geometry
    GEOMETRY_MAIN = "400x400"
    
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
    PHARMBIO_LABEL = 'CSV (PharmBio)'
    PLATER_LABEL = 'CSV (PLATER)'
    CSV = 'pharmbio'
    CSV_PLATER = 'plater'
    PHARMBIO = 'pharmbio'
    PLATER = 'plater'
    PDF_LABEL = '*.PDF (all layouts in one file)'
    PNG_LABEL = '*.PNG (one layout per file)'
    PDF = 'pdf'
    PNG = 'png'

class PlaterFormat:
    """String constants for saving and reading Plater files."""
    DRUGS_LABEL = "Drug"
    CONCENTRATIONS_LABEL = "Concentration"

class FigureProperties:
    DPI = 300

class Validation:
    """Input validation constants."""
    MATERIAL_NAME_MAX_LENGTH = 100
    PATH_DISPLAY_MAX_LENGTH = 20
    PATH_TRUNCATION_PREFIX = '...'


class System:
    """System-related constants."""
    # Platform detection
    WINDOWS_PLATFORM_PREFIX = 'win'
    
    # Encoding
    WINDOWS_CODEPAGE_UTF8 = 'chcp 65001'
    
    # Time delays
    UI_UPDATE_DELAY = 0  # seconds