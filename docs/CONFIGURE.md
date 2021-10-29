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