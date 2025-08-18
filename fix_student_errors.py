#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import Student, CourseEnrollment, Course
from django.contrib.auth.models import User

print("🔧 FIXING STUDENT ERRORS")
print("=" * 50)

# Fix 1: Remove duplicate John Doe (keep the complete one)
print("\n1️⃣ FIXING DUPLICATE STUDENTS:")
john_doe_students = Student.objects.filter(name="John Doe")
if john_doe_students.count() > 1:
    print("  Found duplicate John Doe students:")
    for student in john_doe_students:
        print(f"    - {student.matric_no}: {student.name} (Dept: {student.department}, Level: {student.level})")
    
    # Keep the one with complete data (2024001), remove the incomplete one
    incomplete_john = john_doe_students.filter(department__isnull=True).first()
    if incomplete_john:
        print(f"  🗑️ Removing incomplete student: {incomplete_john.matric_no}")
        incomplete_john.delete()
        print("  ✅ Duplicate removed")
    else:
        print("  ℹ️ No incomplete John Doe found to remove")
else:
    print("  ✅ No duplicate John Doe students found")

# Fix 2: Add missing departments and levels
print("\n2️⃣ FIXING MISSING DEPARTMENT/LEVEL:")
students_to_fix = Student.objects.filter(department__isnull=True) | Student.objects.filter(level__isnull=True)

if students_to_fix.exists():
    print("  Fixing students with missing data:")
    
    # Define default values based on matric number patterns
    for student in students_to_fix:
        print(f"    - {student.matric_no}: {student.name}")
        
        # Set department based on matric number pattern
        if student.department is None:
            if student.matric_no.startswith('SEN'):
                student.department = "Computer Science"
                print(f"      ✅ Set department: Computer Science")
            elif student.matric_no.startswith('ARE'):
                student.department = "Architecture"
                print(f"      ✅ Set department: Architecture")
            else:
                student.department = "General Studies"
                print(f"      ✅ Set department: General Studies")
        
        # Set level based on matric number pattern
        if student.level is None:
            if '20' in student.matric_no:
                student.level = "200"
                print(f"      ✅ Set level: 200")
            else:
                student.level = "100"
                print(f"      ✅ Set level: 100")
        
        student.save()
        print(f"      💾 Student data updated")
else:
    print("  ✅ No students with missing department/level")

# Fix 3: Clean up duplicate course enrollments
print("\n3️⃣ CLEANING UP COURSE ENROLLMENTS:")
# Remove duplicate enrollments for the same student-course combination
duplicates_removed = 0
for student in Student.objects.all():
    for course in Course.objects.all():
        enrollments = CourseEnrollment.objects.filter(student=student, course=course)
        if enrollments.count() > 1:
            # Keep the first one, remove the rest
            first_enrollment = enrollments.first()
            enrollments.exclude(id=first_enrollment.id).delete()
            duplicates_removed += enrollments.count() - 1
            print(f"    🗑️ Removed {enrollments.count() - 1} duplicate enrollments for {student.name} in {course.code}")

if duplicates_removed == 0:
    print("  ✅ No duplicate enrollments found")

# Fix 4: Remove duplicate courses (CS101 vs CSC101)
print("\n4️⃣ FIXING DUPLICATE COURSES:")
cs101_course = Course.objects.filter(code='CS101').first()
csc101_course = Course.objects.filter(code='CSC101').first()

if cs101_course and csc101_course:
    print("  Found duplicate CS courses:")
    print(f"    - CS101: {cs101_course.title}")
    print(f"    - CSC101: {csc101_course.title}")
    
    # Move all enrollments from CSC101 to CS101
    csc101_enrollments = CourseEnrollment.objects.filter(course=csc101_course)
    for enrollment in csc101_enrollments:
        # Check if student is already enrolled in CS101
        existing = CourseEnrollment.objects.filter(student=enrollment.student, course=cs101_course).first()
        if not existing:
            enrollment.course = cs101_course
            enrollment.save()
            print(f"      ✅ Moved {enrollment.student.name} from CSC101 to CS101")
        else:
            enrollment.delete()
            print(f"      🗑️ Removed duplicate enrollment for {enrollment.student.name}")
    
    # Remove the duplicate course
    csc101_course.delete()
    print("  🗑️ Removed duplicate CSC101 course")
else:
    print("  ✅ No duplicate CS courses found")

print("\n" + "=" * 50)
print("✅ Student error fixing complete!")

# Final verification
print("\n🔍 FINAL VERIFICATION:")
final_check = Student.objects.all()
print(f"  - Total Students: {final_check.count()}")
print(f"  - Students with complete data: {final_check.filter(department__isnull=False, level__isnull=False).count()}")
print(f"  - Total Enrollments: {CourseEnrollment.objects.count()}")
print(f"  - Total Courses: {Course.objects.count()}")
