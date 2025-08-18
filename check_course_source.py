#!/usr/bin/env python
import os
import django
import csv

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import Course, CourseEnrollment

print("📚 COURSE SOURCE VERIFICATION")
print("=" * 50)

# Read courses from CSV
print("\n📖 COURSES FROM CSV SOURCE:")
csv_courses = []
try:
    with open('courses.csv', 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header
        for row in csv_reader:
            if len(row) >= 2:
                code = row[0].strip()
                title = row[1].strip()
                csv_courses.append({'code': code, 'title': title})
                print(f"  - {code}: {title}")
except FileNotFoundError:
    print("  ❌ courses.csv file not found!")
except Exception as e:
    print(f"  ❌ Error reading CSV: {e}")

# Get courses from database
print("\n🗄️ COURSES IN DATABASE:")
db_courses = Course.objects.all()
for course in db_courses:
    print(f"  - {course.code}: {course.title}")

# Compare and identify differences
print("\n🔍 COURSE COMPARISON:")

# Find courses in DB but not in CSV (manually added)
db_only_courses = []
for course in db_courses:
    if not any(csv_course['code'] == course.code for csv_course in csv_courses):
        db_only_courses.append(course)
        print(f"  ❌ {course.code}: {course.title} - NOT in CSV (manually added)")

# Find courses in CSV but not in DB (missing)
csv_only_courses = []
for csv_course in csv_courses:
    if not db_courses.filter(code=csv_course['code']).exists():
        csv_only_courses.append(csv_course)
        print(f"  ❌ {csv_course['code']}: {csv_course['title']} - NOT in DB (missing)")

# Find matching courses
matching_courses = []
for csv_course in csv_courses:
    db_course = db_courses.filter(code=csv_course['code']).first()
    if db_course:
        matching_courses.append((csv_course, db_course))
        print(f"  ✅ {csv_course['code']}: {csv_course['title']} - MATCHES")

# Check for title mismatches
print("\n🔍 TITLE MISMATCHES:")
for csv_course in csv_courses:
    db_course = db_courses.filter(code=csv_course['code']).first()
    if db_course and csv_course['title'] != db_course.title:
        print(f"  ⚠️ {csv_course['code']}:")
        print(f"    CSV: {csv_course['title']}")
        print(f"    DB:  {db_course.title}")

# Summary
print("\n" + "=" * 50)
print("📊 SUMMARY:")
print(f"  - Courses in CSV: {len(csv_courses)}")
print(f"  - Courses in DB: {db_courses.count()}")
print(f"  - Matching courses: {len(matching_courses)}")
print(f"  - DB only (manually added): {len(db_only_courses)}")
print(f"  - CSV only (missing from DB): {len(csv_only_courses)}")

# Check enrollments for non-CSV courses
if db_only_courses:
    print("\n⚠️ ENROLLMENTS IN NON-CSV COURSES:")
    for course in db_only_courses:
        enrollments = CourseEnrollment.objects.filter(course=course)
        if enrollments.exists():
            print(f"  - {course.code}: {enrollments.count()} enrollments")
            for enrollment in enrollments:
                print(f"    * {enrollment.student.name} ({enrollment.student.matric_no})")
        else:
            print(f"  - {course.code}: No enrollments (safe to remove)")

print("\n✅ Course source verification complete!")
