# package imports
import json
import os
import random
from scipy import stats

cwd = os.getcwd()
data_path = os.path.join(cwd, 'kaggle_processed')

# get sample of essays
overall_jsons = [f for f in os.listdir(data_path) if f.endswith('.json')]
sample_jsons = random.sample(overall_jsons, 24)


# collect data from jsons
students = []
transition_counts = []
academic_counts = []
for f in sample_jsons:
    f_path = os.path.join(data_path, f)
    with open(f_path, 'r') as f_obj:
        f_data = json.load(f_obj)
    student = {
        'id': f,
        'text': {
            'emotionwords': {
                'id': 'emotionwords',
                'value': [f_data['doctokens'][i] for i in f_data['emotionwords']],
                'label': 'Emotion words used'
            },
            'concretedetails': {
                'id': 'contretedetails',
                'value': [f_data['doctokens'][i] for i in f_data['concretedetails']],
                'label': 'Concrete details'
            },
            'transitionwords': {
                'id': 'transitionwords',
                'value':  list(f_data['transitionprofile'][2].keys()),
                'label': 'Transitions used'
            }
        },
        'metrics': {
            'sentences': {'id': 'sentences', 'value': len(f_data['sentences']), 'label': ' sentences'}
        },
        'indicators': {}
    }
    transition_counts.append(f_data['transitionprofile'][0])
    academic_counts.append(len([x for x in f_data['academics'] if x == 1]) / len([x for x in f_data['academics'] if x == 1 or x == 0]))
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

with open(os.path.join(cwd, 'sample.json'), 'w') as f:
    json.dump(students, f, indent=4)
