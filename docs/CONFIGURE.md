# Instructions for Configuring Writing Observer on RHEL Installations
### Install Global Dependencies
1. sudo yum install redis
2. sudo yum install git
3. sudo yum install nginx

## Install Required RH Python 3.8
4. sudo subscription-manager repos --enable rhel-7-server-optional-rpms \
  --enable rhel-server-rhscl-7-rpms
5. sudo yum -y install @development
6. sudo yum -y install rh-python38

* rh-pyhon38 dev tools are also required

## Setup RH Python 38 and Virtual Envs
7. scl enable rh-python38 bash
8. python --version
* The output should indicate that python 3.8 is active
9. sudo pip install virtualenvwrapper
10. sudo source `/opt/rh/rh-python38/root/usr/local/bin/virtualenvwrapper.sh`
  
## Install Local Dependencies 
11. sudo git clone `https://github.com/ArgLab/writing_observer`
12. cd writing_observer
13. make install
14. sudo mkvirtualenv learning_observer
15. pip install -r requirements.txt
16. cd learning_observer
17. python setup.py develop
18. python learning_observer

* At this point, follow the system's further instructions until the process runs on port 8888 by default

## Server Setup
19. Populate creds.yaml with required Google Cloud Parameters
20. Configure nginx on `port 80` as a proxy for Learning Observer on `port 8888`
21. Replace all instances of `writing.csc.ncsu.edu` with custom server address in all files in directory `~/writing_observer/learning_observer/learning_observer/auth`

## Client/Extension Setup
22. Replace all instances of `writing.csc.ncsu.edu` with custom server address in `~/writing_observer/extension/background.js`
* If SSL is not enabled for the server, all websocket protocols should begin with `ws://` as opposed to `wss://`
23. Open Chrome and navigate to `chrome://extensions`
24. Click on "Load Unpacked". Select `~/writing_observer/extensions` and ensure that it is enabled
25. Select `background page` on the extension section and ensure no errors are present
26. Open a Google Docs document while signed into Chrome and ensure websocket communication between client and server is active


=====================================================================
The following is a work in progerss. These are the steps I used to set up the project on an RHEL 7 system

# Setting up Learning Observer for NCSU systems

## Python
Learning Observer requires at least Python 3.8. RHEL-7 systems do not have the most intuitive way to install and activate Python 3.8.

```bash
sudo yum -y install rh-python38
```
Notes: 
1. rh-python38 dev tools are also required. This might require an extra install step.
1. You may have to update the subscription manager first

## Virtual Environment / Package setup
There is a shell script located at `servermanagement/RunLearningObserver.sh` that will automatically go and fetch Python from our virtual environment, start Learning Observer, and pipe output into log files.

We want to setup the VirtualEnvironment to do just this:
1. Locate where Python3.8 is installed.
1. Use that Python create a virtual environment named `learning_observer` inside the directory specified in the shell script mentioned above.
1. Using the Pip command from within the newly created virtual environment, install all the required packages. You'll want to use the following commands:
```bash
cd writing_observer
pip install --upgrade pip
pip install wheel
pip install -r requirements.txt
cd learning_observer
pip install -e .
cd ..
cd modules/writing_observer
pip install -e .
```
Note: you might need Sudo access to run.

You should now be able to run Learning Observer without errors.

## Running
You can run either of the following commands to start Learning Observer
```bash
# Log to standard out
cd learning_observer
python learning_observer

# Log to log file
./servermanagement/RunLearningObserver.sh
```
Note: the first commands are better for testing and making sure you are connected. The latter command should be used when setting up production. 
