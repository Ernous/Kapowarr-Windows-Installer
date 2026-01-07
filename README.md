# Kapowarr Windows Installer

This project provides a professional NSIS-based installer for Kapowarr on Windows. It includes a system tray application for easy management and can install Kapowarr as a Windows Service.

## Features

- Automatic bundling of Kapowarr latest release
- Portable Python environment included
- Windows Service support via NSSM
- System tray application for status monitoring and control
- Automated builds for x64, x86, and ARM64 architectures

## Project Structure

- installer.nsi: Main NSIS script for building the installer
- pre_build.py: Script to download and prepare all dependencies
- installer_files/: Configuration files, batch scripts, and tray application source
- .github/workflows/: Automation for building and releasing installers

## How to Build Locally

1. Install Python 3.11 or newer
2. Install NSIS
3. Run the pre-build script for your architecture:
   python pre_build.py x64
4. Compile the installer:
   makensis installer.nsi

The resulting installer will be in the installer_output directory.

## Automated Builds

The project uses GitHub Actions to monitor the official Kapowarr repository. When a new version is released, it automatically:
1. Downloads the new version
2. Prepares environments for x64, x86, and ARM64
3. Builds installers for all three architectures
4. Creates a new release in this repository with the compiled installers

## Components Included

- Kapowarr (Latest Release)
- Portable Python
- NSSM (Non-Sucking Service Manager)
- Custom Python Tray Application
