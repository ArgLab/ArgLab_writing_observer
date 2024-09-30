import functools

import learning_observer.log_event
import learning_observer.schoology
import learning_observer.util
import learning_observer.auth
import learning_observer.lms_integration
import learning_observer.constants as constants


LMS_NAME = constants.SCHOOLOGY

SCHOOLOGY_ENDPOINTS = list(map(lambda x: learning_observer.lms_integration.Endpoint(*x, "", None, LMS_NAME), [
    ("course_list", "/courses"),
    ("course_sections", "/courses/{courseId}/sections"),
    ("course_roster", "/sections/{sectionId}/enrollments"),
    ("course_assignments", "/sections/{sectionId}/assignments"),
    ("course_assignments_submissions", "/sections/{courseId}/assignments/{assignmentId}/submissions/{gradeItemId}"),
]))

register_cleaner_with_endpoints = functools.partial(learning_observer.lms_integration.register_cleaner, endpoints=SCHOOLOGY_ENDPOINTS)

        
class SchoologyLMS(learning_observer.lms_integration.LMS):
    def __init__(self):
        super().__init__(lms_name=LMS_NAME, endpoints=SCHOOLOGY_ENDPOINTS)
        
    @register_cleaner_with_endpoints("course_roster", "roster")
    def clean_course_roster(schoology_json):
        students = schoology_json.get('enrollment', [])
        students_updated = []
        for student_json in students:
            schoology_id = student_json['id']
            integration_id = student_json['integration_id']
            local_id = learning_observer.auth.google_id_to_user_id(integration_id)
            student = {
                "course_id": "1",
                "user_id": local_id,
                "profile": {
                    "id": schoology_id,
                    "name": {
                        "given_name": student_json['name'],
                        "family_name": student_json['name'],
                        "full_name": student_json['name']
                    }
                }
            }
            if 'external_ids' not in student_json:
                student_json['external_ids'] = []
            student_json['external_ids'].append({"source": constants.SCHOOLOGY, "id": integration_id})
            students_updated.append(student)
        return students_updated

    @register_cleaner_with_endpoints("course_list", "courses")
    async def clean_course_list(schoology_json):
        courses = schoology_json.get('course', [])
        courses.sort(key=lambda course: course.get('title', 'ZZ'))
        
        # For each course, fetch the sections
        for course in courses:
            course_id = course['id']
            
            # Fetch the sections for each course
            sections_json = await learning_observer.schoology.sections(course_id)
            sections = sections_json.get('section', [])
            
            # Add the sections to the course data
            course['sections'] = sections
            
        return courses
    
    @register_cleaner_with_endpoints("course_sections", "sections")
    async def clean_course_section_list(schoology_json):
        sections = schoology_json.get('section', [])
        sections.sort(key=lambda course: course.get('title', 'ZZ'))
        
        return sections
          
    @register_cleaner_with_endpoints("course_assignments", "assignments")
    def clean_course_assignment_list(schoology_json):
        assignments = schoology_json
        assignments.sort(key=lambda x: x.get('name', 'ZZ'))
        return assignments
    
schoology_lms = SchoologyLMS()

def initialize_routes(app):
    schoology_lms.initialize_routes(app)
