# NCSU system setup guide

The following is a guide to help with the installation of Learning Observer (LO) on NCSU systems.

This guide assumes you are using an RHEL system.
Additionally, depending on where on the system you place the repository, you may need to run all commands as a sudo user.

## Requirements

LO is confirmed to work on `Python 3.8`.
Along with the base install of Python, LO requires the Python developer tools.
These can be installed with the following commands:

```bash
sudo yum install rh-python38    # base python
sudo yum install python38-devel # developer tools for python 3.8
```

The Python installation should be located at `/opt/rh/rh-python38`.
Note this location for future sections.

## Install

### Virtual Environment

To make sure we are using the proper installation of Python, we will use a virtual environment.
To do this, run the following command:

```bash
/path/to/python3.8/ -m venv /path/of/desired/virtual/environment
```

Again, keep note of where the virtual environment is located for future steps.

### Config files

For each system, you'll need to create a new `creds.yaml` file within the `/path/to/repo/learning_observer` directory.
This file defines what type of connections are allowed to be made to the system.
Luckily, there is an example file you can copy located in the `/path/to/repo/learning_observer/learning_observer` directory.
When attempting to run the system later on in this setup guide, if you have any misconfigured here, then the system will tell you what's wrong.

Some of the main changes that need to be made are:

1. types of `auth` allowed
1. `aio` session secret and max age
1. `event_auth` to allow access from various locations (like Chromebooks)
1. `server` for reconfiguring the port information

More configurables are expected to be included in this config file in the future.

### Package installation

Before we get started installing packages, we must ensure that the `pip` in our virtual environment is up to date.
Some of the packages located in the `requirements.txt` file require `wheel` to be installed first.
After the base requirements are installed, we will also need to install the local packages (the Writing Observer module and the Learning Observer module).
To handle all the installs, use the following:

```bash
cd writing_observer                                         # cd into the top level of the repository
/path/to/venv/bin/pip install --upgrade pip                 # upgrade pip
/path/to/venv/bin/pip install wheel                         # install wheel
/path/to/venv/bin/pip install -r requirements.txt           # install package requirements
/path/to/venv/bin/pip install -e /learning_observer         # install learning observer module
/path/to/venv/bin/pip install -e /modules/writing_observer  # install writing observer module
```

### Proxy server

By default, LO runs on port 8888.
Configure nginx, or another proxy server, for LO's port.

## System specific changes

There are various lines of code that point to specific servers.
For each setup, we need to make sure these are pointing to the proper place.

### Server

#### Auth information

On the server, we need to point the redirect uri to the server we are working with.
Depending on how the credentials files was handled, this change may not be necessary to get the system running.
The redirect uri is used with the Google login.
If that is not used, then this step is not needed.
This is located in `/path/to/repo/learning_observer/learning_observer/auth/social_sso.py`.

#### Server management

Additionally, we need to set up the server management files in the `/path/to/repo/servermanagement` direcotry.

In the `RunLearningObserver.sh` file, you'll want to set the system variables to match the current system.

```bash
VIRTUALENV_PYTHON="/full/path/to/venv/bin/pip"
LEARNING_OBSERVER_LOC="/full/path/to/repo/learning_observer"
LOGFILE_DEST="/path/to/log/storage"
```

In the `BackupWebsocketLogs.sh` file, you'll want to set log directory to the same place as you set in `RunLearningObserver.sh` and set where the logs should be backed up.

```bash
LOGFILE_SRC="/path/to/log/storage"
LOGFILE_DEST="/path/to/log/backups"
```

Lastly, we need to update the `learning_observer_logrotate` file.
Set the backup location for the generic logs.

```bash
    olddir /path/to/log/backups
```

### Client

On the clientside, we need to add the correct server to  the `websocket_logger()` method in the `/path/to/repo/extension/extension/background.js` file.
If the server has SSL enabled, then the address we add should start with `wss://`.
If SSL is not enabled, then the address should start with `ws://`.
If a proxy server is not setup yet, make sure to include the port number (default 8888) on the end of the address.
An example of each instance is shown below:

```js
websocket_logger("wss://writing.csc.ncsu.edu/wsapi/in/")        // SSL enabled, nginx set
websocket_logger("ws://writing.csc.ncsu.edu:8888/wsapi/in/")    // SSL not enabled, nginx not setup 
```

## Running the server

There are 2 different ways we can run the system.
One is better for debugging, whereas the other is best for when you want to run the server and leave it up.
We suggest completely testing the installation with the debugging steps first.

### For debugging

To run the system for debugging, we will just run the Learning Observer module.
This will output all the log information to the console.
To do this, use the following command:

```bash
/path/to/venv/bin/python /learning_observer/learning_observer/  # run the learning observer module from within the learning observer directory
```

You should see any errors printed directly to the console.

### As a server

To run the system as a server, we will run the `RunLearningObserver.sh` script.
This fetches the virtual environment, runs the server, and pipes files into the proper log location we setup during the **System specific changes** section.
Run the following commands:

```bash
./servermanagement/RunLearningObserver.sh
```

Check the logs for any errors.

## Connecting the client

The client is run through a Google Chrome extension.
To properly use the client, you must sign into Chrome and use the same account to access to Google Docs.

From there, navigate to the extension manage located in settings.
Turn on Developer Mode (top right), then click the `Load Unpacked` button.
This opens a file explorer, where you should locate the repository.
More specifically, select the `writing_observer/extension/extension` directory.
This will unpack the extension and make it available for use in Google Chrome.

To make sure it is working, click on the `background page` link on extension card from within the extension manager.
This opens an inspect window.
On this window, select the `Console` tab.
Next, open a Google doc and start typing.
You should see events within the console.
Ensure there are no logs sprinkled in.

## Backing up logs

Whenever a websocket is made, the server creates a new log file for that connection on top of the primary logs files.
We need to backup both the generic log files as well as all the websocket specific logs.

### General logs

The generic logs include the `*.pid`, `*.json`, `debug.log`, `incoming_websocket.log` and `learning_observer_service*.log` files located in the log directory.

To backup the generic logs, we use the `logrotate` unix tool.
You'll need to copy the modified configuration file from the repository into the lograte directory.
Use this command:

```bash
cp /path/to/repo/servermanagement/learning_observer_logrotate /etc/lograte.d
```

As long as logrotate is installed, the generic logs will be backed up once a day.

### Websocket logs

The websocket logs take a little more setting up.
We will set up an hourly `cron` job to run a backup script, `/path/to/repo/servermanagement/BackupWebsocketLogs.sh`.
The backup script will search the log directory for any logs that match the websocket pattern and were last modified in the last **60 minutes**.
Next, the backup script will remove any files that match the pattern and were modifed in the last **120 minutes**.
This provides us redundancy in our backups.

To set up the cron job, we first enter the crontab utility then add a line for the backup script.

```bash
crontab -e  # open the cron job menu

0 * * * * ./full/path/to/repo/servermanagement/BackupWebsocketLogs.sh # line to add to the cronjob
# Run it at the 0th minute every hour, every day, every month, and so on
```
