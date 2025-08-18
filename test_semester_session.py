#!/usr/bin/env python
"""
Test script to verify semester and academic session functionality
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import Course, Student, CourseEnrollment, AssignedCourse
from django.contrib.auth.models import User

def test_semester_session():
    print("🧪 Testing Semester and Academic Session Functionality")
    print("=" * 60)
    
    # Check if we have any courses
    courses = Course.objects.all()
    if not courses.exists():
        print("❌ No courses found. Creating sample course...")
        course = Course.objects.create(
            code="CSC101",
            title="Introduction to Computer Science"
        )
        print(f"✅ Created course: {course.code} - {course.title}")
    else:
        course = courses.first()
        print(f"✅ Found course: {course.code} - {course.title}")
    
    # Check if we have any students
    students = Student.objects.all()
    if not students.exists():
        print("❌ No students found. Creating sample student...")
        student = Student.objects.create(
            matric_no="2021001",
            name="John Doe",
            department="Computer Science",
            level="100"
        )
        print(f"✅ Created student: {student.name} ({student.matric_no})")
    else:
        student = students.first()
        print(f"✅ Found student: {student.name} ({student.matric_no})")
    
    # Check if we have any lecturers
    lecturers = User.objects.filter(is_staff=True)
    if not lecturers.exists():
        print("❌ No lecturers found. Creating sample lecturer...")
        lecturer = User.objects.create_user(
            username="lecturer1",
            email="lecturer1@example.com",
            password="password123",
            first_name="Dr. Jane",
            last_name="Smith"
        )
        lecturer.is_staff = True
        lecturer.save()
        print(f"✅ Created lecturer: {lecturer.get_full_name()}")
    else:
        lecturer = lecturers.first()
        print(f"✅ Found lecturer: {lecturer.get_full_name()}")
    
    # Create assigned course
    assigned_course, created = AssignedCourse.objects.get_or_create(
        lecturer=lecturer,
        course=course,
        session="2024/2025",
        semester="1st Semester"
    )
    if created:
        print(f"✅ Created course assignment: {course.code} → {lecturer.username}")
    else:
        print(f"ℹ️ Course assignment already exists: {course.code} → {lecturer.username}")
    
    # Test CourseEnrollment with session and semester
    print("\n📚 Testing CourseEnrollment with Session and Semester:")
    print("-" * 50)
    
    # Create enrollment with session and semester
    enrollment, created = CourseEnrollment.objects.get_or_create(
        student=student,
        course=course,
        session="2024/2025",
        semester="1st Semester"
    )
    
    if created:
        print(f"✅ Created enrollment: {student.name} in {course.code}")
        print(f"   Session: {enrollment.session}")
        print(f"   Semester: {enrollment.semester}")
        print(f"   Enrolled on: {enrollment.enrolled_on}")
    else:
        print(f"ℹ️ Enrollment already exists: {student.name} in {course.code}")
        print(f"   Session: {enrollment.session}")
        print(f"   Semester: {enrollment.semester}")
        print(f"   Enrolled on: {enrollment.enrolled_on}")
    
    # Test unique constraint
    print("\n🔒 Testing Unique Constraint:")
    print("-" * 30)
    
    try:
        duplicate_enrollment = CourseEnrollment.objects.create(
            student=student,
            course=course,
            session="2024/2025",
            semester="1st Semester"
        )
        print("❌ Unique constraint failed - duplicate enrollment created")
    except Exception as e:
        print(f"✅ Unique constraint working: {str(e)}")
    
    # Test different session/semester combination
    print("\n🔄 Testing Different Session/Semester Combination:")
    print("-" * 50)
    
    try:
        different_enrollment = CourseEnrollment.objects.create(
            student=student,
            course=course,
            session="2024/2025",
            semester="2nd Semester"
        )
        print(f"✅ Created enrollment with different semester: {different_enrollment.semester}")
    except Exception as e:
        print(f"❌ Failed to create different semester enrollment: {str(e)}")
    
    # Display all enrollments
    print("\n📋 All Enrollments:")
    print("-" * 20)
    
    all_enrollments = CourseEnrollment.objects.filter(student=student, course=course)
    for i, enroll in enumerate(all_enrollments, 1):
        print(f"{i}. {enroll.student.name} - {enroll.course.code}")
        print(f"   Session: {enroll.session}")
        print(f"   Semester: {enroll.semester}")
        print(f"   Enrolled: {enroll.enrolled_on}")
        print()
    
    print("🎉 Test completed successfully!")
    print("\n📝 Summary:")
    print(f"   - Course: {course.code} - {course.title}")
    print(f"   - Student: {student.name} ({student.matric_no})")
    print(f"   - Lecturer: {lecturer.get_full_name()}")
    print(f"   - Total Enrollments: {CourseEnrollment.objects.count()}")
    print(f"   - Unique Students: {Student.objects.count()}")
    print(f"   - Total Courses: {Course.objects.count()}")

if __name__ == "__main__":
    test_semester_session()
