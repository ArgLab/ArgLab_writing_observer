import functools

import learning_observer.auth
import learning_observer.lms_integration
import learning_observer.constants as constants


LMS_NAME = constants.CANVAS

CANVAS_ENDPOINTS = list(map(lambda x: learning_observer.lms_integration.Endpoint(*x, "", None, LMS_NAME), [
    ("course_list", "/courses"),
    ("course_roster", "/courses/{courseId}/students"),
    ("course_assignments", "/courses/{courseId}/assignments"),
    ("course_assignments_submissions", "/courses/{courseId}/assignments/{assignmentId}/submissions"),
]))

register_cleaner_with_endpoints = functools.partial(learning_observer.lms_integration.register_cleaner, endpoints=CANVAS_ENDPOINTS)

        
class CanvasLMS(learning_observer.lms_integration.LMS):
    def __init__(self):
        super().__init__(lms_name=LMS_NAME, endpoints=CANVAS_ENDPOINTS)
        
    @register_cleaner_with_endpoints("course_roster", "roster")
    def clean_course_roster(canvas_json):
        students = canvas_json
        students_updated = []
        for student_json in students:
            canvas_id = student_json['id']
            integration_id = student_json['integration_id']
            local_id = learning_observer.auth.google_id_to_user_id(integration_id)
            student = {
                "course_id": "1",
                "user_id": local_id,
                "profile": {
                    "id": canvas_id,
                    "name": {
                        "given_name": student_json['name'],
                        "family_name": student_json['name'],
                        "full_name": student_json['name']
                    }
                }
            }
            if 'external_ids' not in student_json:
                student_json['external_ids'] = []
            student_json['external_ids'].append({"source": constants.CANVAS, "id": integration_id})
            students_updated.append(student)
        return students_updated

    @register_cleaner_with_endpoints("course_list", "courses")
    def clean_course_list(canvas_json):
        courses = canvas_json
        courses.sort(key=lambda x: x.get('name', 'ZZ'))
        return courses
    
    @register_cleaner_with_endpoints("course_assignments", "assignments")
    def clean_course_assignment_list(canvas_json):
        assignments = canvas_json
        assignments.sort(key=lambda x: x.get('name', 'ZZ'))
        return assignments
    
canvas_lms = CanvasLMS()

def initialize_canvas_routes(app):
    canvas_lms.initialize_routes(app)
