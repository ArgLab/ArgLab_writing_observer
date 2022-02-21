# System Variables
# --------------------------------------
LOGFILE_SRC="/usr/local/share/Projects/WritingObserver/Repo-Fork/writing_observer/learning_observer/learning_observer/logs"
LOGFILE_DEST="/usr/local/share/Projects/WritingObserver/Repo-Fork/writing_observer/learning_observer/learning_observer/logs"

# Make the backup name
# ---------------------------------------
LOG_DATE=$(date "+%m-%d-%Y--%H-%M-%S")
BACKUP_NAME="$LOGFILE_DEST/learning_observer_backup_$LOG_DATE.bzip2"
echo $BACKUP_NAME;

# Create the backup
# ---------------------------------------
echo "Backing up web socket logs"
find $LOGFILE_SRC -name "????-??-??T*.log" -mmin +60 -print | zip -Z bzip2 $LOGFILE_DEST -@
echo "Removing backed up web sockets logs"
# find LOGFILE_SRC -name "????-??-??T*.log" -mmin +60 -delete
