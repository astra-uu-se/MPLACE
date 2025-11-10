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
# Version: 1.0
# Last Revision: October 2025
#


import tkinter as tk

from models.constants import FileTypes


def ask_layout_export_format(parent) -> str:
    '''Create a window where the user selects the desired format
    
    Returns:
        Selected file-format flag
    '''
    dialog = tk.Toplevel(parent)
    dialog.title("Export Format")
    dialog.grab_set()
    
    tk.Label(dialog, text="Choose export format for the layout file:").pack(padx = 10, pady=5)
    
    var = tk.StringVar(dialog, value = FileTypes.PHARMBIO)
    
    tk.Radiobutton(dialog, text=FileTypes.PHARMBIO_LABEL, variable=var, value=FileTypes.PHARMBIO).pack(pady = 5)
    tk.Radiobutton(dialog, text=FileTypes.PLATER_LABEL, variable=var, value=FileTypes.PLATER).pack(pady = 5)
    
    result = None
    
    def ok():
        nonlocal result
        result = var.get()
        dialog.destroy()
    
    tk.Button(dialog, text="OK", command=ok).pack(pady=10)
    dialog.wait_window()
    
    return result
