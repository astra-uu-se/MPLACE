"""Core business logic for MPLACE.

This package contains the domain logic for:
- DZN file parsing and generation (dzn_parser, dzn_writer)
- CSV file I/O and format conversion (io_utils)
- MiniZinc model execution (minizinc_runner)
- Input validation and schema checking (validators)
- Layout coordinate transformations (layout_utils)

These modules are UI-agnostic and can be used independently
of the Tkinter interface layer.
"""
