#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import Student, CourseEnrollment, Course

print("=== CURRENT ENROLLMENT STATE ===")

# Check all students
students = Student.objects.all()
print(f"\nTotal students: {students.count()}")
for s in students:
    print(f"- {s.matric_no}: {s.name}")

# Check all enrollments
enrollments = CourseEnrollment.objects.all()
print(f"\nTotal enrollments: {enrollments.count()}")
for e in enrollments:
    print(f"- {e.student.matric_no} in {e.course.code} ({e.session}, {e.semester})")

# Check course-specific enrollments
print(f"\n=== COURSE-SPECIFIC ENROLLMENTS ===")
courses = Course.objects.all()
for course in courses:
    course_enrollments = CourseEnrollment.objects.filter(course=course)
    print(f"\n{course.code} ({course.title}): {course_enrollments.count()} students")
    for e in course_enrollments:
        print(f"  - {e.student.matric_no} ({e.student.name})")
