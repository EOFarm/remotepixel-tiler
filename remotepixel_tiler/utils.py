"""Utility functions."""

from typing import Tuple

import numpy

from rio_color.operations import parse_operations
from rio_color.utils import scale_dtype, to_math_type

from rio_tiler.utils import linear_rescale, _chunks


def _postprocess(
    tile: numpy.ndarray,
    mask: numpy.ndarray,
    rescale: str = None,
    color_formula: str = None,
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    if rescale:
        rescale_arr = list(map(float, rescale.split(",")))
        rescale_arr = list(_chunks(rescale_arr, 2))
        if len(rescale_arr) != tile.shape[0]:
            rescale_arr = ((rescale_arr[0]),) * tile.shape[0]
        for bdx in range(tile.shape[0]):
            tile[bdx] = numpy.where(
                mask,
                linear_rescale(
                    tile[bdx], in_range=rescale_arr[bdx], out_range=[0, 255]
                ),
                0,
            )
        tile = tile.astype(numpy.uint8)

    if color_formula:
        # make sure one last time we don't have
        # negative value before applying color formula
        tile[tile < 0] = 0
        for ops in parse_operations(color_formula):
            tile = scale_dtype(ops(to_math_type(tile)), numpy.uint8)

    return tile, mask
