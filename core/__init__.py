# -*- coding: utf-8 -*-
"""
core package (Mordzix)

Zero ciężkich importów w __init__.py (żadnych side-effectów),
żeby import core.* nie wysadzał całej aplikacji.
"""

from __future__ import annotations

__version__ = "5.0.0"
__all__ = ["__version__", "lazy_import"]

def lazy_import(module_name: str):
    import importlib
    return importlib.import_module(f"{__name__}.{module_name}")
