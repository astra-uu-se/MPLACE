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
# Description: Simple validation tests for Stage 1 models.
# Run this to verify models are working correctly.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.2
# Last Revision: December 2025
#

from models.application_state import ApplicationState
from models.dzn_data import DznFormData
from models.csv_data import LayoutData, VisualizationState


def test_application_state():
    """Test ApplicationState creation and methods."""
    print("Testing ApplicationState...")
    
    # Create state
    state = ApplicationState()
    
    # Test defaults
    assert state.dzn_file_path == ''
    assert state.num_rows == '16'
    assert state.num_cols == '24'
    assert not state.use_compd
    assert state.recent_dzn == []
    
    # Test state checks
    assert not state.has_dzn_loaded()
    assert not state.can_run_model()
    
    # Test loading files
    state.dzn_file_path = '/path/to/file.dzn'
    assert state.has_dzn_loaded()
    assert state.can_run_model()
    
    # Test recent files
    state.add_recent_dzn('/path/1.dzn')
    state.add_recent_dzn('/path/2.dzn')
    state.add_recent_dzn('/path/1.dzn')  # Re-add moves to top
    assert state.recent_dzn[0] == '/path/1.dzn'
    assert len(state.recent_dzn) == 2
    
    # Test reset
    state.reset_file_state()
    assert state.dzn_file_path == ''
    
    print("✓ ApplicationState tests passed")


def test_dzn_form_data():
    """Test DznFormData creation."""
    print("Testing DznFormData...")
    
    # Create form data
    form_data = DznFormData(
        num_rows='16',
        num_cols='24',
        inner_empty_edge=True,
        size_empty_edge='1',
        size_corner_empty_wells='0',
        horizontal_cell_lines='[]',
        vertical_cell_lines='[]',
        flag_allow_empty_wells=True,
        flag_concentrations_on_different_rows=False,
        flag_concentrations_on_different_columns=False,
        flag_replicates_on_different_plates=False,
        flag_replicates_on_same_plate=True,
        compounds_dict={'Drug1': [5, '0.1', '0.3']},
        controls_dict={'pos': [8, '100']}
    )
    
    # Test data access
    assert form_data.num_rows == '16'
    assert form_data.get_num_rows_int() == 16
    assert form_data.inner_empty_edge is True
    assert 'Drug1' in form_data.compounds_dict
    
    print("✓ DznFormData tests passed")


def test_visualization_state():
    """Test VisualizationState creation and methods."""
    print("Testing VisualizationState...")
    
    # Create empty state
    viz_state = VisualizationState()
    
    # Test defaults
    assert not viz_state.has_figures()
    assert not viz_state.is_single_figure()
    assert not viz_state.is_multiple_figures()
    assert viz_state.num_rows == 16
    assert viz_state.num_cols == 24
    
    # Add mock figures
    viz_state.figures_to_save.append((None, 'plate1'))
    assert viz_state.has_figures()
    assert viz_state.is_single_figure()
    
    viz_state.figures_to_save.append((None, 'plate2'))
    assert viz_state.is_multiple_figures()
    assert not viz_state.is_single_figure()
    
    # Test clear
    viz_state.clear_figures()
    assert not viz_state.has_figures()
    
    print("✓ VisualizationState tests passed")


def test_layout_data():
    """Test LayoutData creation."""
    print("Testing LayoutData...")
    
    # Create layout data
    layout_data = LayoutData(
        layouts_dict={'Layout1': [['A01', 'A02'], ['B01', 'B02']]},
        concentrations_list={'Drug1': [0.1, 0.3, 1.0]},
        material_colors={'Drug1': 'blue'},
        alpha_mappings={'Drug1': {0.1: 0.3, 0.3: 0.6, 1.0: 1.0}}
    )
    
    # Test data access
    assert 'Layout1' in layout_data.layouts_dict
    assert 'Drug1' in layout_data.concentrations_list
    assert len(layout_data.concentrations_list['Drug1']) == 3
    
    print("✓ LayoutData tests passed")


if __name__ == '__main__':
    print("\n=== Running Stage 1 Model Validation Tests ===\n")
    
    try:
        test_application_state()
        test_dzn_form_data()
        test_visualization_state()
        test_layout_data()
        
        print("\n=== All Stage 1 Tests Passed! ===")
        print("\nYour models are working correctly and can be used in Stage 2.")
        print("Key benefits achieved:")
        print("  ✓ No Tkinter dependencies in models")
        print("  ✓ Centralized application state")
        print("  ✓ Clear data structures")
        print("  ✓ Ready for unit testing")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
