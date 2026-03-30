# MPLACE Progress Tracking

This document tracks the progress of key tasks in the MPLACE project.

## Current Status

| Priority | Item                             | Status         | Details                                                                                      |
|----------|----------------------------------|----------------|----------------------------------------------------------------------------------------------|
| High     | Implement MVC Architecture       | Done           | UI, logic, and I/O were tightly coupled across main.py, WindowGenDZN.py, and WindowVisuals.py; separated everything into Model (data structures), View (UI components), and Controller (business logic) layers. |
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
| Low      | Replace Tab20 Colormap Limitation | Done          | Previous 20-color limit causes repetition with many materials; implemented extended colormap with 60 distinct colors for better material differentiation. |
| Low      | Optimize Matplotlib Performance  | Done           | Cached pyplot.get_cmap('tab20') at module level as COLORMAP_TAB20 in WindowVisuals.py; eliminates repeated colormap lookups and improves rendering performance. |
| Low      | Implement Logging Framework      | Done           | Comprehensive logging system with dual approach: preserved print() statements for user-visible feedback while adding structured logging for debugging. PNG save paths now logged and printed for user visibility. Log file (mplace.log) captures all operations with timestamps. Logging levels: DEBUG for technical details, INFO for major operations, WARNING for recoverable issues, ERROR for failures. |
| Low      | Add Progress Indicators          | Done           | Long-running MiniZinc operations show feedback the elapsed time and, if applicable, the process timeouts. |
| Low      | Improve Error Diagnostics        | Done           | MiniZinc failures provide more specific diagnostic information which is now shown to the user; enhanced subprocess error handling with context-specific guidance. |
| Low      | Add Bounds Checking              | Done           | Plate dimensions and layout parameters are validated against reasonable limits which are introduced in COMPD, and PLAID; add input validation with helpful error messages. |
| Low      | Enhance Documentation            | Done           | Complex algorithms like __parse_control_string__ have more detailed inline comments; added concrete usage examples in docstrings when necessary. |
| Low      | Add Unit Test Coverage           | Not done       | No apparent test coverage for utility functions and data processing; create a test suite for core functionality. |
| Low      | Add Integration Tests            | Not done       | No end-to-end testing of DZN → MiniZinc → CSV → Visualization workflow; add comprehensive integration test suite. |
| Low      | Add Keyboard Shortcuts           | Done       | Added keyboard shortcuts for common operations, together with additional main menu items |
| Low      | Create Recent Files Menu         | Done           | No quick access to recently used DZN/CSV files; add recent files functionality for better workflow efficiency. |
| Low      | Add Batch Processing Support     | Not done       | No support for processing multiple files in sequence; add batch processing capabilities for research workflows. |
| Low      | Expand Export Format Options     | Done           | Export support for PNG and PDF formats for publication-quality figures. |
| Low      | Add Data Consistency Validation  | Done            | Basic validation of the loaded CSV file is performed: if the CSV file wells exceed set plate dimensions, a warning is shown to the user|
| Low      | Create Data Transfer Objects     | Done           | Complex parameter passing could use structured objects instead of individual parameters for better maintainability. |
| Low      | Add Plater CSV Export Support    | Done.          | Add export of layouts to plater's plate-shaped CSV format for R ecosystem integration. Create plate-grid pivot by mapping well coordinates (A01 → row A, col 1) and writing plate-shaped layers (Treatment, Concentration). Implement conversion utilities in core/io_utils.py and expose via UI export options. Easy conversion from current MPLACE CSV format. |
| Low      | Add Wellmap TOML Export Support  | Not done       | Add export of layouts to Wellmap TOML format for microplate metadata exchange. Group wells by compound/concentration patterns to generate [row], [col], and [block] sections with experimental metadata. Implement in core/io_utils.py and expose via UI export options. More complex than Plater format but enables richer experimental design workflows. |

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

*Last updated: March 24, 2026 ("Add Bounds Checking" task is done)*
