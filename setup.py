#!/usr/bin/env python3
"""
Setup script for Animate NetCDF package.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'readme.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "A comprehensive tool for creating animations from NetCDF data files."

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="animate-netcdf",
    version="1.0.2",
    author="Florian Cochard",
    author_email="florian@weatherwise.fr",  # Update with your actual email
    description="A comprehensive tool for creating animations from NetCDF data files",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/floriancochard/animate-netcdf",  # Update with your actual repo

    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Multimedia :: Video",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "animate-netcdf=animate_netcdf.__main__:main",
            "anc=animate_netcdf.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 