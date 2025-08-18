#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import AssignedCourse, RegistrationOfficerAssignment
from django.contrib.auth.models import User

print("👨‍🏫 LECTURER DETAILS CHECK")
print("=" * 50)

# Check all users and their roles
print("\n👤 ALL USERS:")
users = User.objects.all()
for user in users:
    print(f"  - {user.username} ({user.email})")
    print(f"    - Superuser: {'Yes' if user.is_superuser else 'No'}")
    print(f"    - Staff: {'Yes' if user.is_staff else 'No'}")
    print(f"    - Active: {'Yes' if user.is_active else 'No'}")
    print(f"    - Date Joined: {user.date_joined}")
    print()

# Check course assignments
print("\n📚 COURSE ASSIGNMENTS:")
assigned_courses = AssignedCourse.objects.all()
if assigned_courses:
    for assignment in assigned_courses:
        print(f"  - {assignment.lecturer.username} → {assignment.course.code} ({assignment.session}, {assignment.semester})")
else:
    print("  ❌ No course assignments found")

# Check registration officer assignments
print("\n🗂️ REGISTRATION OFFICER ASSIGNMENTS:")
officer_assignments = RegistrationOfficerAssignment.objects.all()
if officer_assignments:
    for assignment in officer_assignments:
        print(f"  - {assignment.lecturer.username} → {assignment.department} Level {assignment.level} ({assignment.session}, {assignment.semester})")
else:
    print("  ❌ No registration officer assignments found")

print("\n" + "=" * 50)
print("✅ Lecturer check complete!")
