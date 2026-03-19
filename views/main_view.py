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
# Description:  Main window view for MPLACE application.
# Pure view layer - handles only UI display and user input.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.3
# Last Revision: March 2026
#

import logging
import os
import time
import queue
import threading
from typing import Callable, Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from controllers.main_controller import MainController
from controllers.minizinc_controller import MiniZincController
from controllers.csv_controller import CsvController
from models.constants import PlateDefaults, MainMenu, UI, Messages, WindowConfig, FileTypes, PathsIni, Validation
from ui.ui_utils import path_show
from ui.ui_validators import numeric_entry_callback
from ui.layout_format_dialog import ask_layout_export_format        

logger = logging.getLogger(__name__)

class MainView:
    """Main application window - pure view layer matching original."""
    
    def __init__(
        self,
        root: tk.Tk,
        controller: MainController,
        minizinc_controller: MiniZincController,
        csv_controller: CsvController,
        on_generate_dzn_clicked: Callable[[], None],
        on_visualize_clicked: Callable[[], None]
    ):
        """Initialize main view matching original layout."""
        logger.info("Initializing main view")
        
        self.root = root
        self.controller = controller
        self.minizinc_controller = minizinc_controller
        self.csv_controller = csv_controller
        self.on_generate_dzn_clicked = on_generate_dzn_clicked
        self.on_visualize_clicked = on_visualize_clicked
        
        self._init_variables()
        self._build_ui()
        
        self._shortcuts = [
            # (menu,  label,              key_event,     accelerator, handler,                                 guard)
            ("file",  MainMenu.LOAD_DZN,  "<Control-d>", "Ctrl+D",    self._on_load_dzn,                       None),
            ("file",  MainMenu.LOAD_CSV,  "<Control-f>", "Ctrl+F",    self._on_load_csv,                       None),
            ("tools", MainMenu.GEN_DZN,   "<Control-g>", "Ctrl+G",    self._on_generate_dzn,                   None),
            ("tools", MainMenu.RUN_MZN,   "<Control-r>", "Ctrl+R",    self._on_run_minizinc,                   self.button_run_minizinc),
            ("tools", MainMenu.VISUALIZE, "<Control-l>", "Ctrl+L",    self._on_visualize,                      self.button_visualize),
            ("tools", MainMenu.RESET,     "<Control-e>", "Ctrl+E",    self._set_program_state_to_default_call, None),
        ]
                
        self._setup_window()
        self._setup_shortcuts()
        self._setup_menu()
        self._refresh_recent_menus()
        self._set_program_state_to_default()
        
        self.root.focus_force()
        
        logger.info("Main view initialized")
    
    def _setup_window(self) -> None:
        """Configure main window."""
        self.root.title(WindowConfig.TITLE_MAIN)
        self.root.resizable(False, False)
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
    
    def _init_variables(self) -> None:
        """Initialize all Tkinter variables."""
        self.dzn_file_path = tk.StringVar(self.root)
        self.csv_file_path = tk.StringVar(self.root)
        self.num_rows = tk.StringVar(self.root)
        self.num_cols = tk.StringVar(self.root)
        self.control_names = tk.StringVar(self.root)
        self.use_compd_flag = tk.BooleanVar(self.root)
        self.vcmd = (self.root.register(numeric_entry_callback))
        self._mzn_queue: queue.Queue = queue.Queue()
        self._mzn_timer_active: bool = False
        self._mzn_start: float = 0.0
    
    def _build_ui(self) -> None:
        """Build UI matching original exactly."""
        # Frame 1: DZN file generation/loading
        self.frame_dzn = ttk.LabelFrame(self.root, text=Messages.FRAME_TITLE_DZN)
        self.frame_dzn.pack(expand=True, fill="both", padx=UI.FRAME_PADDING, pady=UI.FRAME_PADDING)
        
        self.button_generate_dzn = ttk.Button(
            self.frame_dzn, width=UI.BUTTON_WIDTH_STANDARD, state=tk.NORMAL,
            text=Messages.BUTTON_GENERATE_DZN, command=self._on_generate_dzn
        )
        self.button_load_dzn = ttk.Button(
            self.frame_dzn, width=UI.BUTTON_WIDTH_STANDARD, state=tk.NORMAL,
            text=Messages.BUTTON_LOAD_DZN, command=self._on_load_dzn
        )
        self.label_dzn_loaded = tk.Label(self.frame_dzn, text=Messages.NO_DZN_LOADED)
        
        self.frame_dzn.columnconfigure(0, weight=UI.GRID_WEIGHT)
        self.frame_dzn.columnconfigure(1, weight=UI.GRID_WEIGHT)
        
        self.button_generate_dzn.grid(row=0, column=0, columnspan=1, sticky="ew")
        self.button_load_dzn.grid(row=0, column=1, columnspan=1, sticky="ew")
        self.label_dzn_loaded.grid(row=1, column=0, columnspan=2, sticky="w")
        
        # Frame 2: CSV file generation/loading
        self.frame_csv = ttk.LabelFrame(self.root, text=Messages.FRAME_TITLE_CSV)
        self.frame_csv.pack(expand=True, fill="both", padx=UI.FRAME_PADDING, pady=UI.FRAME_PADDING)
        
        self.radio_plaid = ttk.Radiobutton(
            self.frame_csv, text=Messages.MODEL_PLAID, value=UI.SELECT_PLAID, variable=self.use_compd_flag
        )
        self.radio_compd = ttk.Radiobutton(
            self.frame_csv, text=Messages.MODEL_COMPD, value=UI.SELECT_COMPD, variable=self.use_compd_flag
        )
        self.button_run_minizinc = ttk.Button(
            self.frame_csv, width=UI.BUTTON_WIDTH_STANDARD, state=tk.DISABLED,
            text=Messages.BUTTON_RUN_MODEL, command=self._on_run_minizinc
        )
        self.button_load_csv = ttk.Button(
            self.frame_csv, width=UI.BUTTON_WIDTH_STANDARD, state=tk.NORMAL,
            text=Messages.BUTTON_LOAD_CSV, command=self._on_load_csv
        )
        self.label_csv_loaded = tk.Label(self.frame_csv, text=Messages.NO_CSV_LOADED)
        
        self.frame_csv.columnconfigure(0, weight=UI.GRID_WEIGHT)
        self.frame_csv.columnconfigure(1, weight=UI.GRID_WEIGHT)
        
        self.radio_plaid.grid(row=0, column=0, columnspan=1, sticky="")
        self.radio_compd.grid(row=0, column=1, columnspan=1, sticky="")
        self.button_run_minizinc.grid(row=1, column=0, columnspan=1, sticky="ew")
        self.button_load_csv.grid(row=1, column=1, columnspan=1, sticky="ew")
        self.label_csv_loaded.grid(row=2, column=0, columnspan=2, sticky="w")
               
        # Frame 3: Visualization
        self.frame_matplotlib = ttk.LabelFrame(self.root, text=Messages.FRAME_TITLE_VIZ)
        self.frame_matplotlib.pack(expand=True, fill="both", padx=UI.FRAME_PADDING, pady=UI.FRAME_PADDING)
        
        self.label_rows = tk.Label(self.frame_matplotlib, text=Messages.LABEL_ROWS)
        self.entry_rows = ttk.Entry(
            self.frame_matplotlib, textvariable=self.num_rows, width=UI.ENTRY_WIDTH_NUMERIC,
            validate='all', validatecommand=(self.vcmd, '%P')
        )
        self.label_cols = tk.Label(self.frame_matplotlib, text=Messages.LABEL_COLS)
        self.entry_cols = ttk.Entry(
            self.frame_matplotlib, textvariable=self.num_cols, width=UI.ENTRY_WIDTH_NUMERIC,
            validate='all', validatecommand=(self.vcmd, '%P')
        )
        self.button_visualize = ttk.Button(
            self.frame_matplotlib, width=UI.BUTTON_WIDTH_STANDARD, state=tk.DISABLED,
            text=Messages.BUTTON_VISUALIZE, command=self._on_visualize
        )
        self.button_set_program_state_to_default = ttk.Button(
            self.frame_matplotlib, width=UI.BUTTON_WIDTH_STANDARD,
            text=Messages.BUTTON_RESET, command=self._set_program_state_to_default_call
        )
        
        self.frame_matplotlib.columnconfigure(0, weight=UI.GRID_WEIGHT)
        self.frame_matplotlib.columnconfigure(1, weight=UI.GRID_WEIGHT)
        self.frame_matplotlib.columnconfigure(2, weight=UI.GRID_WEIGHT)
        self.frame_matplotlib.columnconfigure(3, weight=UI.GRID_WEIGHT)
        
        self.label_rows.grid(row=0, column=0, columnspan=1, sticky="w")
        self.entry_rows.grid(row=0, column=1, columnspan=1, sticky="w")
        self.label_cols.grid(row=0, column=2, columnspan=1, sticky="w")
        self.entry_cols.grid(row=0, column=3, columnspan=1, sticky="w")
        self.button_visualize.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.button_set_program_state_to_default.grid(row=1, column=2, columnspan=2, sticky="ew")
    
    def _apply_config_defaults(self) -> None:
        """
        Apply configuration constraints based on available resources.

        This method:
        - Disables radio buttons for unavailable models
        - Updates Run Model button state based on config
        - Auto-selects a valid model if current selection is unavailable

        Called from:
        - _set_program_state_to_default() to reapply after clearing state
        """
        logger.info("Applying config defaults")

        # Determine what resources are available
        minizinc_available = (
            self.controller.app_config.minizinc_path != PathsIni.FILE_ERROR_PLACEHOLDER
        )
        plaid_available = (
            self.controller.app_config.plaid_path != PathsIni.FILE_ERROR_PLACEHOLDER
        )
        compd_available = (
            self.controller.app_config.compd_path != PathsIni.FILE_ERROR_PLACEHOLDER
        )

        # 1) Disable radio buttons based on availability
        if not minizinc_available:
            # If MiniZinc missing, both models are unavailable
            self.radio_plaid.config(state=tk.DISABLED)
            self.radio_compd.config(state=tk.DISABLED)
            logger.warning("Both radio buttons disabled - MiniZinc unavailable")
        else:
            # MiniZinc available – disable individual models as needed
            self.radio_plaid.config(
                state=tk.NORMAL if plaid_available else tk.DISABLED
            )
            self.radio_compd.config(
                state=tk.NORMAL if compd_available else tk.DISABLED
            )

            if not plaid_available:
                logger.warning("PLAID radio button disabled - PLAID model unavailable")
            if not compd_available:
                logger.warning("COMPD radio button disabled - COMPD model unavailable")

        # 2) Auto-select a valid model (based on config, not widget state)
        current_selection = self.use_compd_flag.get()  # True/False boolean

        if current_selection == UI.SELECT_COMPD and not compd_available:
            # COMPD selected but unavailable -> fall back to PLAID if possible
            if plaid_available:
                self.use_compd_flag.set(UI.SELECT_PLAID)
                logger.info("Auto-selected PLAID model (COMPD unavailable)")
            else:
                # Neither model available; default to PLAID just for consistency
                self.use_compd_flag.set(UI.SELECT_PLAID)
                logger.warning("Neither PLAID nor COMPD available")

        elif current_selection == UI.SELECT_PLAID and not plaid_available:
            # PLAID selected but unavailable -> fall back to COMPD if possible
            if compd_available:
                self.use_compd_flag.set(UI.SELECT_COMPD)
                logger.info("Auto-selected COMPD model (PLAID unavailable)")
            else:
                self.use_compd_flag.set(UI.SELECT_COMPD)
                logger.warning("Neither PLAID nor COMPD available")

        # 3) Update Run Model button state based on config
        self._update_run_minizinc_button_state()
    
    def _setup_menu(self) -> None:
        """Setup menu bar, deriving entries from self._shortcuts."""
        self.menu_bar = tk.Menu(self.root)

        self.menu_file  = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_tools = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_recent_dzn = tk.Menu(self.menu_file, tearoff=0)
        self.menu_recent_csv = tk.Menu(self.menu_file, tearoff=0)

        menus = {"file": self.menu_file, "tools": self.menu_tools}

        for menu_key, label, _, accelerator, handler, _ in self._shortcuts:
            menus[menu_key].add_command(
                label=label, accelerator=accelerator, command=handler
            )
            # Insert the Recent submenus after the Load CSV entry
            if label == MainMenu.LOAD_CSV:
                self.menu_file.add_separator()
                self.menu_file.add_cascade(label=MainMenu.RCNT_DZN, menu=self.menu_recent_dzn)
                self.menu_file.add_cascade(label=MainMenu.RCNT_CSV, menu=self.menu_recent_csv)
            elif label == MainMenu.RUN_MZN:
                self.menu_tools.add_separator()  # separator before Visualize

        self.menu_bar.add_cascade(label="File",  menu=self.menu_file)
        self.menu_bar.add_cascade(label="Tools", menu=self.menu_tools)
        self.root.config(menu=self.menu_bar)
    
    def _setup_shortcuts(self) -> None:
        """Bind keyboard shortcuts, deriving bindings from self._shortcuts."""
        for _, _, key_event, _, handler, guard in self._shortcuts:
            if guard is not None:
                self.root.bind(key_event,
                    lambda e, h=handler, g=guard: h() if not g.instate(['disabled']) else None)
            else:
                self.root.bind(key_event, lambda e, h=handler: h())
        logger.debug("Keyboard shortcuts registered")    
    
    def _on_generate_dzn(self) -> None:
        """Handle Generate DZN button click."""
        logger.debug("Generate DZN button clicked")
        self.on_generate_dzn_clicked()
    
    def _update_run_minizinc_button_state(self) -> None:
        """
        Update Run Model button state based on config constraints.

        Button is ENABLED when:
        - MiniZinc is available AND
        - (PLAID OR COMPD is available)

        Button is DISABLED when:
        - MiniZinc is missing OR
        - Both PLAID and COMPD are missing
        """
        # Check what resources are available
        minizinc_available = (
            self.controller.app_config.minizinc_path != PathsIni.FILE_ERROR_PLACEHOLDER
        )
        plaid_available = (
            self.controller.app_config.plaid_path != PathsIni.FILE_ERROR_PLACEHOLDER
        )
        compd_available = (
            self.controller.app_config.compd_path != PathsIni.FILE_ERROR_PLACEHOLDER
        )
        dzn_loaded = bool(self.dzn_file_path.get())

        # Button enabled if MiniZinc present AND at least one model available
        button_should_be_enabled = (
            minizinc_available and (plaid_available or compd_available) and dzn_loaded
        )

        new_state = tk.NORMAL if button_should_be_enabled else tk.DISABLED
        self.button_run_minizinc.config(state=new_state)
        self.menu_tools.entryconfig(MainMenu.RUN_MZN, state=new_state)

        if button_should_be_enabled:
            logger.debug("Run Model button enabled - config valid")
        else:
            logger.debug("Run Model button disabled - invalid config")
    
    
    def _on_load_dzn(self) -> None:
        """Handle Load DZN button click."""
        path = filedialog.askopenfilename(title='Open DZN file', filetypes=FileTypes.DZN_FILES)
        if path:
            try:
                path_show(path, self.label_dzn_loaded)
                self.dzn_file_path.set(path)
                cols, rows, controls = self.controller.parse_dzn_file(path)
                self.num_cols.set(cols)
                self.num_rows.set(rows)
                self.control_names.set(controls)
                logger.info(f"DZN file loaded successfully: {path}, {rows}x{cols} plate, controls: {controls}")
                self._update_run_minizinc_button_state()
                self._add_to_recent(path, is_dzn=True)
            except Exception as e:
                logger.error(f"DZN loading failed: {path}, error: {e}")
                messagebox.showerror("Error", f"Failed to load DZN file: {str(e)}")
        self.root.focus_force()
                               
    def _on_run_minizinc(self) -> None:
        """Handle Run Model button click."""
        original_text = self.label_csv_loaded.cget("text")
        model_name = Messages.MODEL_COMPD if self.use_compd_flag.get() else Messages.MODEL_PLAID
        dzn_path = self.dzn_file_path.get()
        use_compd = self.use_compd_flag.get()
        timeout = self.minizinc_controller.get_timeout(use_compd)
        logger.info(f"Running {model_name} model...")

        self.lock()
        self._mzn_start = time.monotonic()
        self._mzn_timer_active = True
        self._tick_timer(timeout)
        self._mzn_queue = queue.Queue()

        def worker():
            try:
                # Run model through MiniZincController
                if use_compd:
                    output = self.minizinc_controller.run_compd_model(dzn_path)
                else:
                    output = self.minizinc_controller.run_plaid_model(dzn_path)
                self._mzn_queue.put(("ok", output))
            except Exception as e:
                self._mzn_queue.put(("err", e))

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(100, lambda: self._poll_mzn_result(model_name, dzn_path, original_text))

    def _tick_timer(self, timeout_s: Optional[int]) -> None:
        """Update the status label with elapsed time every second."""
        if not self._mzn_timer_active:
            return
        elapsed = int(time.monotonic() - self._mzn_start)
        if timeout_s is not None:
            self.label_csv_loaded.config(text=f"Running MiniZinc: {elapsed}s / {timeout_s}s")
        else:
            self.label_csv_loaded.config(text=f"Running MiniZinc: {elapsed}s")
        self.root.after(1000, lambda: self._tick_timer(timeout_s))

    def _poll_mzn_result(self, model_name: str, dzn_path: str, original_text: str) -> None:
        """Poll the result queue; when ready, handle export on the main thread."""
        try:
            status, payload = self._mzn_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, lambda: self._poll_mzn_result(model_name, dzn_path, original_text))
            return

        # MiniZinc finished — stop the timer
        self._mzn_timer_active = False

        if status == "err":
            self.label_csv_loaded.config(text=original_text)
            logger.error(f"MiniZinc execution failed: {payload}")
            messagebox.showerror("Model Execution Error",
                                 f"Failed to run {model_name} model.\n\n{str(payload)}")
            self.unlock()
            self.root.focus_force()
            return

        # status == "ok" — proceed with CSV extraction and export (main thread only)
        try:
            csv_lines = self.minizinc_controller.extract_csv_from_output(payload)

            # Generate suggested filename from DZN path
            dzn_basename = os.path.basename(dzn_path)
            suggested_csv_name = os.path.splitext(dzn_basename)[0] + '.csv'

            # Ask user for CSV format
            file_formats = [
                (FileTypes.CSV,        FileTypes.PHARMBIO_LABEL),
                (FileTypes.CSV_PLATER, FileTypes.PLATER_LABEL)
            ]
            
            chosen_format = ask_layout_export_format(self.root, file_formats)
            
            if not chosen_format:
                self.label_csv_loaded.config(text=original_text)
                messagebox.showwarning("Warning", "Model ran successfully, the user cancelled CSV save")
                logger.info("User cancelled format selection")
                self.unlock()
                self.root.focus_force()
                return
        
            # Save in chosen format
            csv_path = None
            if chosen_format == FileTypes.CSV_PLATER:
                # PLATER format
                rows = self.num_rows.get()
                cols = self.num_cols.get()
                csv_path = self.csv_controller.export_plater(csv_lines[1:], rows, cols)
            else:
                # PharmBio format (default) - pass suggested filename
                csv_path = self.csv_controller.export_pharmbio(csv_lines, suggested_csv_name)
        
            # Check if csv_path is valid
            if csv_path:
                if isinstance(csv_path, str):
                    self._load_csv_into_ui(csv_path)
                    self._add_to_recent(csv_path, is_dzn=False)
                    logger.info(f"MiniZinc execution completed: {os.path.basename(csv_path)}")
                else:
                    self._load_csv_into_ui(csv_path[0])
                    for path in csv_path:
                        self._add_to_recent(path, is_dzn=False)
                    logger.info(f"MiniZinc execution completed: {[os.path.basename(path) for path in csv_path]}")
            else:
                self.label_csv_loaded.config(text=original_text)
                messagebox.showwarning("Warning", "Model ran successfully, the user cancelled CSV save")
                logger.info("User cancelled CSV save")
            
        except Exception as e:
            self.label_csv_loaded.config(text="Export failed after successful model run")
            logger.error(f"CSV export failed after successful model run: {e}")
            messagebox.showerror("Export Error",
                                 f"Model ran successfully but export failed.\n\n{str(e)}")
        
        finally:
            self.unlock()
            self.root.focus_force()
    
    def _on_load_csv(self) -> None:
        """Handle Load CSV button click."""
        path = filedialog.askopenfilename(title='Open CSV file', filetypes=FileTypes.CSV_FILES)
        if path:
            try:
                # Only update UI after successful load
                self._load_csv_into_ui(path)
                self._add_to_recent(path, is_dzn=False)
            except Exception as e:
                logger.error(f"CSV loading failed: {path}, error: {e}")
                messagebox.showerror("Error", f"Failed to load CSV file: {str(e)}")
        self.root.focus_force()
    
    def _on_visualize(self) -> None:
        """Handle Visualize button click."""
        logger.debug("Visualize button clicked")
        self.controller.state.num_rows = self.num_rows.get()
        self.controller.state.num_cols = self.num_cols.get()
        self.controller.state.control_names = self.control_names.get()
        self.on_visualize_clicked()
    
    def _on_close(self) -> None:
        """Handle window close."""
        logger.info("Application shutdown initiated")
        self.root.destroy()
    
    def _add_to_recent(self, path: str, is_dzn: bool) -> None:
        """Add file to recent list."""
        if is_dzn:
            self.controller.state.add_recent_dzn(path)
        else:
            self.controller.state.add_recent_csv(path)
        self._refresh_recent_menus()
    
    def _open_recent_file(self, path: str, is_dzn: bool) -> None:
        """Load recent file."""
        if not os.path.exists(path):
            messagebox.showerror("File Not Found", f"Could not find file:\n{path}\n\nThe entry will be removed from menu.")
            if is_dzn:
                self.controller.state.remove_recent_dzn(path)
            else:
                self.controller.state.remove_recent_csv(path)
            self._refresh_recent_menus()
            self.root.focus_force()
            return
        if is_dzn:
            self.dzn_file_path.set(path)
            path_show(path, self.label_dzn_loaded)
            try:
                cols, rows, controls = self.controller.parse_dzn_file(path)
                self.num_cols.set(cols)
                self.num_rows.set(rows)
                self.control_names.set(controls)
            except Exception as e:
                logger.error(f"Failed to parse DZN from recent: {e}")
                messagebox.showerror("Error", f"Failed to parse DZN file:\n{path}\n\n{str(e)}")
                self.dzn_file_path.set('')
                self.label_dzn_loaded.config(text=Messages.NO_DZN_LOADED)
                self._update_run_minizinc_button_state()
                self.root.focus_force()
                return
            self._update_run_minizinc_button_state()
        else:
            self._load_csv_into_ui(path)
        self.root.focus_force()
    
    def _refresh_recent_menus(self) -> None:
        """Refresh both recent file menus."""
        recent_dzn = self.controller.state.recent_dzn
        recent_csv = self.controller.state.recent_csv
        
        self.menu_recent_dzn.delete(0, tk.END)
        
        if not recent_dzn:
            self.menu_recent_dzn.add_command(label="(No recent DZN)", state=tk.DISABLED)
        else:
            for fpath in recent_dzn:
                display = fpath if len(fpath) <= Validation.RECENT_PATH_DISPLAY_MAX_LENGTH else "..." + fpath[-Validation.RECENT_PATH_DISPLAY_MAX_LENGTH:]
                self.menu_recent_dzn.add_command(label=display, command=lambda p=fpath: self._open_recent_file(p, True))
            self.menu_recent_dzn.add_separator()
            self.menu_recent_dzn.add_command(label="Clear List", command=lambda: self._clear_recent(True))
        
        self.menu_recent_csv.delete(0, tk.END)
        if not recent_csv:
            self.menu_recent_csv.add_command(label="(No recent CSV)", state=tk.DISABLED)
        else:
            for fpath in recent_csv:
                display = fpath if len(fpath) <= Validation.RECENT_PATH_DISPLAY_MAX_LENGTH else "..." + fpath[-Validation.RECENT_PATH_DISPLAY_MAX_LENGTH:]
                self.menu_recent_csv.add_command(label=display, command=lambda p=fpath: self._open_recent_file(p, False))
            self.menu_recent_csv.add_separator()
            self.menu_recent_csv.add_command(label="Clear List", command=lambda: self._clear_recent(False))
    
    def _clear_recent(self, is_dzn: bool) -> None:
        """Clear recent files list."""
        if messagebox.askyesno("Clear Recent Files", "Remove all entries from this menu?"):
            if is_dzn:
                self.controller.state.clear_recent_dzn()
            else:
                self.controller.state.clear_recent_csv()
            self._refresh_recent_menus()
    
    def _load_csv_into_ui(self, path: str) -> None:
        """Update CSV path and enable visualize button."""
        if not path:
            raise ValueError("CSV path cannot be empty")
        self.controller.load_csv_file(path)
        path_show(path, self.label_csv_loaded)
        self.csv_file_path.set(path)
        self.button_visualize.config(state=tk.NORMAL)
        self.menu_tools.entryconfig(MainMenu.VISUALIZE, state=tk.NORMAL)
    
        logger.info(f"CSV path updated: {path}")
    
    def update_after_dzn_generation(self, file_path: str, rows: str, cols: str, controls: str) -> None:
        """Update UI after DZN generation completes."""
        self.dzn_file_path.set(file_path)
        self.num_rows.set(rows)
        self.num_cols.set(cols)
        self.control_names.set(controls)
        path_show(file_path, self.label_dzn_loaded)
        self._add_to_recent(file_path, is_dzn=True)
        self._update_run_minizinc_button_state()
        logger.info(f"DZN file generated, {file_path}: {rows}x{cols} plate, controls: {controls}")
    
    def _set_program_state_to_default_call(self) -> None:
        """Calls to reset all form fields to defaults."""
        if messagebox.askyesno("Reset", "This will clear the loaded DZN/CSV files and reset all parameters. Continue?"):
            self._set_program_state_to_default()
    
    def _set_program_state_to_default(self) -> None:
        """Reset all form fields to defaults."""
        
        self.controller.state.reset()
        
        # Clear loaded files
        self.dzn_file_path.set('')
        self.csv_file_path.set('')
        
        # Reset parameters to defaults
        self.num_rows.set(PlateDefaults.ROWS)
        self.num_cols.set(PlateDefaults.COLS)
        self.control_names.set(PlateDefaults.CONTROL_NAMES)
        
        # Reset UI labels
        self.label_dzn_loaded.config(text=Messages.NO_DZN_LOADED)
        self.label_csv_loaded.config(text=Messages.NO_CSV_LOADED)
        
        # Disable visualization button (no CSV loaded)
        self.button_visualize.config(state=tk.DISABLED)
        self.menu_tools.entryconfig(MainMenu.VISUALIZE, state=tk.DISABLED)
        
        # Reapply config constraints (radio states + Run button state)
        self._apply_config_defaults()
        
        logger.info("Application state reset to defaults")
    
    def lock(self) -> None:
        """Disable all interactive controls while a modal sub-window is open."""
        # Consume shortcut key events so they don't fire on the root
        for _, _, key_event, _, _, _ in self._shortcuts:
            self.root.bind(key_event, lambda e: "break")
        # Disable buttons
        self.button_generate_dzn.config(state=tk.DISABLED)
        self.button_load_dzn.config(state=tk.DISABLED)
        self.button_load_csv.config(state=tk.DISABLED)
        self.button_run_minizinc.config(state=tk.DISABLED)
        self.button_visualize.config(state=tk.DISABLED)
        self.button_set_program_state_to_default.config(state=tk.DISABLED)
        
        # Disable menu entries
        self.menu_file.entryconfig( MainMenu.LOAD_DZN,  state=tk.DISABLED)
        self.menu_file.entryconfig( MainMenu.LOAD_CSV,  state=tk.DISABLED)
        self.menu_file.entryconfig( MainMenu.RCNT_DZN,  state=tk.DISABLED)
        self.menu_file.entryconfig( MainMenu.RCNT_CSV,  state=tk.DISABLED)
        self.menu_tools.entryconfig(MainMenu.GEN_DZN,   state=tk.DISABLED)
        self.menu_tools.entryconfig(MainMenu.RUN_MZN,   state=tk.DISABLED)
        self.menu_tools.entryconfig(MainMenu.VISUALIZE, state=tk.DISABLED)
        self.menu_tools.entryconfig(MainMenu.RESET,     state=tk.DISABLED)
        logger.debug("Main window locked")

    def unlock(self) -> None:
        """Re-enable main window controls after a modal sub-window closes."""
        try:
            if not self.root.winfo_exists():
                return  # Window was destroyed while modal was open
        except tk.TclError:
            return      # Tk interpreter itself was destroyed
        
        # Restore keyboard shortcuts
        self._setup_shortcuts()
        # Restore always-available controls
        self.button_generate_dzn.config(state=tk.NORMAL)
        self.button_load_dzn.config(state=tk.NORMAL)
        self.button_load_csv.config(state=tk.NORMAL)
        self.button_set_program_state_to_default.config(state=tk.NORMAL)
        self.menu_file.entryconfig( MainMenu.LOAD_DZN, state=tk.NORMAL)
        self.menu_file.entryconfig( MainMenu.LOAD_CSV, state=tk.NORMAL)
        self.menu_file.entryconfig( MainMenu.RCNT_DZN, state=tk.NORMAL)
        self.menu_file.entryconfig( MainMenu.RCNT_CSV, state=tk.NORMAL)
        self.menu_tools.entryconfig(MainMenu.GEN_DZN,  state=tk.NORMAL)
        self.menu_tools.entryconfig(MainMenu.RESET,    state=tk.NORMAL)
        
        # Restore state-dependent controls without resetting data
        self._update_run_minizinc_button_state()
        if self.csv_file_path.get():
            self.button_visualize.config(state=tk.NORMAL)
            self.menu_tools.entryconfig(MainMenu.VISUALIZE, state=tk.NORMAL)
        logger.debug("Main window unlocked")
    
    def show(self) -> None:
        """Show main window and start event loop."""
        logger.debug("Starting main window event loop")
        self.root.mainloop()
