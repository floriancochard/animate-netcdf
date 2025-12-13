"""Test that the package can be imported."""
import pytest


def test_package_import():
    """Test that animate_netcdf can be imported."""
    import animate_netcdf
    assert animate_netcdf is not None
    assert hasattr(animate_netcdf, '__version__')


def test_main_module_import():
    """Test that main modules can be imported."""
    from animate_netcdf import __main__
    assert __main__ is not None
