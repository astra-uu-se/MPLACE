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

import pytest
from core.io_utils import scan_csv_plater_matrices, convert_to_pharmbio_format


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plater_lines(drug_rows, conc_rows, cols=None, separator=True,
                  bad_drug_header=False, bad_col_count=False):
    """Build a minimal valid Plater file as a list of raw text lines.

    Each row in *drug_rows* / *conc_rows* is a list of cell strings
    (excluding the leading row-label column).  *cols* defaults to the
    width of the first row.
    """
    if cols is None:
        cols = len(drug_rows[0])
    header_indices = list(range(1, cols + 1))
    if bad_drug_header:
        header_indices = list(reversed(header_indices))

    lines = []
    lines.append("Drug," + ",".join(str(i) for i in header_indices) + "\n")
    for i, row in enumerate(drug_rows):
        label = chr(ord("A") + i)
        cells = row if not bad_col_count else row + ["EXTRA"]
        lines.append(label + "," + ",".join(cells) + "\n")

    if separator:
        # Separator is a line of *cols* empty fields (cols-1 commas).
        # Must match the column count of the surrounding matrices.
        lines.append("," * cols + "\n")

    lines.append("Concentration," + ",".join(str(i) for i in range(1, cols + 1)) + "\n")
    for i, row in enumerate(conc_rows):
        label = chr(ord("A") + i)
        lines.append(label + "," + ",".join(row) + "\n")

    return lines


# ---------------------------------------------------------------------------
# scan_csv_plater_matrices — happy path
# ---------------------------------------------------------------------------

class TestScanPlaterMatricesValid:
    def test_returns_correct_row_count(self):
        lines = _plater_lines([["DrugA", "DrugB"], ["DrugC", ""]], [["0.1", "1.0"], ["", "0.5"]])
        rows, _cols, _d, _c = scan_csv_plater_matrices(lines)
        assert rows == 2

    def test_returns_correct_col_count(self):
        # cols == total CSV column count including the row-label column
        lines = _plater_lines([["DrugA", "DrugB"]], [["0.1", "0.2"]])
        _rows, cols, _d, _c = scan_csv_plater_matrices(lines)
        assert cols == 3  # label col + 2 data cols

    def test_returns_correct_drug_values(self):
        lines = _plater_lines([["DrugA", "DrugB"]], [["0.1", "0.2"]])
        _r, _c, drugs, _concs = scan_csv_plater_matrices(lines)
        assert drugs[0][1] == "DrugA"
        assert drugs[0][2] == "DrugB"

    def test_returns_correct_concentration_values(self):
        lines = _plater_lines([["DrugA", "DrugB"]], [["0.1", "0.5"]])
        _r, _c, _d, concs = scan_csv_plater_matrices(lines)
        assert concs[0][1] == "0.1"
        assert concs[0][2] == "0.5"

    def test_single_row_single_col(self):
        lines = _plater_lines([["DrugX"]], [["99.0"]], cols=1)
        rows, cols, drugs, concs = scan_csv_plater_matrices(lines)
        assert rows == 1
        assert cols == 2
        assert drugs[0][1] == "DrugX"
        assert concs[0][1] == "99.0"


# ---------------------------------------------------------------------------
# scan_csv_plater_matrices — error paths
# ---------------------------------------------------------------------------

class TestScanPlaterMatricesErrors:
    def test_mismatched_row_counts_raises_value_error(self):
        """Drug matrix has 2 rows, concentration matrix only 1.

        The real bug: *rows* is already an int (= len(drugs_matrix)), so
        calling len(rows) in the error message raised TypeError instead of
        ValueError.  This test is the regression guard.
        """
        lines = [
            "Drug,1,2\n",
            "A,DrugA,DrugB\n",
            "B,DrugC,\n",
            ",,\n",             # separator: cols=3, so 2 commas = 3 empty fields
            "Concentration,1,2\n",
            "A,0.1,0.2\n",
        ]
        with pytest.raises(ValueError, match="mismatched"):
            scan_csv_plater_matrices(lines)

    def test_missing_concentration_matrix_raises(self):
        lines = ["Drug,1,2\n", "A,DrugA,DrugB\n"]
        with pytest.raises(ValueError):
            scan_csv_plater_matrices(lines)

    def test_missing_drug_matrix_raises(self):
        lines = ["Concentration,1,2\n", "A,0.1,0.2\n"]
        with pytest.raises(ValueError):
            scan_csv_plater_matrices(lines)

    def test_wrong_column_header_order_raises(self):
        lines = _plater_lines([["DrugA", "DrugB"]], [["0.1", "0.2"]], bad_drug_header=True)
        with pytest.raises(ValueError, match="incorrect order"):
            scan_csv_plater_matrices(lines)

    def test_inconsistent_column_count_raises(self):
        lines = _plater_lines([["DrugA", "DrugB"]], [["0.1", "0.2"]], bad_col_count=True)
        with pytest.raises(ValueError):
            scan_csv_plater_matrices(lines)

    def test_duplicate_drug_matrix_raises(self):
        lines = [
            "Drug,1\n", "A,DrugA\n",
            "Drug,1\n", "A,DrugB\n",
            "Concentration,1\n", "A,0.1\n",
        ]
        with pytest.raises(ValueError, match="too many"):
            scan_csv_plater_matrices(lines)

    def test_no_separator_requires_valid_format(self):
        """The parser requires a blank separator between the two matrices.
        Without it, the Concentration header is consumed as a drug data row,
        resulting in a row-count mismatch (drugs=3, concs=0) and a ValueError.
        """
        lines = _plater_lines([["DrugA", "DrugB"]], [["0.1", "0.2"]], separator=False)
        with pytest.raises(ValueError):
            scan_csv_plater_matrices(lines)


# ---------------------------------------------------------------------------
# convert_to_pharmbio_format — format detection
# ---------------------------------------------------------------------------

class TestConvertToPharmbioFormat:
    def test_pharmbio_header_strips_header_row(self):
        lines = [
            "plateID,well,cmpdname,CONCuM,cmpdnum,VOLuL\n",
            "plate_1,A01,DrugA,0.1,DrugA_0.1,\n",
            "plate_1,A02,DrugB,1.0,DrugB_1.0,\n",
        ]
        result = convert_to_pharmbio_format(lines)
        assert len(result) == 2
        assert result[0].startswith("plate_1")

    def test_pharmbio_data_rows_are_unchanged(self):
        data_row = "plate_1,B03,MyDrug,5.0,MyDrug_5.0,\n"
        lines = ["plateID,well,cmpdname,CONCuM,cmpdnum,VOLuL\n", data_row]
        result = convert_to_pharmbio_format(lines)
        assert result[0] == data_row

    def test_plater_format_converted_contains_drug(self):
        lines = _plater_lines([["DrugA", ""]], [["0.5", ""]])
        result = convert_to_pharmbio_format(lines)
        assert any("DrugA" in line for line in result)

    def test_plater_format_converted_contains_concentration(self):
        lines = _plater_lines([["DrugA", ""]], [["0.5", ""]])
        result = convert_to_pharmbio_format(lines)
        assert any("0.5" in line for line in result)

    def test_unrecognized_format_raises_value_error(self):
        lines = ["completely,wrong,format\n", "garbage,data\n"]
        with pytest.raises(ValueError):
            convert_to_pharmbio_format(lines)
