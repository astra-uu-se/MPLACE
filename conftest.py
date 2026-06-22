import sys
import os

# Ensure the project root is on sys.path so that packages like `core`,
# `models`, and `controllers` are importable from test modules.
sys.path.insert(0, os.path.dirname(__file__))
