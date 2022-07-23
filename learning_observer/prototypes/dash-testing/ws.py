import asyncio
from turtle import update
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
    'border-3 border-warning',
]

def update_student(data=None, id=None):
    if data is None:
        data = {
            'id': id,
            'text': fake.text(),
            'sentences': random.randint(1, 4),
            'paragraphs': 1,
            'unique_words': random.randint(5, 20),
            'time_on_task': random.randint(10, 100),
            'data': {}
        }
    sleep_time = random.randint(10, 60)
    data['card_info'] = random.choice(class_names)
    data['sentences'] += random.randint(1, 10)
    data['paragraphs'] = int(data['sentences'] / random.randint(4, 8))
    data['unique_words'] += random.randint(5, 20)
    data['time_on_task'] += sleep_time
    data['data'] =  {
        'transition_words': random.randint(1,3),
        'use_of_synonyms': random.randint(1,3),
        'sv_agreement': random.randint(1,3),
        'formal_language': random.randint(1,3),
    } 
    return data

@app.websocket('/student/<string:id>')
async def student_data(id):
    data = {
        'id': id,
        'text': fake.text(),
        'sentences': random.randint(1, 4),
        'paragraphs': 1,
        'unique_words': random.randint(5, 20),
        'time_on_task': random.randint(10, 100),
        'data': {}
    }
    while True:
        sleep_time = random.randint(10, 60)
        data['card_info'] = random.choice(class_names)
        data['sentences'] += random.randint(1, 10)
        data['paragraphs'] = int(data['sentences'] / random.randint(4, 8))
        data['unique_words'] += random.randint(5, 20)
        data['time_on_task'] += sleep_time
        data['data'] =  {
            'transition_words': random.randint(1,3),
            'use_of_synonyms': random.randint(1,3),
            'sv_agreement': random.randint(1,3),
            'formal_language': random.randint(1,3),
        }        
        output = json.dumps(data)
        await websocket.send(output)
        await asyncio.sleep(sleep_time)


@app.websocket('/courses/students/<string:id>')
async def course_student_data(id):
    count = int(id)
    students = [update_student(None, i) for i in range(count)]
    while True:
        students = [update_student(s) if bool(random.getrandbits(1)) else s for s in students]
        output = json.dumps(students)
        await websocket.send(output)
        await asyncio.sleep(30)


@app.websocket('/analysis/<string:id>')
async def analysis_data(id):
    data = {
        'id': id
    }
    while True:
        data['data'] = [random.random() for _ in range(10)]
        output = json.dumps(data)
        await websocket.send(output)
        await asyncio.sleep(random.randint(10, 30))

if __name__ == '__main__':
    app.run(port=5000)
