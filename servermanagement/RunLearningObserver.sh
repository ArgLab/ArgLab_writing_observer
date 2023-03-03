
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
VIRTUALENV_PATH="/usr/local/share/projects/WritingObserver/VirtualENVs/WOvenv"
#VIRTUALENV_PYTHON="/usr/local/share/Projects/WritingObserver/VirtualENVs/learning_observer/bin/python3.9"
LEARNING_OBSERVER_LOC="/usr/local/share/projects/WritingObserver/Repositories/ArgLab_writing_observer/learning_observer"
AWE_WORKBENCH_LOC="/usr/local/share/projects/WritingObserver/Repositories/AWE_Workbench/"
AWE_COMPONENTS_LOC="/usr/local/share/projects/WritingObserver/Repositories/AWE_Components/"
LOGFILE_DEST="/usr/local/share/projects/WritingObserver/Repositories/ArgLab_writing_observer/learning_observer/learning_observer/logs"

# Make the logfile name
# ---------------------------------------
LOG_DATE=$(date "+%m-%d-%Y--%H-%M-%S")
LEARNING_OBSERVER_LOGFILE_NAME="$LOGFILE_DEST/learning_observer_service_$LOG_DATE.log"
AWE_WORKBENCH_LOGFILE_NAME="$LOGFILE_DEST/awe_workbench_service_$LOG_DATE.log"
AWE_WORDSEQPROB_LOGFILE_NAME="$LOGFILE_DEST/awe_component_wordseqprobability_service_$LOG_DATE.log"
echo $LEARNING_OBSERVER_LOGFILE_NAME;
echo $AWE_WORKBENCH_LOGFILE_NAME;
echo $AWE_WORDSEQPROB_LOGFILE_NAME;

# Activate the virtual environment.
# ---------------------------------------
source $VIRTUALENV_PATH/bin/activate
 
# Now run the AWE services.
# --------------------------------------
echo "Running AWE Workbench..."
cd $AWE_WORKBENCH_LOC
nohup python -m awe_workbench.web.startServers > $AWE_WORKBENCH_LOGFILE_NAME 2>&1 &
PROCESS_ID=$!
echo $PROCESS_ID > $LOGFILE_DEST/awe_workbench_run.pid


echo "Running AWE WORDSEQPROB..."
cd $AWE_COMPONENTS_LOC
nohup python -m awe_components.wordprobs.wordseqProbabilityServer > $AWE_WORDSEQPROB_LOGFILE_NAME 2>&1 &
PROCESS_ID=$!
echo $PROCESS_ID > $LOGFILE_DEST/awe_wordseqprobabilityserver_run.pid


# And finally run the learning observer service.
# --------------------------------------
echo "Running Learning Observer Service..."
cd $LEARNING_OBSERVER_LOC
#source $VIRTUALENV_PATH/bin/activate
#$($VIRTUALENV_PYTHON $LEARNING_OBSERVER_LOC > $LOG_NAME 2>&1)
nohup python learning_observer > $LEARNING_OBSERVER_LOGFILE_NAME 2>&1 &
PROCESS_ID=$!
echo $PROCESS_ID > $LOGFILE_DEST/learning_observer_run.pid


# Set the number of allowed open files to something large 8192
prlimit --pid $PROCESS_ID --nofile=8192
