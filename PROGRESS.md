# MPLACE Progress Tracking

This document tracks the progress of key tasks in the MPLACE project.

## Current Status

| Priority | Item                             | Status         | Details                                                                                      |
|----------|----------------------------------|----------------|----------------------------------------------------------------------------------------------|
| High     | Implement MVC Architecture       | Not done       | UI, logic, and I/O are tightly coupled across main.py, WindowGenDZN.py, and WindowVisuals.py; need to separate Model (data structures), View (UI components), and Controller (business logic) layers. **See detailed transition plan below.** |
| High     | Decouple Window Dependencies     | Done           | Replaced direct variable sharing between main and WindowGenDZN with callback-based communication; introduced DznGenerationResult dataclass for structured data transfer; WindowGenDZN now uses completion_callback instead of directly manipulating main window variables; clean separation of concerns achieved. |
| High     | Add Comprehensive Error Handling | Done           | All generic except: blocks replaced with specific exceptions (ValueError, TypeError, KeyError, etc.); proper exception chaining with 'from e' added; user-friendly error dialogs implemented throughout all modules. |
| High     | Improve Resource Management      | Done           | Context managers for all file operations; matplotlib figures properly closed with pyplot.close(fig); defensive error handling in plotting ensures figures freed on failure; UI state consistency maintained across error paths; subprocess handling preserved as tested and working. |
| Medium   | Add Input Validation Layer       | Done           | Comprehensive schema validation for compounds/controls dictionaries with parse_materials_dict(), validate_materials_schema(), validate_plate_dimensions(), and format_validation_errors() functions; validates structure, types, bounds (rows/cols ≥ 1), material names (≤100 chars, printable), replicate counts (≥1), and provides user-friendly multi-error messages with examples; replaces basic ast.literal_eval error catching. |
| Medium   | Configuration Management         | Done           | All configuration parsing (including paths.ini) is now handled via config/loader.py and validated centrally. Section-aware config parsing with explicit error reporting for missing/invalid keys. Application configuration is represented by the AppConfig dataclass, passed to components at startup, enabling future environment variable support and extensible validation. Further improvements (e.g., .env support) still planned. |
| Medium   | Code Style Standardization       | Done           | Comprehensive docstrings added to all functions with Args, Returns, Raises sections; consistent comment formatting throughout; proper type annotations on function parameters and returns. |
| Medium   | Add Comprehensive Type Hints     | Done           | Complete type annotations added across all modules using typing imports (List, Dict, Tuple, Union, Sequence); function signatures, class attributes, and global variables properly typed; numpy arrays and complex generic types annotated. |
| Medium   | Implement Consistent Naming Conventions | Done        | Constants converted to UPPERCASE (LETTERS_CAPITAL, LETTERS_LOWERCASE); variables use descriptive names (drugs, controls, num_rows, num_cols); UI elements follow consistent snake_case naming; preserved COMPD tool-specific naming. |
| Medium   | Extract Constants and Magic Numbers | Done        | Comprehensive constants.py module with organized classes (PlateDefaults, UI, Visualization, Performance, PathsIni, Messages, WindowConfig, MaterialDefaults, FileTypes, Validation, System); extracted 60+ magic numbers including plate dimensions, UI padding, widget sizes, visualization parameters, path parsing strings/offsets, and default values; significantly improved maintainability. |
| Medium   | Separate UI Layout from Logic    | Done | WindowGenDZN mixes UI setup with business logic; need clear separation between interface definition and data processing. |
| Low      | Cache Coordinate Transformations | Done           | Added @lru_cache(maxsize=2048) decorator to transform_coordinate function in utility.py; provides significant performance improvement for repeated well coordinate processing across materials and layouts. |
| Low      | Precompute Alpha Mappings        | Done           | Precompute transform_concentrations_to_alphas once per material in draw_plates() and pass to draw_plate() and draw_material_scale(); eliminates repeated alpha calculation across layouts and significantly improves visualization performance for multi-layout datasets. |
| Low      | Replace Tab20 Colormap Limitation | Not done      | Current 20-color limit causes repetition with many materials; implement extended colormap with 50+ distinct colors for better material differentiation. |
| Low      | Optimize Matplotlib Performance  | Done           | Cached pyplot.get_cmap('tab20') at module level as COLORMAP_TAB20 in WindowVisuals.py; eliminates repeated colormap lookups and improves rendering performance. |
| Low      | Implement Logging Framework      | Done           | Comprehensive logging system with dual approach: preserved print() statements for user-visible feedback while adding structured logging for debugging. PNG save paths now logged and printed for user visibility. Log file (mplace.log) captures all operations with timestamps. Logging levels: DEBUG for technical details, INFO for major operations, WARNING for recoverable issues, ERROR for failures. |
| Low      | Add Progress Indicators          | Not done       | Long-running MiniZinc operations show minimal feedback; add progress bars and status updates for better user experience. |
| Low      | Improve Error Diagnostics        | Not done       | MiniZinc failures could provide more specific diagnostic information; enhance subprocess error handling with context-specific guidance. |
| Low      | Add Bounds Checking              | Not done       | Plate dimensions and layout parameters lack validation against reasonable limits; add input validation with helpful error messages. |
| Low      | Enhance Documentation            | Not done       | Complex algorithms like parse_control_string need more detailed inline comments; add concrete usage examples in docstrings. |
| Low      | Add Unit Test Coverage           | Not done       | No apparent test coverage for utility functions and data processing; create test suite for core functionality. |
| Low      | Add Integration Tests            | Not done       | No end-to-end testing of DZN → MiniZinc → CSV → Visualization workflow; add comprehensive integration test suite. |
| Low      | Add Keyboard Shortcuts           | Not done       | No keyboard shortcuts for common operations; add standard shortcuts (Ctrl+O for open, etc.) for improved productivity. |
| Low      | Create Recent Files Menu         | Done           | No quick access to recently used DZN/CSV files; add recent files functionality for better workflow efficiency. |
| Low      | Add Batch Processing Support     | Not done       | No support for processing multiple files in sequence; add batch processing capabilities for research workflows. |
| Low      | Expand Export Format Options     | Done           | Export support for PNG and PDF formats for publication-quality figures. |
| Low      | Add Data Consistency Validation  | Not done       | No validation that CSV data matches expected DZN parameters; add cross-validation between input and output data. |
| Low      | Create Data Transfer Objects     | Done           | Complex parameter passing could use structured objects instead of individual parameters for better maintainability. |
| Low      | Add Plater CSV Export Support    | Done.          | Add export of layouts to plater's plate-shaped CSV format for R ecosystem integration. Create plate-grid pivot by mapping well coordinates (A01 → row A, col 1) and writing plate-shaped layers (Treatment, Concentration). Implement conversion utilities in core/io_utils.py and expose via UI export options. Easy conversion from current MPLACE CSV format. |
| Low      | Add Wellmap TOML Export Support  | Not done       | Add export of layouts to Wellmap TOML format for microplate metadata exchange. Group wells by compound/concentration patterns to generate [row], [col], and [block] sections with experimental metadata. Implement in core/io_utils.py and expose via UI export options. More complex than Plater format but enables richer experimental design workflows. |

---

## MVC Architecture Transition Plan

### Current Architecture Analysis

**Current Structure (Monolithic):**
```
mplace.py (1000 lines)
├── UI Layout (frames, buttons, labels)
├── Event Handlers (on button clicks)
├── Business Logic (DZN generation, MiniZinc execution, CSV conversion)
├── File I/O (read/write CSV, DZN)
├── Application State (global tk.StringVar, paths)
└── Recent Files Management

ui/window_dzn.py (640 lines)
├── UI Layout (DZN generation form)
├── Event Handlers (form submission)
├── Business Logic (DZN text generation)
├── Validation Logic (materials, dimensions)
└── Callback Communication

ui/window_visuals.py (600 lines)
├── UI Layout (visualization window)
├── Event Handlers (save button)
├── Matplotlib Rendering
├── Figure Export Logic
└── Resource Cleanup
```

**Problems:**
1. **Tight Coupling:** UI widgets directly call business logic functions
2. **Global State:** Application state scattered across tk.StringVar and module-level variables
3. **Mixed Responsibilities:** Single functions handle UI updates, file I/O, and business logic
4. **Testing Difficulty:** Cannot test business logic without initializing Tkinter
5. **Code Duplication:** Similar patterns (file dialogs, error handling) repeated across modules

---

### Target MVC Architecture

**New Structure:**

```
models/
├── application_state.py    # NEW: Centralized application state
├── dzn_data.py             # NEW: DZN-related data models
├── csv_data.py             # NEW: CSV/Layout data models
├── constants.py            # EXISTING: Configuration constants
└── dto.py                  # EXISTING: Data transfer objects

controllers/
├── main_controller.py      # NEW: Main window orchestration
├── dzn_controller.py       # NEW: DZN generation logic
├── minizinc_controller.py  # NEW: Model execution logic
├── csv_controller.py       # NEW: CSV export/import logic
└── viz_controller.py       # NEW: Visualization orchestration

views/
├── main_view.py            # NEW: Main window UI (refactored from mplace.py)
├── dzn_view.py             # NEW: DZN form UI (refactored from window_dzn.py)
├── viz_view.py             # NEW: Visualization UI (refactored from window_visuals.py)
└── dialogs.py              # NEW: Reusable dialog components

core/                        # EXISTING: Utility functions (mostly unchanged)
├── dzn_parser.py           # Keep as-is
├── dzn_writer.py           # Keep as-is
├── io_utils.py             # Keep as-is
├── layout_utils.py         # Keep as-is
├── minizinc_runner.py      # Keep as-is
└── validators.py           # Keep as-is
```

---

### Detailed Migration Stages

#### **Stage 1: Create Model Layer (Week 1)**

**Goal:** Extract all application state into proper Model classes.

**Tasks:**

1. **Create `models/application_state.py`:**
   ```python
   from dataclasses import dataclass, field
   from typing import Optional, List
   
   @dataclass
   class ApplicationState:
       """Central application state - replaces scattered tk.StringVar"""
       # File paths
       dzn_file_path: str = ''
       csv_file_path: str = ''
       
       # Plate configuration
       num_rows: str = '16'
       num_cols: str = '24'
       control_names: str = '[]'
       
       # Model selection
       use_compd: bool = False
       
       # Configuration paths
       minizinc_path: str = ''
       plaid_path: str = ''
       compd_path: str = ''
       plaid_mpc_path: str = ''
       compd_mpc_path: str = ''
       
       # Recent files
       recent_dzn: List[str] = field(default_factory=list)
       recent_csv: List[str] = field(default_factory=list)
   ```

2. **Create `models/dzn_data.py`:**
   ```python
   from dataclasses import dataclass
   from typing import Dict, List
   
   @dataclass
   class DznFormData:
       """DZN generation form data"""
       num_rows: str
       num_cols: str
       inner_empty_edge: bool
       size_empty_edge: str
       size_corner_empty_wells: str
       horizontal_cell_lines: str
       vertical_cell_lines: str
       flag_allow_empty_wells: bool
       flag_concentrations_on_different_rows: bool
       flag_concentrations_on_different_columns: bool
       flag_replicates_on_different_plates: bool
       flag_replicates_on_same_plate: bool
       compounds_dict: Dict[str, List]
       controls_dict: Dict[str, List]
   ```

3. **Create `models/csv_data.py`:**
   ```python
   from dataclasses import dataclass
   from typing import List, Dict, Tuple
   import matplotlib.figure as mpl_figure
   
   @dataclass
   class LayoutData:
       """Parsed CSV layout data"""
       layouts_dict: Dict[str, List[List[str]]]
       concentrations_list: Dict[str, List]
       material_colors: Dict[str, any]
       alpha_mappings: Dict[str, Dict]
   
   @dataclass
   class VisualizationState:
       """State for visualization window"""
       figures_to_save: List[Tuple[mpl_figure.Figure, str]]
       material_scales: List[mpl_figure.Figure]
       file_path: str
       figure_name_template: str
       num_rows: int
       num_cols: int
       control_names: List[str]
   ```

**Validation:**
- Models can be instantiated without Tkinter
- Models have clear, documented fields
- All state is centralized, no scattered globals

---

#### **Stage 2: Create Controller Layer (Week 2-3)**

**Goal:** Extract all business logic into Controllers that manipulate Models.

**Tasks:**

1. **Create `controllers/main_controller.py`:**
   ```python
   class MainController:
       """Orchestrates main window operations"""
       
       def __init__(self, state: ApplicationState):
           self.state = state
           self.dzn_controller = DznController()
           self.minizinc_controller = MiniZincController()
           self.csv_controller = CsvController()
       
       def load_dzn_file(self, path: str) -> None:
           """Load DZN file and update state"""
           cols, rows, controls = scan_dzn(path)
           self.state.dzn_file_path = path
           self.state.num_cols = cols
           self.state.num_rows = rows
           self.state.control_names = controls
       
       def load_csv_file(self, path: str) -> None:
           """Load CSV file and update state"""
           # Validation logic here
           self.state.csv_file_path = path
       
       def execute_minizinc(self) -> List[str]:
           """Execute MiniZinc model and return CSV lines"""
           return self.minizinc_controller.run_model(
               self.state.minizinc_path,
               self.state.plaid_mpc_path if not self.state.use_compd else self.state.compd_mpc_path,
               self.state.plaid_path if not self.state.use_compd else self.state.compd_path,
               self.state.dzn_file_path
           )
       
       def reset_state(self) -> None:
           """Reset application to defaults"""
           self.state.dzn_file_path = ''
           self.state.csv_file_path = ''
           # ... reset other fields
   ```

2. **Create `controllers/dzn_controller.py`:**
   ```python
   class DznController:
       """Handles DZN generation logic"""
       
       def validate_form_data(self, data: DznFormData) -> List[str]:
           """Validate DZN form data, return errors"""
           errors = []
           errors.extend(validate_plate_dimensions(data.num_rows, data.num_cols))
           
           compounds, parse_errors = parse_materials_dict(data.compounds_dict)
           errors.extend(parse_errors)
           if not parse_errors:
               errors.extend(validate_materials_schema(compounds, "compounds"))
           
           # ... validation logic from window_dzn.py
           return errors
       
       def generate_dzn_file(self, data: DznFormData, save_path: str) -> Tuple[str, List[str]]:
           """Generate DZN file content and control names"""
           params = DznBuildParams(
               num_rows=data.num_rows,
               num_cols=data.num_cols,
               # ... other fields
           )
           return build_dzn_text(params)
   ```

3. **Create `controllers/minizinc_controller.py`:**
   ```python
   class MiniZincController:
       """Handles MiniZinc execution"""
       
       def run_model(self, minizinc_path: str, solver_config: str, 
                     model_file: str, dzn_file: str) -> str:
           """Execute MiniZinc and return output"""
           return run_model(minizinc_path, solver_config, model_file, dzn_file)
       
       def extract_csv_from_output(self, output: str) -> List[str]:
           """Extract CSV lines from MiniZinc output"""
           return extract_csv_text(output)
   ```

4. **Create `controllers/csv_controller.py`:**
   ```python
   class CsvController:
       """Handles CSV import/export"""
       
       def export_pharmbio(self, csv_lines: List[str], suggested_name: str) -> str:
           """Export in PharmBio format"""
           return write_csv_file(csv_lines, suggested_filename=suggested_name)
       
       def export_plater(self, csv_lines: List[str], rows: str, cols: str) -> List[str]:
           """Export in PLATER format"""
           conversion_input = CSVConversionRequest(
               csv_lines=csv_lines, rows=rows, cols=cols
           )
           return convert_pharmbio_to_plater(conversion_input)
   ```

5. **Create `controllers/viz_controller.py`:**
   ```python
   class VisualizationController:
       """Orchestrates visualization logic"""
       
       def __init__(self):
           self.state: Optional[VisualizationState] = None
       
       def prepare_visualization(self, csv_path: str, template: str, 
                                rows: str, cols: str, controls: str) -> VisualizationState:
           """Prepare visualization data"""
           text_array = read_csv_file(csv_path)
           layouts_dict, concentrations_list = find_all_plates_concentrations(text_array)
           
           # Precompute alpha mappings and colors
           alpha_mappings = {mat: transform_concentrations_to_alphas(conc) 
                           for mat, conc in concentrations_list.items()}
           
           material_colors = self._generate_colors(concentrations_list)
           
           return VisualizationState(
               figures_to_save=[],
               material_scales=[],
               file_path=csv_path,
               figure_name_template=template,
               num_rows=int(rows),
               num_cols=int(cols),
               control_names=ast.literal_eval(controls)
           )
       
       def export_figures_png(self, state: VisualizationState) -> List[str]:
           """Export all figures as individual PNGs"""
           saved_paths = []
           for fig, filename_template in state.figures_to_save:
               path = write_figure(fig, FileTypes.PNG_FILES, filename_template)
               if path not in [-1, -2]:
                   saved_paths.append(path)
           return saved_paths
       
       def export_figures_pdf(self, state: VisualizationState) -> str:
           """Export all figures as single PDF"""
           return write_figures_in_pdf(
               state.figures_to_save, 
               state.figure_name_template, 
               state.material_scales
           )
   ```

**Validation:**
- Controllers have no Tkinter imports
- Controllers can be unit tested with mock Models
- All business logic extracted from UI files

---

#### **Stage 3: Refactor View Layer (Week 4-5)**

**Goal:** Convert UI files into pure Views that only handle display and user input.

**Tasks:**

1. **Create `views/main_view.py`:**
   ```python
   class MainView:
       """Main window UI - pure view layer"""
       
       def __init__(self, root: tk.Tk, controller: MainController):
           self.root = root
           self.controller = controller
           self._setup_ui()
           self._bind_events()
       
       def _setup_ui(self):
           """Create all UI widgets"""
           # Frame 1: DZN file generation/loading
           self.frame_dzn = ttk.LabelFrame(self.root, text=Messages.FRAME_TITLE_DZN)
           self.button_generate_dzn = ttk.Button(self.frame_dzn, text=Messages.BUTTON_GENERATE_DZN)
           # ... create all widgets
       
       def _bind_events(self):
           """Connect UI events to controller methods"""
           self.button_load_dzn.configure(command=self._on_load_dzn_clicked)
           self.button_run_minizinc.configure(command=self._on_run_minizinc_clicked)
           # ... bind all events
       
       def _on_load_dzn_clicked(self):
           """Handle DZN load button click"""
           path = filedialog.askopenfilename(
               title='Open DZN file',
               filetypes=FileTypes.DZN_FILES
           )
           if path:
               try:
                   self.controller.load_dzn_file(path)
                   self.refresh_from_state()
               except Exception as e:
                   messagebox.showerror("Error", f"Failed to load: {str(e)}")
       
       def refresh_from_state(self):
           """Update UI widgets from controller state"""
           state = self.controller.state
           path_show(state.dzn_file_path, self.label_dzn_loaded)
           # ... update all widgets from state
       
       def enable_run_button(self):
           """Enable MiniZinc run button"""
           self.button_run_minizinc.config(state=tk.NORMAL)
       
       def disable_run_button(self):
           """Disable MiniZinc run button"""
           self.button_run_minizinc.config(state=tk.DISABLED)
   ```

2. **Create `views/dzn_view.py`:**
   ```python
   class DznView:
       """DZN generation form - pure view layer"""
       
       def __init__(self, parent: tk.Tk, controller: DznController, 
                    completion_callback: Callable):
           self.parent = parent
           self.controller = controller
           self.completion_callback = completion_callback
           self._setup_ui()
       
       def _setup_ui(self):
           """Create DZN form widgets"""
           self.window = tk.Toplevel(self.parent)
           self.window.title(WindowConfig.TITLE_DZN_GENERATOR)
           # ... create all form fields
       
       def _on_generate_clicked(self):
           """Handle generate button click"""
           # Collect form data
           form_data = DznFormData(
               num_rows=self.num_rows.get(),
               num_cols=self.num_cols.get(),
               # ... collect all fields
           )
           
           # Validate via controller
           errors = self.controller.validate_form_data(form_data)
           if errors:
               messagebox.showerror("Validation Error", format_validation_errors(errors))
               return
           
           # Show save dialog
           path = filedialog.asksaveasfilename(
               defaultextension=".dzn",
               filetypes=FileTypes.DZN_FILES
           )
           if not path:
               return
           
           # Generate via controller
           try:
               dzn_text, control_names = self.controller.generate_dzn_file(form_data, path)
               
               # Write file
               with open(path, 'w') as f:
                   f.write(dzn_text)
               
               # Notify parent
               result = DznGenerationResult(
                   file_path=path,
                   rows=form_data.num_rows,
                   cols=form_data.num_cols,
                   control_names=str(control_names)
               )
               self.completion_callback(result)
               self.window.withdraw()
           except Exception as e:
               messagebox.showerror("Error", f"Failed to generate: {str(e)}")
       
       def show(self):
           """Show DZN generation window"""
           self.window.deiconify()
       
       def reset_form(self):
           """Reset form to defaults"""
           # Reset all form fields
           pass
   ```

3. **Create `views/viz_view.py`:**
   ```python
   class VisualizationView:
       """Visualization window - pure view layer"""
       
       def __init__(self, controller: VisualizationController, state: VisualizationState):
           self.controller = controller
           self.state = state
           self.window = tk.Tk()
           self._setup_ui()
       
       def _setup_ui(self):
           """Create visualization window UI"""
           self.window.title(WindowConfig.TITLE_VISUALIZER)
           self.save_button = ttk.Button(
               self.window, 
               text=Messages.BUTTON_SAVE_LAYOUT,
               command=self._on_save_clicked
           )
           # ... create all widgets
       
       def _on_save_clicked(self):
           """Handle save button click"""
           if len(self.state.figures_to_save) == 1:
               self._save_single_figure()
           else:
               self._save_multiple_figures()
       
       def _save_single_figure(self):
           """Save single figure with format choice"""
           figure, filename = self.state.figures_to_save[0]
           path = write_figure(figure, FileTypes.FIG_FILES, filename, self.state.material_scales)
           if path not in [-1, -2]:
               messagebox.showinfo("Success", f"Saved: {path}")
       
       def _save_multiple_figures(self):
           """Save multiple figures as PNG or PDF"""
           format_choice = ask_layout_export_format(
               self.window, 
               [(FileTypes.PDF, FileTypes.PDF_LABEL), (FileTypes.PNG, FileTypes.PNG_LABEL)]
           )
           
           if format_choice == FileTypes.PNG:
               saved_paths = self.controller.export_figures_png(self.state)
               if saved_paths:
                   file_list = '\n'.join(f"• {p}" for p in saved_paths)
                   messagebox.showinfo("Success", f"Saved {len(saved_paths)} files:\n\n{file_list}")
           elif format_choice == FileTypes.PDF:
               path = self.controller.export_figures_pdf(self.state)
               if path not in [-1, -2]:
                   messagebox.showinfo("Success", f"Saved: {path}")
       
       def render_plates(self):
           """Render all plate visualizations"""
           # Delegate to existing draw_plates function but pass state
           draw_plates(
               self.window,
               self.state.figure_name_template,
               read_csv_file(self.state.file_path),
               num_rows=self.state.num_rows,
               num_cols=self.state.num_cols,
               control_names=self.state.control_names,
               figures_to_save=self.state.figures_to_save,
               material_scales=self.state.material_scales
           )
       
       def show(self):
           """Show visualization window"""
           self.window.mainloop()
   ```

4. **Create `views/dialogs.py`:**
   ```python
   """Reusable dialog components"""
   
   def show_error_dialog(title: str, message: str):
       """Show error message dialog"""
       messagebox.showerror(title, message)
   
   def show_info_dialog(title: str, message: str):
       """Show information dialog"""
       messagebox.showinfo(title, message)
   
   def ask_save_file(title: str, filetypes: List, suggested_name: str = '') -> Optional[str]:
       """Show save file dialog"""
       return filedialog.asksaveasfilename(
           title=title,
           filetypes=filetypes,
           initialfile=suggested_name
       )
   
   def ask_open_file(title: str, filetypes: List) -> Optional[str]:
       """Show open file dialog"""
       return filedialog.askopenfilename(title=title, filetypes=filetypes)
   ```

**Validation:**
- Views only handle widget creation and event binding
- Views call Controller methods, never directly manipulate Models
- Views have no business logic (validation, file I/O, calculations)

---

#### **Stage 4: Update Main Entry Point (Week 6)**

**Goal:** Create new `mplace.py` that wires together MVC components.

**Tasks:**

1. **Create new `mplace.py`:**
   ```python
   """
   MPLACE - MicroPlate Layout Arrangement with Constraint Engines
   Main application entry point (MVC architecture)
   """
   
   import sys
   import logging
   import tkinter as tk
   
   from models.application_state import ApplicationState
   from controllers.main_controller import MainController
   from views.main_view import MainView
   from config.loader import load_config
   
   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('mplace.log'),
           logging.StreamHandler(sys.stdout)
       ]
   )
   logger = logging.getLogger(__name__)
   
   def main():
       """Application entry point"""
       logger.info("MPLACE application starting")
       
       # Load configuration
       try:
           app_config = load_config()
           logger.info("Configuration loaded")
       except FileNotFoundError as e:
           logger.critical(f"Configuration error: {e}")
           tk.messagebox.showerror("Configuration Error", str(e))
           sys.exit(1)
       
       # Initialize state
       state = ApplicationState(
           minizinc_path=app_config.minizinc_path,
           plaid_path=app_config.plaid_path,
           compd_path=app_config.compd_path,
           plaid_mpc_path=app_config.plaid_mpc_path,
           compd_mpc_path=app_config.compd_mpc_path
       )
       
       # Create MVC components
       root = tk.Tk()
       controller = MainController(state)
       view = MainView(root, controller)
       
       # Start application
       logger.info("MPLACE GUI initialized, entering main loop")
       root.mainloop()
   
   if __name__ == "__main__":
       main()
   ```

2. **Rename old `mplace.py` to `mplace_old.py` for reference**

3. **Test new architecture:**
   - All buttons work as before
   - File dialogs function correctly
   - State persists properly
   - Error handling works

**Validation:**
- Application starts and runs correctly
- All features work as before
- Code is significantly cleaner and more testable

---

### Migration Strategy

**Risk Mitigation:**
1. **Git Branching:** Create `mvc-refactor` branch, keep `main` stable
2. **Incremental Testing:** Test after each stage before proceeding
3. **Parallel Development:** Keep old code alongside new until fully validated
4. **Rollback Plan:** Can revert to old architecture at any stage

**Testing Approach:**
1. **Unit Tests:** Write tests for Controllers and Models (no Tkinter needed)
2. **Integration Tests:** Test Controller-Model interactions
3. **Manual Testing:** Test all UI workflows after each stage
4. **Regression Testing:** Ensure no features break during migration

**Time Estimates:**
- Stage 1 (Models): 1 week
- Stage 2 (Controllers): 2 weeks
- Stage 3 (Views): 2 weeks
- Stage 4 (Integration): 1 week
- **Total: 6 weeks** (assuming part-time development)

---

### Benefits After Migration

**Code Quality:**
- ✅ Clean separation of concerns
- ✅ Testable business logic
- ✅ Reusable components
- ✅ Maintainable codebase

**Development Speed:**
- ✅ Easier to add features
- ✅ Faster debugging
- ✅ Safer refactoring
- ✅ Better collaboration

**Testing:**
- ✅ Unit tests for Controllers
- ✅ Integration tests without UI
- ✅ Mock-based testing
- ✅ Higher code coverage

**Architecture:**
- ✅ Industry-standard MVC pattern
- ✅ Clear component boundaries
- ✅ Scalable structure
- ✅ Documentation-friendly

---

### Organization Rules

**What Goes Where:**
- **models/**: Data structures and application state. No behavior except simple getters/setters.
- **controllers/**: Business logic, orchestration, validation. No UI code, no direct widget manipulation.
- **views/**: Tkinter widgets, layouts, event binding. No business logic, no file I/O.
- **core/**: Utility functions, algorithms, pure functions. No state, no UI.
- **config/**: Configuration loading and validation.

**Safety Guidelines:**
- Test after each stage - don't move to next stage if current breaks
- Git commit after each working stage  
- One file at a time - don't move multiple files simultaneously
- Fix imports immediately - don't leave broken imports
- Keep old code until new code is fully validated

---

## How to Update This File

This progress tracking file should be updated after each significant change or batch of changes to reflect the current status of development tasks.

**Status Values:**
- `Not done` - Task not started
- `Partially done` - Task in progress or partially completed  
- `In progress` - Task currently being worked on
- `Done (partial)` - Task mostly complete but may need refinement
- `Done` - Task fully completed

---

*Last updated: November 20, 2025 (added comprehensive MVC transition plan)*
