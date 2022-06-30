# package imports
from faker import Faker

fake = Faker()

students = [
    {'name': fake.name(), 'id': i, 'text': fake.text()} for i in range(10)
]
