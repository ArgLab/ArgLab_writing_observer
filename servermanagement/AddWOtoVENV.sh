#!/usr/bin/env bash
#
# Add AWOtoVENV
# Collin F. Lynch

# This script takes as argument a specified VENV.  It
# then adds the Learning Observer, Writing Observer, and
# the dashboard.  Construction of the VENV can be done
# using the SetupVENV script located in this directory.


# Argument
# --------------------------------------------
# This takes a single argument that should point
# to the directory of the VENV.  You can then
# use this to make any necessary changes.  
VIRTUAL_ENV="$1"
echo "USING VENV: $VIRTUAL_ENV"



# Parameters:
# ---------------------------------------------
# Change these if you need to use a different
# python or pip.  Otherwise leave them as-is. 
PYTHON_CMD="python"
PIP_CMD="pip"

CODE_REPOS_LOC="../../"

# Activate VENV
# ---------------------------------------------------------
source "$VIRTUAL_ENV/bin/activate"


# Installation
# ----------------------------------------------------------
# If we plan to use a GPU then this line must also
# be run.  Comment out the code below if you do
# not want cuda installed or edit it for your
# library version.
#
# Note that by default we seem to be unable to rely
# on spacy to pull the right cuda on its own
#echo -e "\n=== Installing Spacy CUDA, comment out if not needed. ==="
#echo -e "\n    Using CUDA v. 117"
#"$PIP_CMD" install spacy[cuda117]

# If you are using cuda 12.1 as we are on some
# systems then spacy's passthrough install will
# not work.  Therefore you will need a two-step
# process.
echo -e "\n    Using CUDA v. 12.x"
"$PIP_CMD" install cupy-cuda12x
"$PIP_CMD" install spacy[cuda12x]


# Install basic requirements.
echo -e "\n=== Installing Requirements.txt ==="
cd ..
"$PIP_CMD" install -r requirements.txt

echo -e "\n=== Installing Learning Observer ==="
make install
#cd learning_observer
#"$PYTHON_CMD" setup.py develop

pip install --upgrade spacy[cuda12x]
pip install --upgrade pydantic


echo -e "\n=== Installing Modules ==="
cd ../modules/

echo -e "\n--- Installing Writing Observer ---"
cd ./writing_observer
"$PYTHON_CMD" setup.py develop
cd ..

echo -e "\n--- Installing lo_dash_react_components. ---"
cd ./lo_dash_react_components
nvm install
nvm use
npm install
"$PYTHON_CMD" setup.py develop
pip install .
cd ..

echo -e "\n--- Installing wo_highlight_dashboard. ---"
cd ./wo_highlight_dashboard
"$PYTHON_CMD" setup.py develop
cd ..


echo -e "\n--- Installing common student errors. ---"
cd ./wo_common_student_errors
"$PYTHON_CMD" setup.py develop
cd ..


echo -e "\n--- Installing bulk analysius (askGPT). ---"
cd ./wo_bulk_essay_analysis
"$PYTHON_CMD" setup.py develop
cd ..





