from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "main",
        "utils.analyst",
        "utils.archiver",
        "utils.collector",
        "utils.config",
        "utils.filter",
        "utils.memory",
        "utils.validator",
    ],
)
def test_core_modules_import(module_name: str) -> None:
    assert importlib.import_module(module_name) is not None
