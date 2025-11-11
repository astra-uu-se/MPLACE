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
# Description:  A window where the user can select in which format to save the layout
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.1
# Last Revision: November 2025
#

import logging
import tkinter as tk

from typing import List, Tuple

from models.constants import FileTypes


# Configure logging for utility module
logger = logging.getLogger(__name__)


def ask_layout_export_format(parent, file_formats: List[Tuple[str, str]] = []) -> str:
    '''Create a window where the user selects the desired format
    
    Args:
        The list of possible file-formats
    
    Returns:
        Selected file-format flag
    '''
    if not file_formats:
        logger.debug(f"No file format is supplied for the file format selection window")
        return
    
    dialog = tk.Toplevel(parent)
    dialog.title("Export Format")
    dialog.grab_set()
    
    tk.Label(dialog, text="Choose export format for the layout file:").pack(padx = 10, pady=5)
    
    default_value, _ = file_formats[0]
    var = tk.StringVar(dialog, value = default_value)
    
    for (format_type, format_label) in file_formats:
        tk.Radiobutton(dialog, text=format_label, variable=var, value=format_type).pack(pady = 5)
    
    result = None
    
    def ok():
        nonlocal result
        result = var.get()
        dialog.destroy()
    
    tk.Button(dialog, text="OK", command=ok).pack(pady=10)
    dialog.wait_window()
    
    return result
