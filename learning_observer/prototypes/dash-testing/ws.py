import asyncio
import json
import os
from quart import websocket, Quart

app = Quart(__name__)

cwd = os.getcwd()
data_in = os.path.join(cwd, 'data', 'sample.json')

@app.websocket('/courses/students/<string:id>')
async def course_student_data(id):
    # initialize group of students and send
    with open(data_in, 'r') as f_obj:
        data = json.load(f_obj)
    for i, item in enumerate(data):
        item['id'] = i
    output = json.dumps(data)
    await websocket.send(output)
    await asyncio.sleep(30)

    while True:
        # TODO figure out how to listen for specific updates, like which text to provide

        # flip a coin for each student to see if they have updates
        # updates = [update_student(s) for s in students if bool(random.getrandbits(1))]
        # output = json.dumps(updates)
        # await websocket.send(output)
        await asyncio.sleep(5)


if __name__ == '__main__':
    app.run(port=5000)
