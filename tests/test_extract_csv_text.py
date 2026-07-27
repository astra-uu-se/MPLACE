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
# Description: Integration tests for extract_csv_text, save_figure_to_path,
#              save_figures_to_pdf, path_truncate, read_csv_file error paths,
#              and multi-plate PharmBio to Plater conversion.
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.0
# Last Revision: July 2026
#

import os
import tempfile
import textwrap
import pytest
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure

from core.io_utils import (
    extract_csv_text,
    save_figure_to_path,
    save_figures_to_pdf,
    path_truncate,
    read_csv_file,
    convert_pharmbio_to_plater,
)
from models.constants import Validation
from models.dto import CSVConversionRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CSV_HEADER = "plateID,well,cmpdname,CONCuM,cmpdnum,VOLuL"

def _make_minizinc_output(*extra_lines, prefix="", suffix=""):
    """Wrap CSV header + data rows in realistic MiniZinc stdout."""
    data = "\n".join([
        "plate_1,A01,Drug1,0.1,Drug1_0.1,",
        "plate_1,B03,Drug1,0.3,Drug1_0.3,",
    ])
    return "\n".join(filter(None, [
        prefix,
        CSV_HEADER,
        data,
        *extra_lines,
        suffix,
    ]))

def _blank_figure():
    fig = Figure(figsize=(2, 2), dpi=72)
    fig.add_subplot(111)
    return fig


# ---------------------------------------------------------------------------
# 1. extract_csv_text
# ---------------------------------------------------------------------------

class TestExtractCsvText:

    def test_extracts_header_and_data_rows(self):
        text = _make_minizinc_output()
        lines = extract_csv_text(text)
        assert lines[0].strip() == CSV_HEADER
        assert len(lines) == 3   # header + 2 data rows

    def test_lines_end_with_newline(self):
        text = _make_minizinc_output()
        for line in extract_csv_text(text):
            assert line.endswith("\n")

    def test_stops_at_percent_comment(self):
        text = _make_minizinc_output("% solver stats", "this should not appear")
        lines = extract_csv_text(text)
        content = "".join(lines)
        assert "solver stats" not in content
        assert "should not appear" not in content

    def test_stops_at_dash_separator(self):
        text = _make_minizinc_output("----------", "after separator")
        lines = extract_csv_text(text)
        assert all("after separator" not in l for l in lines)

    def test_stops_at_criteria_function(self):
        text = _make_minizinc_output("criteria function value = 42")
        lines = extract_csv_text(text)
        assert all("criteria function" not in l for l in lines)

    def test_stops_at_finished(self):
        text = _make_minizinc_output("finished")
        lines = extract_csv_text(text)
        assert all("finished" not in l for l in lines)

    def test_end_marker_before_header_is_ignored(self):
        # An end marker that appears before the header must not set e <= s
        text = "----------\n" + _make_minizinc_output()
        lines = extract_csv_text(text)
        assert lines[0].strip() == CSV_HEADER

    def test_unsatisfiable_raises_runtime_error(self):
        text = "=====UNSATISFIABLE====="
        with pytest.raises(RuntimeError, match="unsatisfiable"):
            extract_csv_text(text)

    def test_missing_header_raises_value_error(self):
        text = "some output\nwithout the csv header\n"
        with pytest.raises(ValueError, match="CSV header not found"):
            extract_csv_text(text)

    def test_no_end_marker_reads_to_eof(self):
        # When there is no end marker, everything after the header is returned
        text = CSV_HEADER + "\nplate_1,A01,Drug1,0.1,Drug1_0.1,"
        lines = extract_csv_text(text)
        assert len(lines) == 2

    def test_multiple_solutions_uses_last_header(self):
        # MiniZinc can emit multiple solutions separated by ----------
        # Each solution starts with a fresh CSV header; the last one wins
        text = textwrap.dedent(f"""\
            {CSV_HEADER}
            plate_1,A01,Drug1,0.1,Drug1_0.1,
            ----------
            {CSV_HEADER}
            plate_1,B03,Drug1,0.3,Drug1_0.3,
            finished
        """)
        lines = extract_csv_text(text)
        assert lines[0].strip() == CSV_HEADER
        # Only the second solution's data row should be present
        content = "".join(lines)
        assert "B03" in content


# ---------------------------------------------------------------------------
# 2. save_figure_to_path
# ---------------------------------------------------------------------------

class TestSaveFigureToPath:

    def test_saves_png(self):
        fig = _blank_figure()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            save_figure_to_path(fig, path)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    def test_saves_pdf_single_figure(self):
        fig = _blank_figure()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            save_figure_to_path(fig, path)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
            # Rudimentary check: PDF magic bytes
            with open(path, "rb") as f:
                assert f.read(4) == b"%PDF"
        finally:
            os.unlink(path)

    def test_saves_pdf_with_material_scales(self):
        fig = _blank_figure()
        scales = [_blank_figure(), _blank_figure()]
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            save_figure_to_path(fig, path, material_scales=scales)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    def test_png_larger_than_empty_file(self):
        fig = _blank_figure()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            save_figure_to_path(fig, path)
            assert os.path.getsize(path) > 1000  # A real PNG, not a stub
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# 3. save_figures_to_pdf
# ---------------------------------------------------------------------------

class TestSaveFiguresToPdf:

    def test_saves_multi_figure_pdf(self):
        figures = [(_blank_figure(), f"plate_{i}.png") for i in range(3)]
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            save_figures_to_pdf(figures, path)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
            with open(path, "rb") as f:
                assert f.read(4) == b"%PDF"
        finally:
            os.unlink(path)

    def test_appends_material_scales(self):
        figures = [(_blank_figure(), "plate_1.png")]
        scales = [_blank_figure(), _blank_figure()]
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            save_figures_to_pdf(figures, path, material_scales=scales)
            # A PDF with 3 pages must be larger than one with 1 page
            size_with_scales = os.path.getsize(path)
        finally:
            os.unlink(path)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path_no_scales = f.name
        try:
            save_figures_to_pdf(figures, path_no_scales)
            size_without_scales = os.path.getsize(path_no_scales)
        finally:
            os.unlink(path_no_scales)

        assert size_with_scales > size_without_scales


# ---------------------------------------------------------------------------
# 4. path_truncate
# ---------------------------------------------------------------------------

class TestPathTruncate:

    def test_short_path_unchanged(self):
        short = "short/path.csv"
        assert short in path_truncate(short)
        assert not path_truncate(short).startswith(Validation.PATH_TRUNCATION_PREFIX)

    def test_long_path_gets_prefix(self):
        long_path = "a" * (Validation.PATH_DISPLAY_MAX_LENGTH + 10) + "/file.csv"
        result = path_truncate(long_path)
        assert result.startswith(Validation.PATH_TRUNCATION_PREFIX)

    def test_long_path_capped_at_max_length(self):
        long_path = "x" * 300 + "/file.csv"
        result = path_truncate(long_path)
        # prefix + tail, tail <= PATH_DISPLAY_MAX_LENGTH
        tail = result[len(Validation.PATH_TRUNCATION_PREFIX):]
        assert len(tail) <= Validation.PATH_DISPLAY_MAX_LENGTH

    def test_exactly_max_length_gets_prefix(self):
        exact = "b" * Validation.PATH_DISPLAY_MAX_LENGTH
        result = path_truncate(exact)
        assert result.startswith(Validation.PATH_TRUNCATION_PREFIX)


# ---------------------------------------------------------------------------
# 5. read_csv_file error paths
# ---------------------------------------------------------------------------

class TestReadCsvFileErrors:

    def test_missing_file_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            read_csv_file("/no/such/file.csv")

    def test_unrecognised_format_raises_value_error(self):
        content = "col1,col2,col3\nfoo,bar,baz\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            path = f.name
        try:
            with pytest.raises(ValueError):
                read_csv_file(path)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# 6. Multi-plate PharmBio → Plater conversion
# ---------------------------------------------------------------------------

class TestMultiPlateConversion:

    @pytest.fixture(scope="class")
    def two_plate_lines(self):
        """Synthetic PharmBio data with two plates, 2 wells each."""
        return [
            "plate_1,A01,Drug1,0.1,Drug1_0.1,\n",
            "plate_1,B03,Drug1,0.3,Drug1_0.3,\n",
            "plate_2,A01,Drug2,1.0,Drug2_1.0,\n",
            "plate_2,C05,Drug2,2.0,Drug2_2.0,\n",
        ]

    def test_returns_two_strings(self, two_plate_lines):
        result = convert_pharmbio_to_plater(
            CSVConversionRequest(csv_lines=two_plate_lines, rows="16", cols="24")
        )
        assert len(result) == 2
        assert all(isinstance(r, str) for r in result)

    def test_each_result_is_parseable(self, two_plate_lines):
        from core.io_utils import scan_csv_plater_matrices
        results = convert_pharmbio_to_plater(
            CSVConversionRequest(csv_lines=two_plate_lines, rows="16", cols="24")
        )
        for plater_text in results:
            lines = [l + "\n" for l in plater_text.splitlines()]
            rows, cols, drugs, concs = scan_csv_plater_matrices(lines)
            assert rows == 16

    def test_plate1_preserves_well_count(self, two_plate_lines):
        from core.io_utils import scan_csv_plater_matrices
        results = convert_pharmbio_to_plater(
            CSVConversionRequest(csv_lines=two_plate_lines, rows="16", cols="24")
        )
        lines = [l + "\n" for l in results[0].splitlines()]
        _, _, drugs, _ = scan_csv_plater_matrices(lines)
        non_empty = sum(1 for row in drugs for cell in row[1:] if cell != "")
        assert non_empty == 2

    def test_plate2_preserves_well_count(self, two_plate_lines):
        from core.io_utils import scan_csv_plater_matrices
        results = convert_pharmbio_to_plater(
            CSVConversionRequest(csv_lines=two_plate_lines, rows="16", cols="24")
        )
        lines = [l + "\n" for l in results[1].splitlines()]
        _, _, drugs, _ = scan_csv_plater_matrices(lines)
        non_empty = sum(1 for row in drugs for cell in row[1:] if cell != "")
        assert non_empty == 2