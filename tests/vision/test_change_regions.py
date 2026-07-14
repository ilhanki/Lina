from lina.vision.live.change_detector import _change_regions


def signature(size, cells, value=255):
    values = [0] * (size * size)
    for x, y in cells:
        values[y * size + x] = value
    return tuple(values)


def test_identical_and_small_noise_produce_no_boxes():
    base = signature(8, ())
    assert _change_regions(base, base, 8, 32) == ()
    assert _change_regions(base, signature(8, {(2, 2), (2, 3)}, 20), 8, 32) == ()


def test_adjacent_blocks_merge_and_coordinates_are_normalized():
    base = signature(8, ())
    regions = _change_regions(base, signature(8, {(2, 3), (3, 3), (2, 4), (3, 4)}), 8, 32)
    assert len(regions) == 1
    assert (regions[0].x, regions[0].y, regions[0].width, regions[0].height) == (0.25, 0.375, 0.25, 0.25)


def test_separate_regions_remain_separate_and_tiny_noise_is_filtered():
    base = signature(8, ())
    changed = {(0, 0), (1, 0), (6, 6), (7, 6), (4, 3)}
    regions = _change_regions(base, signature(8, changed), 8, 32)
    assert len(regions) == 2


def test_maximum_five_largest_regions_are_returned():
    size = 16
    cells = set()
    for index in range(7):
        x = (index % 4) * 4
        y = (index // 4) * 6
        cells.update({(x, y), (x + 1, y)})
    regions = _change_regions(signature(size, ()), signature(size, cells), size, 32)
    assert len(regions) == 5


def test_diagonal_cells_are_not_merged_without_an_edge_neighbor():
    base = signature(4, ())
    assert _change_regions(base, signature(4, {(0, 0), (1, 1)}), 4, 32) == ()
