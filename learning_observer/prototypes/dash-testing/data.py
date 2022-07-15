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
        'data': {
            'metric 1': random.choice(levels),
            'metric 2': random.choice(levels),
            'metric 3': random.choice(levels),
            'metric 4': random.choice(levels),
        },
        'class_name': random.choice(class_names)
    } for i in range(10)
]
