# package imports
import json
import os
import random
from scipy import stats

cwd = os.getcwd()
data_path = os.path.join(cwd, 'data', 'kaggle_processed')

overall_jsons = [f for f in os.listdir(data_path) if f.endswith('.masked')]
essays = []
# find the ones with libraries mentioned for set 2
for f in overall_jsons:
    f_path = os.path.join(data_path, f)
    with open(f_path, 'r', encoding='utf-8') as f_obj:
        f_data = f_obj.read()
    essay = f.split(".")[0]
    if 'librar' in f_data and 'computer' not in f_data and f'{essay}.json' in os.listdir(data_path):
        essays.append(f'{essay}.json')

# get sample of essays
sample_jsons = random.sample(essays, 24)

# collect data from jsons
students = []
transition_counts = []
academic_counts = []
argument_counts = []
for f in sample_jsons:
    f_path = os.path.join(data_path, f)
    with open(f_path, 'r') as f_obj:
        f_data = json.load(f_obj)
    text_path = f'{f_path.rsplit(".")[0]}.unmasked'
    with open(text_path, 'r', encoding='utf-8') as text_obj:
        text = text_obj.read()
    student = {
        'id': f,
        'text': {
            'emotionwords': {
                'id': 'emotionwords',
                'value': [f_data['doctokens'][i] for i in f_data['emotionwords']],
                'label': 'Emotion words'
            },
            'concretedetails': {
                'id': 'concretedetails',
                'value': [f_data['doctokens'][i] for i in f_data['concretedetails']],
                'label': 'Concrete details'
            },
            'argumentwords': {
                'id': 'argumentwords',
                'value': [f_data['doctokens'][i] for i in f_data['argumentwords']],
                'label': 'Argument words'
            },
            'transitionwords': {
                'id': 'transitionwords',
                'value':  list(f_data['transitionprofile'][2].keys()),
                'label': 'Transitions used'
            },
            'studenttext': {
                'id': 'studenttext',
                'value': text,
                'label': 'Student text'
            }
        },
        'metrics': {
            'sentences': {'id': 'sentences', 'value': len(f_data['sentences']), 'label': ' sentences'}
        },
        'indicators': {}
    }
    transition_counts.append(f_data['transitionprofile'][0])

    # this will ignore the blanks and periods/commas
    # TODO fix this, not good to rely on the academics attribtue
    total_words = len([x for x in f_data['academics'] if x == 1 or x == 0])
    
    academic_counts.append(len([x for x in f_data['academics'] if x == 1]) / total_words)
    argument_counts.append(len(f_data['argumentwords']) / total_words)
    students.append(student)

# collect indicator information (percentiles)
for i, s in enumerate(students):
    s['indicators']['transitions'] = {
        'id': 'transitions',
        'value': int(stats.percentileofscore(transition_counts, transition_counts[i])),
        'label': 'Transitions',
        'help': 'Percentile based on total number of transitions used'
    }
    s['indicators']['academiclanguage'] = {
        'id': 'academiclanguage',
        'value': int(stats.percentileofscore(academic_counts, academic_counts[i])),
        'label': 'Academic Language',
        'help': 'Percentile based on percent of academic language used'
    }
    s['indicators']['argumentlanguage'] = {
        'id': 'argumentlanguage',
        'value': int(stats.percentileofscore(argument_counts, argument_counts[i])),
        'label': 'Argument Language',
        'help': 'Percentile based on percent of argument words used'
    }

with open(os.path.join(cwd, 'data', 'sample.json'), 'w') as f:
    json.dump(students, f, indent=4)
