# NetCDF Animation Creator

Create beautiful animations from NetCDF files with support for both single files and multiple files without concatenation. **75-87% faster** than traditional concatenation methods.

## 🚀 Quick Start

### Installation

```bash
pip install -e .
```

### Basic Usage

```bash
# Interactive mode (recommended)
anc

# Single file
anc your_file.nc
# or
anc your_file.nc --variable InstantaneousRainRate --type efficient --fps 15


# Multiple files
anc *.nc
# or
anc F4C_00.2.SEG01.OUT.*.nc --variable InstantaneousRainRate --type efficient --fps 15

# Configuration (optional)
anc config
# or
anc config *.nc --output my_config.json
# or
anc "*.nc" --config my_config.json

```

## ✅ Key Features

- **Multi-File Support**: Process multiple NetCDF files directly (no concatenation needed)
- **Smart Dimension Handling**: Auto-detects animation dimension (time, level, etc.)
- **Three Animation Types**: `efficient` (fast), `contour` (detailed), `heatmap` (simple)
- **Configuration Management**: Interactive setup and JSON-based configuration
- **Zoom Functionality**: Crop domain by specified zoom factor

## 🔧 Command Line Options

| Option       | Description                                  | Default        |
| ------------ | -------------------------------------------- | -------------- |
| `--variable` | Variable name to animate                     | Required       |
| `--type`     | Plot type: `efficient`, `contour`, `heatmap` | `efficient`    |
| `--fps`      | Frames per second                            | `10`           |
| `--output`   | Output filename                              | Auto-generated |
| `--config`   | Load configuration from JSON file            | None           |
| `--zoom`     | Zoom factor for cropping domain              | 1.0            |

## 🧪 Testing

```bash
# Validate setup
anc validate

# Run tests
anc test --full
```

## 🚀 Deployment

This project uses automated deployment to PyPI via GitHub Actions. To release a new version:

### Automatic Deployment

1. **Create a new version tag:**

   ```bash
   python scripts/release.py patch    # for bug fixes
   python scripts/release.py minor    # for new features
   python scripts/release.py major    # for breaking changes
   ```

2. **Manual tag creation (alternative):**
   ```bash
   # Update version in pyproject.toml
   git add pyproject.toml
   git commit -m "Bump version to X.Y.Z"
   git tag vX.Y.Z
   git push origin main
   git push origin vX.Y.Z
   ```

### Setup Requirements

1. **PyPI API Token:** Create a PyPI API token at https://pypi.org/manage/account/token/
2. **GitHub Secrets:** Add your PyPI token as a GitHub secret named `PYPI_API_TOKEN`
   - Go to your GitHub repository → Settings → Secrets and variables → Actions
   - Add new repository secret with name `PYPI_API_TOKEN` and your token as the value

The GitHub Actions workflow will automatically:

- Build the package when you push a version tag (e.g., `v1.0.3`)
- Run tests on every push to main/develop branches
- Publish to PyPI when tests pass
