#!/usr/bin/env python3
"""
Setup script for automated PyPI deployment.
This script helps you configure the necessary settings for automated deployment.
"""

import os
import sys
from pathlib import Path

def check_git_repo():
    """Check if we're in a git repository"""
    if not Path(".git").exists():
        print("❌ Error: Not in a git repository")
        print("Please run this script from your project root directory")
        return False
    return True

def check_github_remote():
    """Check if GitHub remote is configured"""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"], 
            capture_output=True, 
            text=True
        )
        if "github.com" in result.stdout:
            return True
        else:
            print("⚠️  Warning: GitHub remote not detected")
            print("Make sure your repository is pushed to GitHub")
            return False
    except:
        print("⚠️  Warning: Could not check git remotes")
        return False

def check_pyproject_toml():
    """Check if pyproject.toml exists and has correct structure"""
    if not Path("pyproject.toml").exists():
        print("❌ Error: pyproject.toml not found")
        return False
    
    with open("pyproject.toml", "r") as f:
        content = f.read()
    
    if 'name = "animate-netcdf"' not in content:
        print("⚠️  Warning: Package name not found in pyproject.toml")
        return False
    
    if 'version = "' not in content:
        print("⚠️  Warning: Version not found in pyproject.toml")
        return False
    
    return True

def check_github_actions():
    """Check if GitHub Actions workflows exist"""
    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        print("❌ Error: GitHub Actions workflows not found")
        print("Make sure .github/workflows/ directory exists with workflow files")
        return False
    
    workflow_files = list(workflows_dir.glob("*.yml"))
    if not workflow_files:
        print("❌ Error: No workflow files found in .github/workflows/")
        return False
    
    print(f"✅ Found {len(workflow_files)} workflow file(s)")
    return True

def print_setup_instructions():
    """Print setup instructions"""
    print("\n" + "="*60)
    print("🚀 AUTOMATED PYPI DEPLOYMENT SETUP")
    print("="*60)
    
    print("\n📋 To complete the setup, follow these steps:")
    
    print("\n1️⃣  Create a PyPI API Token:")
    print("   - Go to https://pypi.org/manage/account/token/")
    print("   - Create a new API token")
    print("   - Copy the token (you'll need it for step 2)")
    
    print("\n2️⃣  Add the token to GitHub Secrets:")
    print("   - Go to your GitHub repository")
    print("   - Navigate to Settings → Secrets and variables → Actions")
    print("   - Click 'New repository secret'")
    print("   - Name: PYPI_API_TOKEN")
    print("   - Value: [your PyPI API token]")
    
    print("\n3️⃣  Push your repository to GitHub:")
    print("   git push origin main")
    
    print("\n4️⃣  Test the deployment:")
    print("   python scripts/release.py patch")
    
    print("\n✅ Once completed, every time you run the release script,")
    print("   your package will automatically be published to PyPI!")
    
    print("\n" + "="*60)

def main():
    print("🔍 Checking deployment setup...")
    
    checks = [
        ("Git Repository", check_git_repo),
        ("GitHub Remote", check_github_remote),
        ("pyproject.toml", check_pyproject_toml),
        ("GitHub Actions", check_github_actions),
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        if check_func():
            print(f"✅ {name} is properly configured")
        else:
            print(f"❌ {name} needs attention")
            all_passed = False
    
    if all_passed:
        print("\n🎉 All checks passed! Your deployment setup looks good.")
        print("Make sure to complete the PyPI token setup (see instructions below).")
    else:
        print("\n⚠️  Some issues were found. Please fix them before proceeding.")
    
    print_setup_instructions()

if __name__ == "__main__":
    main() 