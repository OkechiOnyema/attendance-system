#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import Student, CourseEnrollment, Course
from django.contrib.auth.models import User

print("🔍 STUDENT ERROR CHECK")
print("=" * 50)

# Check for students with missing/invalid data
print("\n❌ STUDENTS WITH ERRORS:")
students_with_errors = []
for student in Student.objects.all():
    errors = []
    
    # Check for missing department
    if not student.department:
        errors.append("Missing department")
    
    # Check for missing level
    if not student.level:
        errors.append("Missing level")
    
    # Check for duplicate names
    duplicate_names = Student.objects.filter(name=student.name).exclude(matric_no=student.matric_no)
    if duplicate_names.exists():
        errors.append(f"Duplicate name with: {[s.matric_no for s in duplicate_names]}")
    
    if errors:
        students_with_errors.append((student, errors))
        print(f"  - {student.matric_no}: {student.name}")
        for error in errors:
            print(f"    ❌ {error}")

if not students_with_errors:
    print("  ✅ No students with errors found")

# Check course enrollment issues
print("\n📘 COURSE ENROLLMENT ISSUES:")

# Check for duplicate enrollments
print("\n  🔍 Duplicate Enrollments:")
duplicate_enrollments = []
for student in Student.objects.all():
    for course in Course.objects.all():
        enrollments = CourseEnrollment.objects.filter(student=student, course=course)
        if enrollments.count() > 1:
            duplicate_enrollments.append((student, course, enrollments.count()))
            print(f"    - {student.name} enrolled {enrollments.count()} times in {course.code}")

if not duplicate_enrollments:
    print("    ✅ No duplicate enrollments found")

# Check for enrollments in non-existent courses
print("\n  🔍 Invalid Course References:")
invalid_enrollments = []
for enrollment in CourseEnrollment.objects.all():
    try:
        # This will fail if course doesn't exist
        course = enrollment.course
    except:
        invalid_enrollments.append(enrollment)
        print(f"    - {enrollment.student.name} enrolled in non-existent course")

if not invalid_enrollments:
    print("    ✅ All course references are valid")

# Check for students enrolled in multiple similar courses
print("\n  🔍 Multiple Similar Courses:")
similar_courses = {
    'CS101': 'Introduction to Computer Science',
    'CSC101': 'Introduction to Computer Science'
}

for student in Student.objects.all():
    cs_courses = CourseEnrollment.objects.filter(
        student=student, 
        course__code__in=['CS101', 'CSC101']
    )
    if cs_courses.count() > 1:
        print(f"    - {student.name} enrolled in multiple CS courses:")
        for enrollment in cs_courses:
            print(f"      * {enrollment.course.code}: {enrollment.course.title}")

# Summary
print("\n" + "=" * 50)
print("📊 SUMMARY:")
print(f"  - Total Students: {Student.objects.count()}")
print(f"  - Students with Errors: {len(students_with_errors)}")
print(f"  - Total Enrollments: {CourseEnrollment.objects.count()}")
print(f"  - Duplicate Enrollments: {len(duplicate_enrollments)}")
print(f"  - Invalid References: {len(invalid_enrollments)}")

print("\n✅ Student error check complete!")
