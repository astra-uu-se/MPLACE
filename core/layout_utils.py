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
# Description:  Various supplementary utilities related to visualization of layouts
#
# Authors: Ramiz GINDULLIN (ramiz.gindullin@it.uu.se)
# Version: 1.3.3
# Last Revision: March 2026
#

import logging

from functools import lru_cache
from typing import List, Sequence, Union, Dict, Tuple

from models.constants import Alphabet, Performance, Visualization


# Configure logging for utility module
logger = logging.getLogger(__name__)


@lru_cache(maxsize=Performance.COORDINATE_CACHE_SIZE)
def transform_coordinate(well: str) -> List[int]:
    """Transform coordinates from standard csv-file format.
    
    Args:
        well: Well coordinate (e.g., 'A1', 'B3')
        
    Returns:
        List of [row, col] coordinates (0-indexed)
        
    Example:
        transform_coordinate('A1') returns [0, 0]
        transform_coordinate('B3') returns [1, 2]
        transform_coordinate('Aa14')returns [26,14]
    
    Note:
        This function is cached for performance when processing repeated well coordinates.
    """
    row = 0
    for i in range(len(well)):
        symbol = well[i]
        if symbol in Alphabet.LETTERS_CAPITAL:
            row += Alphabet.LETTERS_CAPITAL.index(symbol)
        elif symbol in Alphabet.LETTERS_LOWERCASE:
            row = Alphabet.LETTERS_LOWERCASE.index(symbol) + (row + 1) * len(Alphabet.LETTERS_LOWERCASE)
        else:
            col = int(well[i:]) - 1
            logger.debug(f"Coordinate transform: {well} -> [{row}, {col}]")
            return [row, col]
    error_msg = f'Coordinates {well} can not be transformed.'
    logger.debug(error_msg)
    raise ValueError(error_msg)


@lru_cache(maxsize=Performance.COORDINATE_CACHE_SIZE)
def transform_index(index: int) -> str:
    """Convert a numerical index to a corresponding letter.
    
    Example:
        transform_index(0) returns 'A'
        transform_index(27) returns 'Ab'
    """
    if index < len(Alphabet.LETTERS_CAPITAL):
        return Alphabet.LETTERS_CAPITAL[index]
    return Alphabet.LETTERS_CAPITAL[index//len(Alphabet.LETTERS_CAPITAL)-1] + Alphabet.LETTERS_LOWERCASE[index%len(Alphabet.LETTERS_CAPITAL)]


def transform_concentrations_to_alphas(concentration_list: Sequence[Union[str, float, int]]) -> Dict[Union[str, float, int], float]:
    """Transform concentration list to alpha values for visualization.
    
    Args:
        concentration_list: List of concentration values
        
    Returns:
        Dictionary mapping concentrations to alpha values (0.3 to 1.0)
        
    Examples:
        - Single concentration: returns {concentration: 1.0}
        - Multiple concentrations: returns evenly spaced alpha values
    """
    min_alpha = Visualization.ALPHA_MIN
    max_alpha = Visualization.ALPHA_MAX
    num_alpha = len(concentration_list)
    if num_alpha == 1:
        return {concentration_list[0]: 1}
    alphas = {}
    for i in range(len(concentration_list)):
        alphas[concentration_list[i]] = min(
            [1, min_alpha + (max_alpha - min_alpha) * i / (num_alpha - 1)])
    logger.debug(f"Alpha mapping generated for {num_alpha} concentrations")
    return alphas


def to_number_if_possible(value: str) -> Union[int, float, str]:
    """Convert string to number if possible, otherwise return original value.
    
    Args:
        value: String value to convert
        
    Returns:
        Integer, float, or original string value
    """
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def find_all_plates_concentrations(text_array: List[str]) -> Tuple[Dict[str,List[str]],Dict[str, Union[int, float, str]]]:
    """Scans the content of CSV file and returns the list of plate names and concentrations for each material
    
    Args:
        text_array: List of CSV data lines (excluding header), each formatted as
                    'plateID,well,cmpdname,CONCuM,cmpdnum,VOLuL'
        
    Returns:
        Tuple of:
              - layouts_dict: {plateID: list of [well, material, conc, ...] rows}
              - concentrations_list: {material_name: sorted list of unique concentration values}
    """
    layouts_dict: Dict[str, List[List[str]]] = {}
    concentrations_list: Dict[str, List[Union[str, float, int]]] = {}
    
    for line in text_array:
        if line == '\n':  # happens on Windows machines
            continue
        array = line.strip().split(',')
        if array[0] in layouts_dict:
            layouts_dict[array[0]].append(array[1:])
        else:
            layouts_dict[array[0]] = [array[1:]]

        if array[2] in concentrations_list:
            if to_number_if_possible(array[3]) not in concentrations_list[array[2]]:
                concentrations_list[array[2]].append(to_number_if_possible(array[3]))
        else:
            concentrations_list[array[2]] = [to_number_if_possible(array[3])]
    
    # Sort concentrations numerically (or lexicographically for string values)
    for material in concentrations_list:
        concentrations_list[material].sort(
            key=lambda x: (isinstance(x, str), x)
        )
    
    return layouts_dict, concentrations_list