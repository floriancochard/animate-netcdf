# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.3] - 2025-12-13

### Fixed

- Fixed package data inclusion
- Bumpted version to 1.7.3

## [1.7.2] - 2025-12-13

### Added

- Better GitHub Actions workflows

## [1.7.1] - 2025-12-12

### Fixed

- Fixed documentation links
- Fixed package data inclusion

## [1.7.0] - 2025-12-12

### Added

- Designer mode for cleaner visualizations
- Transparent background for PNG output
- Ignore values functionality

## [1.6.1] - 2025-07-31

### Changed

- Readme updated

## [1.6.0] - 2024-01-XX

### Added

- Automated PyPI deployment via GitHub Actions
- Release automation scripts (`scripts/release.py`, `scripts/setup_deployment.py`)
- Comprehensive deployment documentation
- GitHub Actions workflows for testing and publishing
- Setup verification script for deployment configuration

### Changed

- **Note**: Version jumped from 1.0.2 to 1.6.0 due to automated deployment setup
- Updated project documentation with deployment instructions
- Enhanced project structure with CI/CD configuration

### Technical

- Added `.github/workflows/publish.yml` for automated PyPI publishing
- Added `.github/workflows/test.yml` for multi-Python version testing
- Updated `pyproject.toml` with proper version management
- Added deployment documentation in `docs/DEPLOYMENT.md`

## [1.0.2] - Previous Release

### Features

- Multi-file NetCDF animation support
- Three animation types: efficient, contour, heatmap
- Interactive configuration management
- Zoom functionality for domain cropping
- Smart dimension handling for time/level animations

### Technical

- Command-line interface with `anc` command
- Configuration-based workflow support
- FFmpeg integration for video generation
- Comprehensive testing framework

---

## Version History Note

**Version Jump Explanation**: The version jumped from 1.0.2 to 1.6.0 during the setup of automated deployment infrastructure. This was an administrative change to establish proper CI/CD workflows and does not represent a proportional increase in features. Future releases will follow normal semantic versioning from 1.6.0 onwards.
