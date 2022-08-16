import asyncio
from faker import Faker
import json
import random
from quart import websocket, Quart

app = Quart(__name__)
fake = Faker()

def create_student(id):
    data = {
        'id': id,
        'text': fake.text(max_nb_chars=1250),
        'link': 'http://www.example.com',
        'metrics': {
            'sentences': {'id': 'sentences', 'value': random.randint(1, 4), 'label': ' sentences'},
            'since_last_edit': {'id': 'since_last_edit', 'value': random.randint(10, 100), 'label': ' minutes since last edit'},
            'edits_per_min': {'id': 'edits_per_min', 'value': random.randint(10, 100), 'label': ' words in 5 minutes'},
        },
        'indicators': {
            'transition_words': {'id': 'transition_words', 'value': random.randint(1, 3), 'label': 'Transitions'},
            'academic_language': {'id': 'academic_language', 'value': random.randint(1, 3), 'label': 'Academic Language'},
        }
    }
    return data

def update_student(data):
    updates = {
        'id': data['id'],
        'metrics': {},
        'indicators': {}
    }
    # flip a coin for each update
    if bool(random.getrandbits(1)):
        updates['metrics']['sentences'] = {'value': data['metrics']['sentences']['value'] + random.randint(1, 10)}
    if bool(random.getrandbits(1)):
        updates['metrics']['since_last_edit'] = {'value': random.randint(0, 10)}
    if bool(random.getrandbits(1)): 
        updates['metrics']['edits_per_min'] = {'value': random.randint(5, 20)}
    if bool(random.getrandbits(1)):
        updates['indicators']['transition_words'] = {'value': random.randint(1, 3)}
    if bool(random.getrandbits(1)):
        updates['indicators']['academic_language'] = {'value': random.randint(1, 3)}
    return updates


@app.websocket('/courses/students/<string:id>')
async def course_student_data(id):
    count = int(id)
    
    # initialize group of students and send
    students = [create_student(i) for i in range(count)]
    output = json.dumps(students)
    await websocket.send(output)
    await asyncio.sleep(30)

    while True:
        # TODO figure out how to listen for specific updates, like which text to provide

        # flip a coin for each student to see if they have updates
        updates = [update_student(s) for s in students if bool(random.getrandbits(1))]
        output = json.dumps(updates)
        await websocket.send(output)
        await asyncio.sleep(5)


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
