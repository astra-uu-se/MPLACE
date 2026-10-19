# Copyright 2025 Ramiz Gindullin.
#
# Licensed under the CC0 license.
#
#
# Description:  Tooltip widget
#
# Authors: squareRoot17
# Version: 1.0
# Last Revision: October 2025
#

import tkinter as tk

class ToolTip(object):
    """Tooltip widget for displaying help text on hover.
    
    Source: squareRoot17, https://stackoverflow.com/questions/20399243/display-message-when-hovering-over-something-with-mouse-cursor-in-python
    """
    
    def __init__(self, widget: tk.Widget) -> None:
        """Initialize tooltip for widget.
        
        Args:
            widget: Tkinter widget to attach tooltip to
        """
        self.widget = widget
        self.tipwindow: tk.Toplevel = None
        self.id: str = None
        self.x: int = 0
        self.y: int = 0

    def showtip(self, text: str) -> None:
        """Display text in tooltip window.
        
        Args:
            text: Text to display in tooltip
        """
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 5
        y = y + cy + self.widget.winfo_rooty() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", fg="black", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "12", "normal"))
        label.pack(ipadx=1)

    def hidetip(self) -> None:
        """Hide the tooltip window."""
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


def CreateToolTip(widget: tk.Widget, text: str) -> None:
    """Create a tooltip for the given widget.
    
    Args:
        widget: Tkinter widget to attach tooltip to
        text: Help text to display on hover
    """
    toolTip = ToolTip(widget)

    def enter(event):
        toolTip.showtip(text)

    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)