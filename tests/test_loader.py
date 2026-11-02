from apm.loader import YamlError, load_yaml
import pytest


def test_no_implicit_float_nor_date(tmp_path):
    p = tmp_path / "x.yaml"
    p.write_text("version: 2026.10\ndate: 2026-11-02\nn: 3\n")
    data, lines = load_yaml(p)
    assert data == {"version": "2026.10", "date": "2026-11-02", "n": 3}
    assert lines[id(data)] == 1


def test_duplicate_key_is_rejected_with_line(tmp_path):
    p = tmp_path / "x.yaml"
    p.write_text("a: 1\nb: 2\na: 3\n")
    with pytest.raises(YamlError) as exc:
        load_yaml(p)
    assert exc.value.line == 3
