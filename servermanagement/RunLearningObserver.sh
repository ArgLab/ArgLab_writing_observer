#!/usr/bin/env bash
# ===============================
# RunLearningObserver.sh
# Collin F. Lynch
#
# This bash script provides a simple wrapper to run the 
# learning observer service and pipe the data to a logfile
# over time this should be integrated into the systemd 
# service process.  This uses static variables to specify
# the location of the virtualenv and the command and 
# specifies the location for the running logfile. 

# System Variables
# --------------------------------------
VIRTUALENV_PATH="/usr/local/share/projects/WritingObserver/VENV/WOVenv"
#VIRTUALENV_PYTHON="/usr/local/share/Projects/WritingObserver/VirtualENVs/learning_observer/bin/python3.9"
LEARNING_OBSERVER_LOC="/usr/local/share/projects/WritingObserver/Repositories/ArgLab_writing_observer/learning_observer"
LOGFILE_DEST="/usr/local/share/projects/WritingObserver/Repositories/ArgLab_writing_observer/learning_observer/learning_observer/logs"


# Make the logfile name
# ---------------------------------------
LOG_DATE=$(date "+%m-%d-%Y--%H-%M-%S")
LOGFILE_NAME="$LOGFILE_DEST/learning_observer_service_$LOG_DATE.log"
echo $LOG_NAME;

DOC_PROCESSOR_LOG="$LOGFILE_DEST/document_processor_service_$LOG_DATE.log"
echo $DOC_PROCESSOR_LOG;

# Now run the thing.
# --------------------------------------
echo "Running Learning Observer Service..."
cd $LEARNING_OBSERVER_LOC

source $VIRTUALENV_PATH/bin/activate

nohup python learning_observer/doc_processor.py > $DOC_PROCESSOR_LOG 2>&1 &
DOC_PROCESS_ID=$!
echo $DOC_PROCESS_ID > $LOGFILE_DEST/doc_run.pid

nohup python learning_observer > $LOGFILE_NAME 2>&1 &
PROCESS_ID=$!
echo $PROCESS_ID > $LOGFILE_DEST/run.pid

# Set the number of allowed open files to something large 8192
prlimit --pid $PROCESS_ID --nofile=8192
