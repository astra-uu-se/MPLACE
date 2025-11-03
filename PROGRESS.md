# MPLACE Progress Tracking

This document tracks the progress of key tasks in the MPLACE project.

## Current Status

| Priority | Item                             | Status         | Details                                                                                      |
|----------|----------------------------------|----------------|----------------------------------------------------------------------------------------------|
| High     | Implement MVC Architecture       | Not done       | UI, logic, and I/O are tightly coupled across main.py, WindowGenDZN.py, and WindowVisuals.py; need to separate Model (data structures), View (UI components), and Controller (business logic) layers. |
| High     | Decouple Window Dependencies     | Done           | Replaced direct variable sharing between main and WindowGenDZN with callback-based communication; introduced DznGenerationResult dataclass for structured data transfer; WindowGenDZN now uses completion_callback instead of directly manipulating main window variables; clean separation of concerns achieved. |
| High     | Add Comprehensive Error Handling | Done           | All generic except: blocks replaced with specific exceptions (ValueError, TypeError, KeyError, etc.); proper exception chaining with 'from e' added; user-friendly error dialogs implemented throughout all modules. |
| High     | Improve Resource Management      | Done           | Context managers for all file operations; matplotlib figures properly closed with pyplot.close(fig); defensive error handling in plotting ensures figures freed on failure; UI state consistency maintained across error paths; subprocess handling preserved as tested and working. |
| Medium   | Add Input Validation Layer       | Done           | Comprehensive schema validation for compounds/controls dictionaries with parse_materials_dict(), validate_materials_schema(), validate_plate_dimensions(), and format_validation_errors() functions; validates structure, types, bounds (rows/cols ≥ 1), material names (≤100 chars, printable), replicate counts (≥1), and provides user-friendly multi-error messages with examples; replaces basic ast.literal_eval error catching. |
| Medium   | Configuration Management         | Done           | paths.ini parsing centralized in utility.read_paths_ini_file with clearer error messages; needs environment variable support, validation schema, and centralized configuration object. Further improvements planned by original author. |
| Medium   | Code Style Standardization      | Done           | Comprehensive docstrings added to all functions with Args, Returns, Raises sections; consistent comment formatting throughout; proper type annotations on function parameters and returns. |
| Medium   | Add Comprehensive Type Hints    | Done           | Complete type annotations added across all modules using typing imports (List, Dict, Tuple, Union, Sequence); function signatures, class attributes, and global variables properly typed; numpy arrays and complex generic types annotated. |
| Medium   | Implement Consistent Naming Conventions | Done        | Constants converted to UPPERCASE (LETTERS_CAPITAL, LETTERS_LOWERCASE); variables use descriptive names (drugs, controls, num_rows, num_cols); UI elements follow consistent snake_case naming; preserved COMPD tool-specific naming. |
| Medium   | Extract Constants and Magic Numbers | Done        | Comprehensive constants.py module with organized classes (PlateDefaults, UI, Visualization, Performance, PathsIni, Messages, WindowConfig, MaterialDefaults, FileTypes, Validation, System); extracted 60+ magic numbers including plate dimensions, UI padding, widget sizes, visualization parameters, path parsing strings/offsets, and default values; significantly improved maintainability. |
| Medium   | Separate UI Layout from Logic    | Done | WindowGenDZN mixes UI setup with business logic; need clear separation between interface definition and data processing. |
| Low      | Cache Coordinate Transformations | Done           | Added @lru_cache(maxsize=2048) decorator to transform_coordinate function in utility.py; provides significant performance improvement for repeated well coordinate processing across materials and layouts. |
| Low      | Precompute Alpha Mappings        | Done           | Precompute transform_concentrations_to_alphas once per material in draw_plates() and pass to draw_plate() and draw_material_scale(); eliminates repeated alpha calculation across layouts and significantly improves visualization performance for multi-layout datasets. |
| Low      | Replace Tab20 Colormap Limitation | Not done      | Current 20-color limit causes repetition with many materials; implement extended colormap with 50+ distinct colors for better material differentiation. |
| Low      | Optimize Matplotlib Performance  | Done           | Cached pyplot.get_cmap('tab20') at module level as COLORMAP_TAB20 in WindowVisuals.py; eliminates repeated colormap lookups and improves rendering performance. |
| Low      | Implement Logging Framework     | Done           | Comprehensive logging system with dual approach: preserved print() statements for user-visible feedback while adding structured logging for debugging. PNG save paths now logged and printed for user visibility. Log file (mplace.log) captures all operations with timestamps. Logging levels: DEBUG for technical details, INFO for major operations, WARNING for recoverable issues, ERROR for failures. |
| Low      | Add Progress Indicators          | Not done       | Long-running MiniZinc operations show minimal feedback; add progress bars and status updates for better user experience. |
| Low      | Improve Error Diagnostics        | Not done       | MiniZinc failures could provide more specific diagnostic information; enhance subprocess error handling with context-specific guidance. |
| Low      | Add Bounds Checking             | Not done       | Plate dimensions and layout parameters lack validation against reasonable limits; add input validation with helpful error messages. |
| Low      | Enhance Documentation           | Not done       | Complex algorithms like parse_control_string need more detailed inline comments; add concrete usage examples in docstrings. |
| Low      | Add Unit Test Coverage          | Not done       | No apparent test coverage for utility functions and data processing; create test suite for core functionality. |
| Low      | Add Integration Tests           | Not done       | No end-to-end testing of DZN → MiniZinc → CSV → Visualization workflow; add comprehensive integration test suite. |
| Low      | Add Keyboard Shortcuts          | Not done       | No keyboard shortcuts for common operations; add standard shortcuts (Ctrl+O for open, etc.) for improved productivity. |
| Low      | Create Recent Files Menu        | Done           | No quick access to recently used DZN/CSV files; add recent files functionality for better workflow efficiency. |
| Low      | Add Batch Processing Support    | Not done       | No support for processing multiple files in sequence; add batch processing capabilities for research workflows. |
| Low      | Expand Export Format Options    | Not done       | Only PNG export currently supported; add PDF, SVG support for publication-quality figures. |
| Low      | Add Data Consistency Validation | Not done       | No validation that CSV data matches expected DZN parameters; add cross-validation between input and output data. |
| Low      | Create Data Transfer Objects    | Done           | Complex parameter passing could use structured objects instead of individual parameters for better maintainability. |
| Low      | Add Plater CSV Export Support   | Done.          | Add export of layouts to plater's plate-shaped CSV format for R ecosystem integration. Create plate-grid pivot by mapping well coordinates (A01 → row A, col 1) and writing plate-shaped layers (Treatment, Concentration). Implement conversion utilities in core/io_utils.py and expose via UI export options. Easy conversion from current MPLACE CSV format. |
| Low      | Add Wellmap TOML Export Support | Not done       | Add export of layouts to Wellmap TOML format for microplate metadata exchange. Group wells by compound/concentration patterns to generate [row], [col], and [block] sections with experimental metadata. Implement in core/io_utils.py and expose via UI export options. More complex than Plater format but enables richer experimental design workflows. |

---


### Organization Rules

**What Goes Where:**
- **ui/**: Only Tkinter widgets, layouts, and event binding. No file I/O, no complex algorithms
- **core/**: All the "heavy lifting" - file processing, subprocess calls, text generation  
- **models/**: Constants, simple data classes. No behavior/methods
- **config/**: Configuration loading and validation

**Safety Guidelines:**
- Test after each stage - don't move to next stage if current breaks
- Git commit after each working stage  
- One file at a time - don't move multiple files simultaneously
- Fix imports immediately - don't leave broken imports


## How to Update This File

This progress tracking file should be updated after each significant change or batch of changes to reflect the current status of development tasks.

**Status Values:**
- `Not done` - Task not started
- `Partially done` - Task in progress or partially completed  
- `In progress` - Task currently being worked on
- `Done (partial)` - Task mostly complete but may need refinement
- `Done` - Task fully completed

---

*Last updated: October 30, 2025 (completed "Create Recent Files Menu" task)*
