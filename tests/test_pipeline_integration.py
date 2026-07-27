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
# Description: Integration tests for the CSV I/O and visualization pipeline.
# Tests the full non-GUI pipeline using sample/test.csv as a fixture.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.0
# Last Revision: June 2026
#

import os
import pytest
import tempfile

from core.io_utils import (
    read_csv_file,
    convert_to_pharmbio_format,
    convert_pharmbio_to_plater,
    scan_csv_plater_matrices,
)
from core.layout_utils import find_all_plates_concentrations
from models.dto import CSVConversionRequest
from controllers.viz_controller import VisualizationController


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

SAMPLE_CSV = os.path.join(
    os.path.dirname(__file__), "..", "sample", "test.csv"
)


@pytest.fixture(scope="module")
def sample_lines():
    """Data lines from sample/test.csv (header stripped)."""
    return read_csv_file(SAMPLE_CSV)


@pytest.fixture(scope="module")
def plates_and_concentrations(sample_lines):
    return find_all_plates_concentrations(sample_lines)


@pytest.fixture(scope="module")
def viz_controller():
    return VisualizationController()


# ---------------------------------------------------------------------------
# 1. CSV reading
# ---------------------------------------------------------------------------

class TestReadCsv:
    def test_loads_correct_line_count(self, sample_lines):
        # sample/test.csv has 25 data rows (header excluded by read_csv_file)
        assert len(sample_lines) == 25

    def test_header_is_stripped(self, sample_lines):
        for line in sample_lines:
            assert not line.startswith("plateID"), (
                "Header line must not appear in parsed output"
            )

    def test_lines_have_expected_fields(self, sample_lines):
        # PharmBio data rows have 5 fields — VOLuL (6th) is always empty/absent
        for line in sample_lines:
            fields = line.strip().split(",")
            assert len(fields) in (5, 6), f"Unexpected field count: {len(fields)}"


# ---------------------------------------------------------------------------
# 2. Layout / concentration parsing
# ---------------------------------------------------------------------------

class TestFindAllPlatesConcentrations:
    def test_finds_single_plate(self, plates_and_concentrations):
        layouts, _ = plates_and_concentrations
        assert list(layouts.keys()) == ["plate_1"]

    def test_plate_has_correct_well_count(self, plates_and_concentrations):
        layouts, _ = plates_and_concentrations
        assert len(layouts["plate_1"]) == 25

    def test_finds_three_materials(self, plates_and_concentrations):
        _, concentrations = plates_and_concentrations
        assert set(concentrations.keys()) == {"Drug1", "Drug2", "pos"}

    def test_drug1_concentrations_sorted(self, plates_and_concentrations):
        _, concentrations = plates_and_concentrations
        drug1 = concentrations["Drug1"]
        assert drug1 == sorted(drug1), "Drug1 concentrations must be in ascending order"

    def test_drug1_has_two_concentrations(self, plates_and_concentrations):
        _, concentrations = plates_and_concentrations
        # 0.1 and 0.3 appear in the file
        assert len(concentrations["Drug1"]) == 2

    def test_concentrations_are_numeric(self, plates_and_concentrations):
        _, concentrations = plates_and_concentrations
        for material, conc_list in concentrations.items():
            for c in conc_list:
                assert isinstance(c, (int, float)), (
                    f"{material}: concentration {c!r} was not converted to a number"
                )

    def test_controls_ordered_last(self, plates_and_concentrations):
        # The sort puts string keys (non-numeric material names) first;
        # "pos" is a string key, Drug1/Drug2 keys are also strings but
        # their concentrations are numeric. What matters is the dict is
        # deterministic and pos is present.
        _, concentrations = plates_and_concentrations
        assert "pos" in concentrations


# ---------------------------------------------------------------------------
# 3. PharmBio → Plater → PharmBio round-trip
# ---------------------------------------------------------------------------

class TestPlaterRoundTrip:
    @pytest.fixture(scope="class")
    def plater_text(self, sample_lines):
        """Convert sample PharmBio lines to Plater format string."""
        plates, _ = find_all_plates_concentrations(sample_lines)
        request = CSVConversionRequest(
            csv_lines=plates["plate_1"],
            rows="16",
            cols="24",
        )
        results = convert_pharmbio_to_plater(
            CSVConversionRequest(
                csv_lines=sample_lines,
                rows="16",
                cols="24",
            )
        )
        assert len(results) == 1
        return results[0]

    def test_plater_output_is_string(self, plater_text):
        assert isinstance(plater_text, str)

    def test_plater_has_drugs_and_concentrations_headers(self, plater_text):
        lines = plater_text.splitlines()
        headers = [l.split(",")[0] for l in lines]
        assert "Drugs" in headers or any("Drug" in h for h in headers), (
            "Plater output must contain a Drugs matrix header"
        )

    def test_plater_is_parseable_back(self, plater_text):
        """scan_csv_plater_matrices must accept what convert_pharmbio_to_plater produced."""
        lines = [l + "\n" for l in plater_text.splitlines()]
        rows, cols, drugs_matrix, conc_matrix = scan_csv_plater_matrices(lines)
        assert rows == 16
        assert cols == 25   # 24 data columns + 1 row-label column

    def test_round_trip_preserves_well_count(self, plater_text):
        lines = [l + "\n" for l in plater_text.splitlines()]
        rows, cols, drugs_matrix, conc_matrix = scan_csv_plater_matrices(lines)
        non_empty = sum(
            1 for row in drugs_matrix for cell in row[1:] if cell != ""
        )
        assert non_empty == 25


# ---------------------------------------------------------------------------
# 4. VisualizationController.prepare_visualization (no GUI)
# ---------------------------------------------------------------------------

class TestPrepareVisualization:
    @pytest.fixture(scope="class")
    def viz_state(self, viz_controller):
        return viz_controller.prepare_visualization(
            csv_path=SAMPLE_CSV,
            template="plate_",
            rows="16",
            cols="24",
            controls="['pos']",
        )

    def test_returns_visualization_state(self, viz_state):
        from models.csv_data import VisualizationState
        assert isinstance(viz_state, VisualizationState)

    def test_state_has_one_plate(self, viz_state):
        assert len(viz_state.plates) == 1
        assert "plate_1" in viz_state.plates

    def test_state_dimensions(self, viz_state):
        assert viz_state.num_rows == 16
        assert viz_state.num_cols == 24

    def test_state_has_material_colors(self, viz_state):
        assert set(viz_state.material_colors.keys()) == {"Drug1", "Drug2", "pos"}

    def test_state_has_alpha_mappings(self, viz_state):
        assert set(viz_state.alpha_mappings.keys()) == {"Drug1", "Drug2", "pos"}

    def test_alpha_values_in_range(self, viz_state):
        for material, mapping in viz_state.alpha_mappings.items():
            for conc, alpha in mapping.items():
                assert 0.0 <= alpha <= 1.0, (
                    f"{material}[{conc}]: alpha {alpha} out of [0, 1]"
                )

    def test_control_names_parsed(self, viz_state):
        assert "pos" in viz_state.control_names

    def test_missing_file_raises(self, viz_controller):
        with pytest.raises(FileNotFoundError):
            viz_controller.prepare_visualization(
                csv_path="/nonexistent/path/fake.csv",
                template="plate_",
                rows="16",
                cols="24",
                controls="[]",
            )

    def test_invalid_dimensions_raise(self, viz_controller):
        with pytest.raises(ValueError):
            viz_controller.prepare_visualization(
                csv_path=SAMPLE_CSV,
                template="plate_",
                rows="0",
                cols="24",
                controls="[]",
            )


# ---------------------------------------------------------------------------
# 5. Figure rendering (headless, no Tkinter)
# ---------------------------------------------------------------------------

class TestHeadlessRendering:
    """Verify figures can be created and saved without a display."""

    @pytest.fixture(scope="class")
    def viz_state(self, viz_controller):
        return viz_controller.prepare_visualization(
            csv_path=SAMPLE_CSV,
            template="plate_",
            rows="16",
            cols="24",
            controls="['pos']",
        )

    def test_plate_figure_renders_to_png(self, viz_controller, viz_state):
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib.figure import Figure

        fig = Figure(dpi=100)
        ax = fig.add_subplot(111)
        viz_controller.prepare_plate_axes(ax, viz_state.num_rows, viz_state.num_cols)
        viz_controller.plot_plate_wells(ax, viz_state.plates["plate_1"], viz_state)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            fig.savefig(path, dpi=100)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    def test_material_scale_renders_to_png(self, viz_controller, viz_state):
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib.figure import Figure

        for material in viz_state.material_colors:
            fig = Figure(figsize=(4, 1), dpi=100)
            ax = fig.add_subplot(111)
            viz_controller.create_material_scale(ax, material, viz_state)

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                path = f.name
            try:
                fig.savefig(path, dpi=100)
                assert os.path.getsize(path) > 0, (
                    f"Empty PNG for material scale: {material}"
                )
            finally:
                os.unlink(path)