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
# Description: MPLACE - MicroPlate Layout Arrangement with Constraint Engines
# Main application entry point with MVC architecture.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.2.5
# Last Revision: March 2026

import tkinter as tk
import logging
import sys
from pathlib import Path

# Controllers
from controllers.main_controller import MainController
from controllers.dzn_controller import DznController
from controllers.csv_controller import CsvController
from controllers.viz_controller import VisualizationController

# Views
from views.main_view import MainView
from views.dzn_view import DznView
from views.viz_view import VizView

# Models
from models.application_state import ApplicationState

# Constants
from models.constants import PathsIni, Messages

def setup_logging() -> None:
    """Configure application-wide logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mplace.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("MPLACE application starting")

def initialize_application_state() -> ApplicationState:
    """
    Initialize application state with default paths.
    
    Returns:
        Initialized ApplicationState instance
    """
    state = ApplicationState()
    # Set default paths from constants
    state.minizinc_path = PathsIni.MINIZINC
    state.plaid_path = PathsIni.PLAID
    state.plaid_mpc_path = PathsIni.PLAID_MPC
    state.compd_path = PathsIni.COMPD
    state.compd_mpc_path = PathsIni.COMPD_MPC
    
    logger = logging.getLogger(__name__)
    logger.info("Application state initialized")
    return state

class MPlaceApplication:
    """
    Main MPLACE application coordinator.
    
    This class wires together the MVC components and manages the application lifecycle.
    
    Attributes:
        root: Tkinter root window
        state: Application state
        controllers: Dictionary of controller instances
        views: Dictionary of view instances
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing MPlaceApplication")
        
        self.root = tk.Tk()
        self.state = initialize_application_state()
        self.controllers = self._create_controllers()
        self.views = self._create_views()
        
        # Display startup warnings for missing configurations
        self._show_startup_warnings()
        
        self.logger.info("MPlaceApplication initialized successfully")
    
    
    def _create_controllers(self) -> dict:
        """
        Create all controller instances.
        
        Returns:
            Dictionary of controller instances
        """
        # MainController creates and manages MiniZincController internally
        controllers = {
            'main': MainController(self.state),
            'dzn': DznController(),
            'csv': CsvController(),
            'viz': VisualizationController()
        }
        
        self.logger.debug(f"Created {len(controllers)} controllers")
        return controllers
    
    def _create_views(self) -> dict:
        """
        Create all view instances and wire them to controllers.
        
        Returns:
            Dictionary of view instances
        """
        # Create main view - access minizinc_controller through main controller
        main_view = MainView(
            root=self.root,
            controller=self.controllers['main'],
            minizinc_controller=self.controllers['main'].minizinc_controller,  # ← Access through main
            csv_controller=self.controllers['csv'],
            on_generate_dzn_clicked=self._open_dzn_window,
            on_visualize_clicked=self._open_viz_window
        )
        
        # Create DZN view with callback for completion
        dzn_view = DznView(
            parent=self.root,
            controller=self.controllers['dzn'],
            on_generation_complete=self._on_dzn_generated,
            on_window_closed=lambda: main_view.unlock()
        )
        
        # Create visualization view
        viz_view = VizView(
            parent=self.root,
            viz_controller=self.controllers['viz'],
            csv_controller=self.controllers['csv']
        )
        
        views = {
            'main': main_view,
            'dzn': dzn_view,
            'viz': viz_view
        }
        
        self.logger.debug(f"Created {len(views)} views")
        return views
    
    def _show_startup_warnings(self) -> None:
        """Display warnings for missing or misconfigured files."""
        startup_warnings = []
        config = self.controllers['main'].app_config
        
        if config.minizinc_path == PathsIni.FILE_ERROR_PLACEHOLDER:
            startup_warnings.append("MiniZinc is not found - can not use PLAID or COMPD.")
        if config.plaid_path == PathsIni.FILE_ERROR_PLACEHOLDER:
            startup_warnings.append("PLAID model file is not loaded: can not use PLAID model.")
        if config.compd_path == PathsIni.FILE_ERROR_PLACEHOLDER:
            startup_warnings.append("COMPD model file is not loaded: can not use COMPD model.")
        if config.plaid_mpc_path == PathsIni.FILE_ERROR_PLACEHOLDER:
            startup_warnings.append("Solver configuration for PLAID is not loaded. Default configuration (Gecode, 1 thread) will be used.")
        if config.compd_mpc_path == PathsIni.FILE_ERROR_PLACEHOLDER:
            startup_warnings.append("Solver configuration for COMPD is not loaded. Default configuration (Gecode, 1 thread) will be used.")
        
        if len(startup_warnings) == 1:
            tk.messagebox.showwarning("Warning", startup_warnings[0])
        elif len(startup_warnings) > 1:
            tk.messagebox.showwarning("Warnings", "\n\n".join(startup_warnings))
    
    def _open_dzn_window(self) -> None:
        """Open the DZN generation window."""
        self.logger.info("Opening DZN generation window")
        self.views['main'].lock()       # ← lock before opening
        self.views['dzn'].show()
    
    def _open_viz_window(self) -> None:
        """Open the visualization window."""
        self.logger.info("Opening visualization window")
        self.views['main'].lock()
        state = self.state
        
        # Check if CSV is loaded
        if not state.csv_file_path:
            self.logger.warning("Attempted to open visualization without CSV loaded")
            tk.messagebox.showerror("Error", "Please load a CSV file first")
            return
        
        # Generate figure name template
        csv_path = Path(state.csv_file_path)
        
        # Add model name suffix to figure template to distinguish PLAID vs COMPD results
        model_name = Messages.MODEL_COMPD if state.use_compd else Messages.MODEL_PLAID
        figure_name_template = str(csv_path.parent / csv_path.stem) + '_' + model_name + '_'
        
        
        # Open visualization
        self.views['viz'].show(
            file_path=state.csv_file_path,
            figure_name_template=figure_name_template,
            rows=state.num_rows,
            cols=state.num_cols,
            control_names=state.control_names
        )
        
        self.views['main'].unlock()
    
    def _on_dzn_generated(self, file_path: str, rows: str, cols: str, controls: str) -> None:
        """
        Handle DZN file generation completion.
        
        Args:
            file_path: Path to generated DZN file
            rows: Number of rows
            cols: Number of columns
            controls: Control names string
        """
        self.logger.info(f"DZN generated: {file_path}")
        
        # Update main view
        self.views['main'].update_after_dzn_generation(
            file_path=file_path,
            rows=rows,
            cols=cols,
            controls=controls
        )
    
    def run(self) -> None:
        """Start the application main loop."""
        self.logger.info("Starting MPLACE application main loop")
        self.views['main'].show()

def main():
    """Application entry point."""
    try:
        setup_logging()
        app = MPlaceApplication()
        app.run()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
