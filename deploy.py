#!/usr/bin/env python3
"""
Deployment helper script for HTML Email Template Transformer
This script helps you prepare and deploy your Streamlit app.
"""

import os
import subprocess
import sys

def check_git_installed():
    """Check if git is installed."""
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_git_repo():
    """Check if current directory is a git repository."""
    return os.path.exists('.git')

def init_git_repo():
    """Initialize git repository."""
    print("🔄 Initializing git repository...")
    subprocess.run(['git', 'init'], check=True)
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit: HTML Email Template Transformer'], check=True)
    subprocess.run(['git', 'branch', '-M', 'main'], check=True)
    print("✅ Git repository initialized successfully!")

def create_github_repo():
    """Guide user to create GitHub repository."""
    print("\n📋 To deploy your app, follow these steps:")
    print("\n1. Create a new repository on GitHub:")
    print("   - Go to https://github.com/new")
    print("   - Choose a repository name (e.g., 'html-email-transformer')")
    print("   - Make it public or private")
    print("   - Don't initialize with README (we already have one)")
    print("   - Click 'Create repository'")
    
    repo_url = input("\n2. Enter your GitHub repository URL (e.g., https://github.com/username/repo-name): ").strip()
    
    if repo_url:
        try:
            subprocess.run(['git', 'remote', 'add', 'origin', repo_url], check=True)
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)
            print("✅ Code pushed to GitHub successfully!")
            return repo_url
        except subprocess.CalledProcessError as e:
            print(f"❌ Error pushing to GitHub: {e}")
            return None
    return None

def deploy_to_streamlit():
    """Guide user to deploy on Streamlit Cloud."""
    print("\n🌐 Deploy to Streamlit Cloud:")
    print("\n1. Go to https://share.streamlit.io")
    print("2. Sign in with your GitHub account")
    print("3. Click 'New app'")
    print("4. Select your repository and branch (main)")
    print("5. Set the main file path to: app.py")
    print("6. Click 'Deploy'")
    print("\nYour app will be deployed and you'll get a public URL!")

def main():
    print("🚀 HTML Email Template Transformer - Deployment Helper")
    print("=" * 60)
    
    # Check if git is installed
    if not check_git_installed():
        print("❌ Git is not installed. Please install git first:")
        print("   - Windows: https://git-scm.com/download/win")
        print("   - macOS: brew install git")
        print("   - Linux: sudo apt-get install git")
        return
    
    # Check if git repo exists
    if not check_git_repo():
        print("📁 No git repository found. Creating one...")
        init_git_repo()
    else:
        print("✅ Git repository already exists.")
    
    # Check if remote exists
    try:
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
        if 'origin' not in result.stdout:
            print("🔗 No remote repository configured.")
            repo_url = create_github_repo()
            if repo_url:
                deploy_to_streamlit()
        else:
            print("✅ Remote repository already configured.")
            deploy_to_streamlit()
    except subprocess.CalledProcessError:
        print("❌ Error checking git remote.")
        return

if __name__ == "__main__":
    main() 