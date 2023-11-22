#!/usr/bin/env bash
#
# Add SetupAWE_Components
# Damilola Babalola

# This script installs the AWE_Components and its prerequisities at once.


# Parameters:
# ---------------------------------------------
# Change these if you need to use a different
# python or pip.  Otherwise leave them as-is. 
PYTHON_CMD="python"
PIP_CMD="pip"


# Installing the prerequisites for AWE_Components
echo -e "\n=== Installing Holmes Extractor Expandable ==="
cd ../../holmes-extractor-expandable/
"$PIP_CMD" install .
cd ..

echo -e "\n=== Installing AWE_LanguageTool ==="
cd ./AWE_LanguageTool/
"$PIP_CMD" install .
cd ..

echo -e "\n=== Installing AWE_SpellCorrect ==="
cd ./AWE_SpellCorrect/
"$PIP_CMD" install .
cd ..

echo -e "\n=== Installing AWE_Lexica ==="
cd ./AWE_Lexica/
"$PIP_CMD" install .
cd ..

# Now installing AWE_Components
echo -e "\n=== Installing AWE_Components ==="
cd ./AWE_Components/
"$PIP_CMD" install -e .
"$PYTHON_CMD" -m awe_components.setup.data --install
cd ..
