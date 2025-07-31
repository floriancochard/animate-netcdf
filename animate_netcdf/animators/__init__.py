#!/usr/bin/env python3
"""
Animation modules for the Animate NetCDF package.

This package contains animation-related classes including:
- Base animator (abstract class)
- Single file animator
- Multi-file animator
"""

from .base_animator import BaseAnimator
from .single_file_animator import SingleFileAnimator
from .multi_file_animator import MultiFileAnimator

__all__ = [
    'BaseAnimator',
    'SingleFileAnimator',
    'MultiFileAnimator'
] 