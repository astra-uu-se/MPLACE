# Copyright 2025 Ramiz Gindullin.
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
# Description: Validation tests for Stage 2 controllers.
# Run this to verify controllers are working correctly.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.2
# Last Revision: December 2025
#

import os
from models.application_state import ApplicationState
from models.dzn_data import DznFormData
from controllers.main_controller import MainController
from controllers.dzn_controller import DznController
from controllers.csv_controller import CsvController


def test_main_controller():
    """Test MainController operations."""
    print("Testing MainController...")
    
    # Create state and controller
    state = ApplicationState()
    controller = MainController(state)
    
    # Test initial state
    assert not controller.can_run_model()
    assert not controller.can_visualize()
    
    # Test state updates
    controller.state.dzn_file_path = 'test.dzn'
    assert controller.can_run_model()
    
    controller.state.csv_file_path = 'test.csv'
    assert controller.can_visualize()
    
    # Test reset
    controller.reset_state()
    assert not controller.can_run_model()
    
    # Test recent files
    controller.state.add_recent_dzn('file1.dzn')
    controller.state.add_recent_dzn('file2.dzn')
    recent = controller.get_recent_dzn_files()
    assert len(recent) == 2
    assert recent[0] == 'file2.dzn'
    
    print("✓ MainController tests passed")


def test_dzn_controller():
    """Test DznController validation."""
    print("Testing DznController...")
    
    controller = DznController()
    
    # Test valid form data - using STRINGS for dicts like UI does
    valid_data = DznFormData(
        num_rows='16',
        num_cols='24',
        inner_empty_edge=False,
        size_empty_edge='0',
        size_corner_empty_wells='0',
        horizontal_cell_lines='[]',
        vertical_cell_lines='[]',
        flag_allow_empty_wells=True,
        flag_concentrations_on_different_rows=False,
        flag_concentrations_on_different_columns=False,
        flag_replicates_on_different_plates=False,
        flag_replicates_on_same_plate=True,
        compounds_dict="{'Drug1': [5, '0.1', '0.3']}",  # STRING, not dict
        controls_dict="{'pos': [8, '100']}"              # STRING, not dict
    )
    
    errors = controller.validate_form_data(valid_data)
    assert len(errors) == 0, f"Expected no errors, got: {errors}"
    
    # Test invalid dimensions
    invalid_data = DznFormData(
        num_rows='0',  # Invalid
        num_cols='24',
        inner_empty_edge=False,
        size_empty_edge='0',
        size_corner_empty_wells='0',
        horizontal_cell_lines='[]',
        vertical_cell_lines='[]',
        flag_allow_empty_wells=True,
        flag_concentrations_on_different_rows=False,
        flag_concentrations_on_different_columns=False,
        flag_replicates_on_different_plates=False,
        flag_replicates_on_same_plate=False,
        compounds_dict="{}",   # Empty but valid string
        controls_dict="{}"     # Empty but valid string
    )
    
    errors = controller.validate_form_data(invalid_data)
    assert len(errors) > 0, "Expected validation errors"
    
    print("✓ DznController tests passed")


def test_csv_controller():
    """Test CsvController validation."""
    print("Testing CsvController...")
    
    controller = CsvController()
    
    # Test CSV validation
    valid_lines = ['header1,header2', 'data1,data2']
    assert controller.validate_csv_lines(valid_lines)
    
    # Test empty lines
    assert not controller.validate_csv_lines([])
    
    # Test insufficient rows
    assert not controller.validate_csv_lines(['header only'])
    
    print("✓ CsvController tests passed")


if __name__ == '__main__':
    print("\n=== Running Stage 2 Controller Validation Tests ===\n")
    
    try:
        test_main_controller()
        test_dzn_controller()
        test_csv_controller()
        
        print("\n=== All Stage 2 Tests Passed! ===")
        print("\nYour controllers are working correctly and can be used in Stage 3.")
        print("Key benefits achieved:")
        print("  ✓ No Tkinter dependencies in controllers")
        print("  ✓ Business logic separated from UI")
        print("  ✓ Fully testable without GUI")
        print("  ✓ Clean separation of concerns")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
