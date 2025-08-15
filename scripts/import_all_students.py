import os
from admin_ui.models import Student
from admin_ui.utils import load_students_from_csv

STUDENT_FOLDER = 'data/students/'

for filename in os.listdir(STUDENT_FOLDER):
    if filename.endswith('.csv'):
        filepath = os.path.join(STUDENT_FOLDER, filename)
        print(f"Importing from {filepath}...")
        students = load_students_from_csv(filepath)
        for student in students:
            Student.objects.get_or_create(
                matric_no=student['matric_no'],
                defaults={
                    'full_name': student['full_name'],
                    'level': student['level']
                }
            )
