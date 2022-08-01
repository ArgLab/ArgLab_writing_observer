import asyncio
from attr import attrib
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

def create_student(id):
    data = {
        'id': id,
        'text': fake.text(),
        'sentences': random.randint(1, 4),
        'paragraphs': 1,
        'card_info': random.choice(class_names),
        'unique_words': random.randint(5, 20),
        'time_on_task': random.randint(10, 100),
        'transition_words': random.randint(1, 3),
        'use_of_synonyms': random.randint(1, 3),
        'sv_agreement': random.randint(1, 3),
        'formal_language': random.randint(1, 3)
    }
    return data

def update_student(data):
    updates = {}
    updates['id'] = data['id']
    # flip a coin for each update
    if bool(random.getrandbits(1)):
        updates['sentences'] = data['sentences'] + random.randint(1, 10)
    if bool(random.getrandbits(1)):
        updates['paragraphs'] = data['paragraphs'] + int(data['sentences'] / random.randint(4, 8))
    if bool(random.getrandbits(1)):
        updates['unique_words'] = data['unique_words'] + random.randint(5, 20)
    if bool(random.getrandbits(1)):
        updates['time_on_task'] = data['time_on_task'] + random.randint(0, 60)
    if bool(random.getrandbits(1)):
        updates['transition_words'] = random.randint(1, 3)
    if bool(random.getrandbits(1)):
        updates['use_of_synonyms'] = random.randint(1, 3)
    if bool(random.getrandbits(1)):
        updates['sv_agreement'] = random.randint(1, 3)
    if bool(random.getrandbits(1)):
        updates['formal_language'] = random.randint(1, 3)
    return updates

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
    
    # initialize group of students and send
    students = [create_student(i) for i in range(count)]
    output = json.dumps(students)
    await websocket.send(output)
    await asyncio.sleep(30)

    while True:
        # flip a coin for each student to see if they have updates
        updates = [update_student(s) for s in students if bool(random.getrandbits(1))]
        output = json.dumps(updates)
        await websocket.send(output)
        await asyncio.sleep(30)


@app.websocket('/analysis/<string:id>')
async def analysis_data(id):
    await websocket.accept()
    while True:
        msg = await websocket.receive()
        data_in = json.loads(msg)
        reports = data_in['reports']
        all_reports = ['transition_words', 'use_of_synonyms', 'sv_agreement', 'formal_language']
        assignments = 4
        data = {
            'x': [
                [
                    i for i in range(assignments)
                ] if r in reports else [None for _ in range(assignments)] for r in all_reports 
            ],
            'y': [
                [
                    random.choice(['Low', 'Mid', 'High']) for _ in range(assignments)
                ] if r in reports else [None for _ in range(assignments)] for r in all_reports
            ],
        }
        output = json.dumps(data)
        await websocket.send(output)

if __name__ == '__main__':
    app.run(port=5000)
