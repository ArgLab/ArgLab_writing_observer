# Prototypes

Required packages
```bash
cd learning_observer/prototypes/dash-testing
pip install requirements.txt
```

Running. Since you'll need two servers running, you'll need two terminals.
```bash
cd learning_observer/prototypes/dash-testing
python ws.py    # simple websocket server to connect to
python app.py   # dash application
```

Under `pages/teacher_dashboard.py` you'll see a bunch of `clientside_callbacks`. Those are Javascript functions, see `assets/scripts.js` for more.

The websockets are connected through a clientside callback using `from dash_extensions import WebSocket`.

`drag.py` is an example for getting the dragging and dropping working.
