# Prototypes

Required packages
```bash
cd learning_observer/prototypes/dash-testing
pip install requirements.txt
pip install learning_observer_components-0.0.1.tar.gz # these components are not published anywhere so manual install is necessary
mkdir data  # create a directory for the data (not shared through Git)
# add the data files to this location
```

Running. Since you'll need two servers running, you'll need two terminals.
```bash
cd learning_observer/prototypes/dash-testing
python ws.py    # simple websocket server to connect to
python app.py   # dash application
```

Navigate to [http://127.0.0.1:8050/dashboard](http://127.0.0.1:8050/dashboard) to see the working prototype.

The websockets are connected through a clientside callback using `from dash_extensions import WebSocket`.

`drag.py` is an example for getting the dragging and dropping working.
