"""Provider package for the Export Engine.

Importing this package registers every provider with the shared registry.
``apps/exports/apps.py`` imports ``apps.exports.providers`` in ``ready()`` so
the whole catalogue is populated as soon as Django is fully loaded.
"""

from __future__ import annotations

from . import (  # noqa: F401
    beneficiaries,
    directories,
    documents,
    meal,
    meetings,
    programs,
    registers,
    reports,
)
from .base import BaseProvider, Registry, register, registry

__all__ = [
    "BaseProvider",
    "Registry",
    "register",
    "registry",
]
