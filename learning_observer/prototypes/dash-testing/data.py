# package imports
from faker import Faker
import random

fake = Faker()

class_names = [
    'border-3 border-primary',
    'border-3 border-secondary',
    'border-3 border-warning',
]
levels = [
    'high', 'mid', 'low'
]
students = [
    {
        'name': fake.name(),
        'id': i,
        'text': fake.text(),
        'sentences': random.randint(5, 20),
        'paragraphs': random.randint(1, 4),
        'unique_words': random.randint(5, 20),
        'time_on_task': random.randint(15,100),
        'data': {
            'transition words': random.choice(levels),
            'effective use of synonyms': random.choice(levels),
            'subject-verb agreement': random.choice(levels),
            'formal language': random.choice(levels),
        },
        'class_name': random.choice(class_names)
    } for i in range(10)
]
