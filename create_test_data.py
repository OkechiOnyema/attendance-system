#!/usr/bin/env python
import os
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import Course, Student, CourseEnrollment
from django.contrib.auth.models import User

print("🚀 CREATING TEST DATA")
print("=" * 50)

# Create test courses
print("\n📚 Creating test courses...")
courses_data = [
    {"code": "CS101", "title": "Introduction to Computer Science"},
    {"code": "MATH201", "title": "Advanced Mathematics"},
    {"code": "ENG101", "title": "English Composition"},
]

courses = []
for course_data in courses_data:
    course, created = Course.objects.get_or_create(
        code=course_data["code"],
        defaults={"title": course_data["title"]}
    )
    if created:
        print(f"  ✅ Created course: {course.code} - {course.title}")
    else:
        print(f"  ℹ️ Course already exists: {course.code} - {course.title}")
    courses.append(course)

# Create test students
print("\n🎓 Creating test students...")
students_data = [
    {"matric_no": "2024001", "name": "John Doe", "department": "Computer Science", "level": "100"},
    {"matric_no": "2024002", "name": "Jane Smith", "department": "Mathematics", "level": "200"},
    {"matric_no": "2024003", "name": "Bob Johnson", "department": "Computer Science", "level": "100"},
]

students = []
for student_data in students_data:
    student, created = Student.objects.get_or_create(
        matric_no=student_data["matric_no"],
        defaults={
            "name": student_data["name"],
            "department": student_data["department"],
            "level": student_data["level"]
        }
    )
    if created:
        print(f"  ✅ Created student: {student.name} ({student.matric_no})")
    else:
        print(f"  ℹ️ Student already exists: {student.name} ({student.matric_no})")
    students.append(student)

# Create test enrollments
print("\n📘 Creating test enrollments...")
enrollments_data = [
    {"student": students[0], "course": courses[0]},  # John Doe in CS101
    {"student": students[1], "course": courses[1]},  # Jane Smith in MATH201
    {"student": students[2], "course": courses[0]},  # Bob Johnson in CS101
    {"student": students[0], "course": courses[2]},  # John Doe in ENG101
]

for enrollment_data in enrollments_data:
    enrollment, created = CourseEnrollment.objects.get_or_create(
        student=enrollment_data["student"],
        course=enrollment_data["course"]
    )
    if created:
        print(f"  ✅ Enrolled {enrollment.student.name} in {enrollment.course.code}")
    else:
        print(f"  ℹ️ Enrollment already exists: {enrollment.student.name} in {enrollment.course.code}")

print("\n" + "=" * 50)
print("✅ Test data creation complete!")
print("\n🔍 Now you can:")
print("  1. Check Django Admin: http://localhost:8000/admin/")
print("  2. Check Frontend: http://localhost:8000/admin-panel/")
print("  3. Run: python check_database.py")
