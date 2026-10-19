# Copyright 2026 Ramiz Gindullin.
#
# Licensed under the CC0 license.
#
#
# Description:  Utilities related to UI manipulations that can be used with multiple views
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.6
# Last Revision: June 2026
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