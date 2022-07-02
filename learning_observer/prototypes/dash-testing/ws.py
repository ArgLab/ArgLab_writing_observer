import asyncio
from faker import Faker
import json
import random
from quart import websocket, Quart

app = Quart(__name__)
fake = Faker()

@app.websocket('/random_data/')
async def random_data():
    while True:
        output = json.dumps([random.random() for _ in range(10)])
        await websocket.send(output)
        await asyncio.sleep(10)

class_names = [
    'border-3 border-primary',
    'border-3 border-secondary',
    'bg-warning',
]
@app.websocket('/student/<string:id>')
async def student_data(id):
    data = {
        'id': id,
        'text': fake.text(),
        'sentences': 9,
        'paragraphs': 3
    }
    while True:
        data['class_name'] = random.choice(class_names)
        output = json.dumps(data)
        await websocket.send(output)
        await asyncio.sleep(random.randint(10, 100))


@app.websocket('/analysis/<string:id>')
async def analysis_data(id):
    data = {
        'id': id
    }
    while True:
        data['data'] = [random.random() for _ in range(10)]
        output = json.dumps(data)
        await websocket.send(output)
        await asyncio.sleep(random.randint(10, 60))

if __name__ == '__main__':
    app.run(port=5000)
