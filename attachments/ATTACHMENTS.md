# OpenFOAM Source Code Attachments

This directory should contain the OpenFOAM source code for the skill to analyze.

## Directory Structure

```
attachments/
└── OpenFOAM/
    └── src/           # OpenFOAM source code
        ├── finiteVolume/
        ├── transportModels/
        ├── turbulenceModels/
        └── ...
```

## How to Obtain OpenFOAM Source Code

### Option 1: Download from Official Website

1. Visit [OpenFOAM Downloads](https://openfoam.org/download/)
2. Download the source package for OpenFOAM 9 (or your preferred version)
3. Extract and copy the `src` directory to `attachments/OpenFOAM/`

### Option 2: Clone from Git

```bash
# Clone OpenFOAM repository
git clone https://develop.openfoam.com/Development/openfoam.git

# Copy src directory
cp -r openfoam/src attachments/OpenFOAM/
```

### Option 3: Use Existing Installation

If you have OpenFOAM installed on your system:

```bash
# Set the FOAM_SRC environment variable
export FOAM_SRC=/opt/openfoam/src  # Linux
# or
set FOAM_SRC=C:\OpenFOAM\src        # Windows
```

The skill will automatically detect and use the source code from `FOAM_SRC`.

## Source Code Statistics

- Expected `.H` files: ~8,700
- Expected `.C` files: ~8,300
- Total source files: ~17,000+

## Note

The `attachments/OpenFOAM/` directory is excluded from Git by default (see `.gitignore`) due to the large number of files. Please download the source code separately after cloning this repository.
