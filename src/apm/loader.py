"""Lecture YAML sûre (NFR-04) : pas de float ni de date implicites, clés dupliquées
refusées, numéro de ligne mémorisé pour chaque mapping et séquence."""
from __future__ import annotations

from pathlib import Path

import yaml

_DROPPED = {"tag:yaml.org,2002:float", "tag:yaml.org,2002:timestamp"}


class YamlError(Exception):
    def __init__(self, message: str, line: int | None = None):
        super().__init__(message)
        self.line = line


class _Loader(yaml.SafeLoader):
    pass


_Loader.yaml_implicit_resolvers = {
    first: [(tag, rx) for tag, rx in resolvers if tag not in _DROPPED]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def _construct_map(loader: _Loader, node: yaml.MappingNode):
    data: dict = {}
    loader.lines[id(data)] = node.start_mark.line + 1
    yield data
    seen: set = set()
    for key_node, _ in node.value:
        if isinstance(key_node, yaml.ScalarNode):
            if key_node.value in seen:
                raise YamlError(f"clé dupliquée « {key_node.value} »", key_node.start_mark.line + 1)
            seen.add(key_node.value)
    data.update(loader.construct_mapping(node))


def _construct_seq(loader: _Loader, node: yaml.SequenceNode):
    data: list = []
    loader.lines[id(data)] = node.start_mark.line + 1
    yield data
    data.extend(loader.construct_sequence(node))


_Loader.add_constructor("tag:yaml.org,2002:map", _construct_map)
_Loader.add_constructor("tag:yaml.org,2002:seq", _construct_seq)


def load_yaml(path: Path) -> tuple[object, dict[int, int]]:
    """Retourne (données, {id(objet): ligne}). Lève YamlError."""
    text = path.read_text(encoding="utf-8")
    loader = _Loader(text)
    loader.lines = {}
    try:
        data = loader.get_single_data()
    except YamlError:
        raise
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        raise YamlError(str(getattr(exc, "problem", None) or exc), mark.line + 1 if mark else None) from exc
    finally:
        loader.dispose()
    return data, loader.lines
