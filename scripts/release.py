#!/usr/bin/env python3
"""
Release script for animate-netcdf package.
This script helps automate the release process by:
1. Bumping the version number
2. Creating a git tag
3. Pushing to remote
"""

import re
import subprocess
import sys
from pathlib import Path

def get_current_version():
    """Extract current version from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    match = re.search(r'version = "([^"]+)"', content)
    if match:
        return match.group(1)
    else:
        raise ValueError("Could not find version in pyproject.toml")

def bump_version(version, bump_type):
    """Bump version number according to semantic versioning"""
    major, minor, patch = map(int, version.split('.'))
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        raise ValueError("bump_type must be 'major', 'minor', or 'patch'")
    
    return f"{major}.{minor}.{patch}"

def update_version_in_file(file_path, old_version, new_version):
    """Update version in a file"""
    with open(file_path, "r") as f:
        content = f.read()
    
    content = content.replace(f'version = "{old_version}"', f'version = "{new_version}"')
    
    with open(file_path, "w") as f:
        f.write(content)

def run_command(cmd, check=True):
    """Run a shell command"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/release.py <bump_type>")
        print("bump_type: major, minor, or patch")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    if bump_type not in ['major', 'minor', 'patch']:
        print("bump_type must be 'major', 'minor', or 'patch'")
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Calculate new version
    new_version = bump_version(current_version, bump_type)
    print(f"New version: {new_version}")
    
    # Update version in pyproject.toml
    update_version_in_file("pyproject.toml", current_version, new_version)
    print(f"Updated version in pyproject.toml to {new_version}")
    
    # Check if there are other uncommitted changes (excluding the version change we just made)
    result = run_command("git status --porcelain", check=False)
    if result.stdout.strip():
        # Filter out the pyproject.toml change we just made
        lines = result.stdout.strip().split('\n')
        other_changes = [line for line in lines if not line.endswith('pyproject.toml')]
        if other_changes:
            print("Warning: You have uncommitted changes. Please commit them first.")
            print('\n'.join(other_changes))
            sys.exit(1)
    
    # Commit the version change
    run_command(f'git add pyproject.toml')
    run_command(f'git commit -m "Bump version to {new_version}"')
    
    # Create and push tag
    tag_name = f"v{new_version}"
    run_command(f'git tag {tag_name}')
    run_command(f'git push origin main')
    run_command(f'git push origin {tag_name}')
    
    print(f"\n🎉 Successfully released version {new_version}!")
    print(f"Tag {tag_name} has been created and pushed.")
    print("GitHub Actions will automatically build and publish to PyPI.")

if __name__ == "__main__":
    main() 