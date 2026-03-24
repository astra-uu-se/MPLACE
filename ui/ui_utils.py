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
# Description:  Utilities related to UI manipulations that can be used with multiple views
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.3
# Last Revision: March 2026
#

import logging
import tkinter as tk

from core.io_utils import path_truncate
logger = logging.getLogger(__name__)


def path_show(path: str, label_object: tk.Label) -> None:
    """Display truncated path in label widget.
    
    Args:
        path: File path to display
        label_object: Tkinter label widget to update
    """
    display_text = 'File loaded: ' + path_truncate(path)
    label_object.config(text=display_text)
    logger.debug(f"UI updated with path: {display_text}")