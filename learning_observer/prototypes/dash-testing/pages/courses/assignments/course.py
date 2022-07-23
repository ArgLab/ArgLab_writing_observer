# package imports
import dash_bootstrap_components as dbc
from faker import Faker

# local imports
from .assignment import Assignment

fake = Faker()

class Course:
    def __init__(self, id, role):
        self.id = id
        self.name = f'Course {id}'
        self.role = role

        if role == 'teacher':
            self.students = self.fetch_students()
            self.assignments = self.fetch_assignments()
        elif role == 'student':
            self.dashboard = 'BRUH'
        else:
            self.dashboard = 'No role'

    def fetch_students(self):
        return [
            {
                'id': i,
                'name': fake.name()
            } for i in range(15)
        ]

    def fetch_assignments(self):
        return [
            Assignment(i, f'Assignment {i}', fake.text())
            for i in range(12)
        ]
