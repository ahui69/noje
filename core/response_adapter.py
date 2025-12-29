#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
response_adapter.py — adapter odpowiedzi do endpointów.

Minimalny, ale stabilny:
- Nie rozsypuje importów.
- Pozwala endpointom opakować dane do spójnego dict.
"""

from __future__ import annotations

from typing import Any, Dict, List


def adapt(data: Any) -> Dict[str, Any]:
    """
    Adaptuje dowolne dane do dict.
    Jeśli `data` jest dict -> zwraca as-is.
    Jeśli jest list/str/inna -> pakuje w {"data": ...}.
    """
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return {"data": data}
    if isinstance(data, str):
        return {"text": data}
    return {"data": data}
