# scripts/import_courses.py

import os
import django
import csv

# ✅ Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Attendance-System.settings')
django.setup()

from admin_ui.models import Course
from admin_ui.utils import load_courses_from_csv

def import_courses():
    filepath = 'courses.csv'  # Adjust path if needed
    courses = load_courses_from_csv(filepath)

    if not courses:
        print("⚠️ No courses found in CSV.")
        return

    for course in courses:
        obj, created = Course.objects.get_or_create(
            code=course['code'],
            defaults={'title': course['title']}
        )
        if created:
            print(f"✅ Added: {course['code']} – {course['title']}")
        else:
            print(f"🔁 Already exists: {course['code']}")

if __name__ == '__main__':
    import_courses()
