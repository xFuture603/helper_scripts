"""Tests for the yaml_deduplicate script."""
# pylint: disable=redefined-outer-name,import-error
import tempfile
from pathlib import Path

import pytest
import yaml

from yaml_deduplicate.yaml_deduplicate import YAMLProcessor


@pytest.fixture
def yaml_processor():
    """Returns a YAMLProcessor instance."""
    return YAMLProcessor(file_list=[])


@pytest.fixture
def temp_yaml_files():
    """Creates temporary YAML files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        file1_path = dir_path / "file1.yaml"
        file2_path = dir_path / "file2.yaml"
        common_path = dir_path / "common.yaml"

        data1 = {"a": 1, "b": {"c": 2, "d": 3}, "e": [1, 2]}
        data2 = {"a": 1, "b": {"c": 2, "d": 4}, "f": 5}

        with open(file1_path, "w", encoding="utf-8") as f:
            yaml.dump(data1, f)
        with open(file2_path, "w", encoding="utf-8") as f:
            yaml.dump(data2, f)

        yield file1_path, file2_path, common_path


def test_intersect_dicts(yaml_processor):
    """Tests the intersect_dicts function."""
    dict1 = {"a": 1, "b": {"c": 2, "d": 3}}
    dict2 = {"a": 1, "b": {"c": 2, "d": 4}}
    dict3 = {"a": 1, "b": {"c": 2}}
    result = yaml_processor.intersect_dicts([dict1, dict2, dict3])
    assert result == {"a": 1, "b": {"c": 2}}


def test_remove_common(yaml_processor):
    """Tests the remove_common function."""
    original = {"a": 1, "b": {"c": 2, "d": 3}}
    common = {"a": 1, "b": {"c": 2}}
    yaml_processor.remove_common(original, common)
    assert original == {"b": {"d": 3}}


def test_merge_references(yaml_processor):
    """Tests the merge_references function."""
    ref1 = {"a": 1, "b": {"c": 2}}
    ref2 = {"b": {"d": 4}, "e": 5}
    merged = yaml_processor.merge_references([ref1, ref2])
    assert merged == {"a": 1, "b": {"c": 2, "d": 4}, "e": 5}


def test_process_files_extract_common(temp_yaml_files):
    """Tests the process_files function for extracting common values."""
    file1_path, file2_path, common_path = temp_yaml_files

    processor = YAMLProcessor(
        file_list=[str(file1_path), str(file2_path)], common_file=str(common_path)
    )
    processor.process_files()

    with open(common_path, "r", encoding="utf-8") as f:
        common_data = yaml.safe_load(f)
    assert common_data == {"a": 1, "b": {"c": 2}}

    with open(file1_path, "r", encoding="utf-8") as f:
        file1_data = yaml.safe_load(f)
    assert file1_data == {"b": {"d": 3}, "e": [1, 2]}


def test_process_files_remove_reference(temp_yaml_files):
    """Tests the process_files function for removing reference values."""
    file1_path, file2_path, _ = temp_yaml_files
    ref_path = Path(file1_path).parent / "ref.yaml"
    ref_data = {"a": 1, "b": {"c": 2}}
    with open(ref_path, "w", encoding="utf-8") as f:
        yaml.dump(ref_data, f)

    processor = YAMLProcessor(
        file_list=[str(file1_path), str(file2_path)], reference_files=[str(ref_path)]
    )
    processor.process_files()

    with open(file1_path, "r", encoding="utf-8") as f:
        file1_data = yaml.safe_load(f)
    assert file1_data == {"b": {"d": 3}, "e": [1, 2]}
