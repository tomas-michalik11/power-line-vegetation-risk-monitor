import pytest
from shapely.geometry import LineString
from src.corridor import split_line


def test_split_exact():
    line = LineString([(0, 0), (300, 0)])
    result = split_line(line, 100)
    assert len(result) == 3
    assert result[0].length == pytest.approx(100.0)


def test_split_remainder():
    line = LineString([(0, 0), (250, 0)])
    result = split_line(line, 100)
    assert len(result) == 3
    assert result[-1].length == pytest.approx(50.0)
