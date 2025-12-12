# Publishing to PyPI

This guide explains how to publish `animate-netcdf` to PyPI.

## Prerequisites

1. **PyPI Account**: Ensure you have an account on [PyPI](https://pypi.org)
2. **API Token**: Create an API token at https://pypi.org/manage/account/token/
3. **GitHub Secret**: Add your PyPI API token as a secret named `PYPI_API_TOKEN` in your GitHub repository settings

## Method 1: Automated Publishing via GitHub Actions (Recommended)

Your repository is configured with GitHub Actions that automatically publish to PyPI when you push a version tag.

### Steps:

1. **Ensure version is correct** in `pyproject.toml` (currently: 1.7.0)

2. **Commit any changes**:

   ```bash
   git add .
   git commit -m "Update version to 1.7.0"
   ```

3. **Create and push a version tag**:

   ```bash
   git tag v1.7.0
   git push origin main
   git push origin v1.7.0
   ```

4. **GitHub Actions will automatically**:
   - Build the package
   - Publish to PyPI
   - You can monitor progress at: `https://github.com/YOUR_USERNAME/animate-netcdf/actions`

### Using the Release Script

Alternatively, use the provided release script:

```bash
python scripts/release.py patch   # for patch version (1.7.0 -> 1.7.1)
python scripts/release.py minor    # for minor version (1.7.0 -> 1.8.0)
python scripts/release.py major    # for major version (1.7.0 -> 2.0.0)
```

This script will:

- Bump the version in `pyproject.toml`
- Commit the change
- Create and push the tag
- Trigger the GitHub Actions workflow

## Method 2: Manual Publishing

If you prefer to publish manually:

### Steps:

1. **Install build tools**:

   ```bash
   pip install build twine
   ```

2. **Build the package**:

   ```bash
   python -m build
   ```

   This creates `dist/` directory with `.whl` and `.tar.gz` files.

3. **Check the build** (optional but recommended):

   ```bash
   twine check dist/*
   ```

4. **Upload to PyPI**:

   ```bash
   twine upload dist/*
   ```

   You'll be prompted for your PyPI username and password/token.

   Or use an API token:

   ```bash
   twine upload dist/* --username __token__ --password YOUR_API_TOKEN
   ```

5. **Test on TestPyPI first** (recommended for first-time publishing):
   ```bash
   twine upload --repository testpypi dist/*
   pip install --index-url https://test.pypi.org/simple/ animate-netcdf
   ```

## Version Management

- Update version in `pyproject.toml` (line 7)
- Update version in `animate_netcdf/__init__.py` (line 13)
- Follow [Semantic Versioning](https://semver.org/):
  - **MAJOR**: Breaking changes
  - **MINOR**: New features (backward compatible)
  - **PATCH**: Bug fixes (backward compatible)

## Current Version

Current version: **1.7.0**

## Troubleshooting

- **"Package already exists"**: The version number must be unique. Increment it in `pyproject.toml`
- **"Authentication failed"**: Check your PyPI API token
- **"Build failed"**: Ensure all dependencies in `requirements.txt` are valid
- **GitHub Actions not triggering**: Ensure the tag format is `v*` (e.g., `v1.7.0`)
