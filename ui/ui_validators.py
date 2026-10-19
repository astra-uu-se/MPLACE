# Copyright 2025 Ramiz Gindullin.
#
# Licensed under the CC0 license.
#
#
# Description:  Numeric input validation callback
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.0
# Last Revision: October 2025
#

import tkinter as tk


def numeric_entry_callback(P: str) -> bool:
    """Validation callback for numeric input.
    
    Args:
        P: Input string to validate
        
    Returns:
        True if input is valid (digits or empty), False otherwise
    """
    return str.isdigit(P) or P == ""