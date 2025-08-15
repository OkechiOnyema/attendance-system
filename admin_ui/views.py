# views.py — Part 1: Authentication & Lecturer Registration

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.http import HttpResponseForbidden
from urllib.parse import unquote
from .forms import (
    LecturerLoginForm,
    SuperUserCreationForm,
    SuperUserLoginForm,
    OfficerLoginForm,
    CSVUploadForm,
    StudentCSVUploadForm
)
from .models import (
    FingerprintStudent,
    RegistrationOfficerAssignment,
    AssignedCourse,
    Student,
    Course
)
from .utils import load_courses_from_csv
from datetime import datetime, timedelta
from django.utils import timezone

# 🔐 Superuser Login
def superuser_login_view(request):
    form = SuperUserLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user and user.is_superuser:
            login(request, user)
            messages.success(request, 'Welcome, Superuser!')
            return redirect('admin_ui:register_lecturer')
        messages.error(request, 'Invalid credentials or not a superuser.')
    return render(request, 'admin_ui/superuser_login.html', {'form': form})

# 🧾 Superuser Creation
def create_superuser_view(request):
    form = SuperUserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if form.cleaned_data['passkey'] == settings.SUPERUSER_PASSKEY:
            User.objects.create_superuser(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            messages.success(request, '✅ Superuser created successfully!')
            return redirect('superuser_login')
        messages.error(request, '❌ Invalid passkey.')
    return render(request, 'admin_ui/create_superuser.html', {'form': form})

# 👨‍🏫 Lecturer Login
def lecturer_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_authenticated:
            if hasattr(user, 'lecturerassignment') or AssignedCourse.objects.filter(lecturer=user).exists():
                login(request, user)
                messages.success(request, f"✅ Welcome, {user.username}!")
                return redirect('admin_ui:dashboard')
            else:
                messages.error(request, "❌ Access denied. You are not assigned to any courses.")
        else:
            messages.error(request, "❌ Invalid username or password.")
    
    return render(request, 'admin_ui/lecturer_login.html')

# 👨‍🎓 Student Login
def student_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_authenticated:
            # Check if user is a student (has student profile or is enrolled in courses)
            try:
                student = Student.objects.get(user=user)
                if CourseEnrollment.objects.filter(student=student).exists():
                    login(request, user)
                    messages.success(request, f"✅ Welcome, {student.name}!")
                    return redirect('admin_ui:student_dashboard')
                else:
                    messages.error(request, "❌ Access denied. You are not enrolled in any courses.")
            except Student.DoesNotExist:
                messages.error(request, "❌ Access denied. Student profile not found.")
        else:
            messages.error(request, "❌ Invalid username or password.")
    
    return render(request, 'admin_ui/student_login.html')

# 🗂 Register Lecturer + Assign Courses + Officer
@login_required
@user_passes_test(lambda u: u.is_superuser)
def register_lecturer_view(request):
    courses = load_courses_from_csv('courses.csv')
    lecturers = User.objects.filter(groups__name='Lecturers')
    departments = ["Computer Science", "Electrical Engineering", "Mathematics", "Physics", "Statistics"]

    if request.method == 'POST':
        if 'register_lecturer' in request.POST:
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            department = request.POST.get('department')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password != confirm_password:
                messages.error(request, "❌ Passwords do not match.")
            elif User.objects.filter(email=email).exists():
                messages.warning(request, "Lecturer with this email already exists.")
            else:
                username = email.split("@")[0]
                lecturer = User.objects.create_user(username=username, email=email, password=password)
                group, _ = Group.objects.get_or_create(name='Lecturers')
                lecturer.groups.add(group)
                messages.success(request, "✅ Lecturer registered successfully!")

        elif 'assign_course' in request.POST:
            selected_lecturer_id = request.POST.get('selected_lecturer')
            selected_courses = request.POST.getlist('selected_courses')
            session = request.POST.get('session')
            semester = request.POST.get('semester')

            try:
                lecturer = User.objects.get(id=selected_lecturer_id)
                for course in courses:
                    if course['code'] in selected_courses:
                        course_obj, _ = Course.objects.get_or_create(
                            code=course['code'],
                            defaults={'title': course['title']}
                        )
                        AssignedCourse.objects.get_or_create(
                            lecturer=lecturer,
                            course=course_obj,
                            session=session,
                            semester=semester
                        )
                messages.success(request, "📚 Courses assigned successfully!")
            except User.DoesNotExist:
                messages.error(request, "Lecturer not found for course assignment.")

        elif 'assign_registration_officer' in request.POST:
            lecturer_id = request.POST.get('lecturer_id')
            session = request.POST.get('session')
            semester = request.POST.get('semester')
            level = request.POST.get('level')
            department = request.POST.get('department')

            try:
                lecturer = User.objects.get(id=lecturer_id)
                RegistrationOfficerAssignment.objects.create(
                    lecturer=lecturer,
                    session=session,
                    semester=semester,
                    level=level,
                    department=department
                )
                messages.success(request, "🛂 Registration officer assigned successfully!")
            except User.DoesNotExist:
                messages.error(request, "Lecturer not found for registration assignment.")

        return redirect('admin_ui:register_lecturer')

    assigned_officers = RegistrationOfficerAssignment.objects.all().order_by('-assigned_at')
    context = {
        'courses': courses,
        'lecturers': lecturers,
        'departments': departments,
        'assigned_officers': assigned_officers,
    }
    return render(request, 'admin_ui/register_lecturer.html', context)

# views.py — Part 2: Registration Officer Dashboard & CSV Handling

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib.auth.models import User
from .forms import CSVUploadForm, StudentCSVUploadForm
from .models import Student, FingerprintStudent, RegistrationOfficerAssignment, Course
from .utils import load_courses_from_csv
import csv
import os

# 🗂 Registration Officer Login
def registration_officer_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_authenticated:
            if RegistrationOfficerAssignment.objects.filter(lecturer=user).exists():
                login(request, user)
                messages.success(request, "✅ Welcome, Registration Officer!")
                return redirect('admin_ui:registration_officer_dashboard')
            else:
                messages.error(request, "❌ Access denied. You are not assigned as a registration officer.")
        else:
            messages.error(request, "❌ Invalid username or password.")
    
    return render(request, 'admin_ui/registration_officer_login.html')

# 🗂 Registration Officer Dashboard
@login_required
def registration_officer_dashboard(request):
    form = CSVUploadForm()
    assignments = RegistrationOfficerAssignment.objects.filter(lecturer=request.user)
    students = Student.objects.all()

    if request.method == 'POST':
        if 'csv_file' in request.FILES:
            form = CSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
                reader = csv.DictReader(decoded_file)

                for row in reader:
                    matric = (
                        row.get('matric_no') or row.get('matric_number') or
                        row.get('Matric Number') or row.get('Matric No') or
                        row.get('Matric') or row.get('matric')
                    )
                    name = row.get('name') or row.get('Name') or row.get('Full Name')
                    department = row.get('department') or row.get('Department') or ''
                    level = row.get('level') or row.get('Level') or ''
                    
                    if matric and name:
                        try:
                            Student.objects.update_or_create(
                                matric_no=matric.strip(),
                                defaults={
                                    'name': name.strip(),
                                    'department': department.strip() if department else None,
                                    'level': level.strip() if level else None
                                }
                            )
                        except Exception as e:
                            messages.error(request, f"❌ Error saving student {matric}: {str(e)}")
                            continue
                messages.success(request, "✅ Students uploaded successfully.")
                students = Student.objects.all()
            else:
                messages.error(request, "❌ Invalid CSV file.")

        elif 'matric_number' in request.POST:
            matric = request.POST.get('matric_number')
            try:
                student = Student.objects.get(matric_no=matric.strip())
                fingerprint, _ = FingerprintStudent.objects.get_or_create(student=student)
                if not fingerprint.fingerprint_data or fingerprint.fingerprint_data == 'not_enrolled':
                    fingerprint.fingerprint_data = "enrolled"
                    fingerprint.save()
                    messages.success(request, f"✅ Fingerprint enrolled for {student.name}")
                else:
                    messages.info(request, f"ℹ️ {student.name} is already enrolled.")
                # Redirect to refresh the page and show updated status
                return redirect('admin_ui:registration_officer_dashboard')
            except Student.DoesNotExist:
                messages.error(request, f"❌ Student with matric number {matric} not found.")

    context = {
        'form': form,
        'students': students,
        'assignments': assignments,
    }
    
    # Add enrollment status for each student to ensure template displays correctly
    for student in students:
        try:
            fingerprint = FingerprintStudent.objects.get(student=student)
            student.enrollment_status = fingerprint.fingerprint_data
        except FingerprintStudent.DoesNotExist:
            student.enrollment_status = 'not_enrolled'
    
    return render(request, 'admin_ui/registration_officer_dashboard.html', context)

# 📦 Upload CSV to Preview
@login_required
def upload_student_csv_view(request):
    form = StudentCSVUploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        csv_file = request.FILES['csv_file']
        file_path = default_storage.save(f'temp/{csv_file.name}', ContentFile(csv_file.read()))
        return redirect('preview_student_csv', file_path=file_path)
    return render(request, 'admin_ui/upload_students.html', {'form': form})

# 👁 Preview CSV contents
@login_required
def preview_student_csv_view(request, file_path):
    students = []
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    try:
        with open(full_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                matric = row.get('matric_number')
                name = row.get('name')
                department = row.get('department') or row.get('Department') or ''
                level = row.get('level') or row.get('Level') or ''
                if matric and name:
                    students.append({
                        'matric_number': matric.strip(), 
                        'name': name.strip(),
                        'department': department.strip() if department else '',
                        'level': level.strip() if level else ''
                    })
        return render(request, 'admin_ui/preview_students.html', {
            'students': students,
            'file_path': file_path
        })
    except Exception as e:
        messages.error(request, f"❌ Failed to load CSV: {e}")
        return redirect('upload_student_csv')

# ✅ Confirm Save to Database
@login_required
def confirm_student_csv_save_view(request):
    if request.method == 'POST':
        file_path = request.POST.get('file_path')
        full_path = default_storage.path(file_path)
        with open(full_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                matric = row.get('matric_number')
                name = row.get('name')
                department = row.get('department') or row.get('Department') or ''
                level = row.get('level') or row.get('Level') or ''
                if matric and name:
                    try:
                        Student.objects.update_or_create(
                            matric_no=matric.strip(),
                            defaults={
                                'name': name.strip(),
                                'department': department.strip() if department else None,
                                'level': level.strip() if level else None
                            }
                        )
                    except Exception as e:
                        messages.error(request, f"❌ Error saving student {matric}: {str(e)}")
                        continue
        messages.success(request, '✅ Students saved successfully!')
        return redirect('upload_student_csv')
    return redirect('upload_student_csv')

# views.py — Part 3: Fingerprint Enrollment, De-enrollment & Attendance

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse, NoReverseMatch
from .models import (
    Student,
    FingerprintStudent,
    CourseEnrollment,
    AssignedCourse,
    AttendanceSession,
    AttendanceRecord
)
from .utils import load_courses_from_csv
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 🧬 Enroll Fingerprint + Assign Courses
@login_required
def enroll_fingerprint_view(request, matric_no):
    # Decode the URL-encoded matric number
    matric_no = unquote(matric_no)
    student = get_object_or_404(Student, matric_no=matric_no)
    fingerprint, _ = FingerprintStudent.objects.get_or_create(student=student)
    courses = load_courses_from_csv('courses.csv')

    if request.method == 'POST':
        selected_courses = request.POST.getlist('selected_courses')
        fingerprint.fingerprint_data = "fingerprint_enrolled_hash"
        fingerprint.save()

        CourseEnrollment.objects.filter(student=student).delete()
        for course_data in courses:
            if course_data['code'] in selected_courses:
                # Create course enrollment with course data from CSV
                course_obj, _ = Course.objects.get_or_create(
                    code=course_data['code'],
                    defaults={'title': course_data['title']}
                )
                CourseEnrollment.objects.create(
                    student=student, 
                    course=course_obj
                )

        messages.success(request, f"✅ Fingerprint and course enrollment saved for {student.name}")

    enrolled_courses = CourseEnrollment.objects.filter(student=student)
    enrolled_course_codes = enrolled_courses.values_list('course__code', flat=True)

    context = {
        'student': student,
        'courses': courses,
        'fingerprint': fingerprint,
        'enrolled_course_codes': list(enrolled_course_codes),
        'enrolled_courses': enrolled_courses
    }
    return render(request, 'admin_ui/enroll_fingerprint.html', context)

# ❌ De-enroll Student
@require_POST
@login_required
def de_enroll_student(request, matric_no):
    # Decode the URL-encoded matric number
    matric_no = unquote(matric_no)
    student = get_object_or_404(Student, matric_no=matric_no)

    fingerprint = FingerprintStudent.objects.filter(student=student).first()
    if fingerprint:
        fingerprint.fingerprint_data = 'not_enrolled'
        fingerprint.save()
        logger.info(f"Fingerprint data cleared for {student.matric_no}")

    deleted_count, _ = CourseEnrollment.objects.filter(student=student).delete()
    logger.info(f"{deleted_count} course enrollments removed for {student.matric_no}")

    messages.warning(request, f"⚠️ {student.name} has been de-enrolled.")

    try:
        url = reverse('admin_ui:enroll_fingerprint', kwargs={'matric_no': student.matric_no})
    except NoReverseMatch:
        logger.error(f"Reverse failed for matric_no: {student.matric_no}")
        url = f'/admin-panel/enroll-fingerprint/{student.matric_no}/'

    return redirect(url)

# 👨‍🏫 Lecturer Dashboard
@login_required
def dashboard(request):
    assigned_courses = AssignedCourse.objects.filter(lecturer=request.user)
    
    # Get active network sessions for this lecturer (only today's sessions)
    today = timezone.now().date()
    active_network_sessions = NetworkSession.objects.filter(
        lecturer=request.user,
        is_active=True,
        date=today
    ).order_by('-created_at')
    
    # Get total students across all assigned courses (using CourseEnrollment for accurate count)
    # This counts unique students across all assigned courses
    total_students = Student.objects.filter(
        courseenrollment__course__in=[assigned.course for assigned in assigned_courses]
    ).distinct().count()
    
    # Alternative: Count students per course and sum (if you want total enrollments, not unique students)
    total_enrollments = 0
    for assigned in assigned_courses:
        enrolled_count = CourseEnrollment.objects.filter(
            course=assigned.course
        ).count()
        total_enrollments += enrolled_count
    
    # Get total active sessions count (all time, not just today)
    total_active_sessions = NetworkSession.objects.filter(
        lecturer=request.user,
        is_active=True
    ).count()
    
    # Get today's active sessions count
    today_active_sessions = active_network_sessions.count()
    
    # Get recent network sessions for display
    recent_sessions = NetworkSession.objects.filter(
        lecturer=request.user
    ).order_by('-date', '-start_time')[:5]
    
    return render(request, 'admin_ui/dashboard.html', {
        'assigned_courses': assigned_courses,
        'active_network_sessions': active_network_sessions,
        'total_students': total_students,  # Unique students across all courses
        'total_enrollments': total_enrollments,  # Total enrollments (may include duplicates)
        'recent_sessions': recent_sessions
    })

# 👨‍🎓 Student Dashboard
@login_required
def student_dashboard(request):
    """Dashboard for students to view their courses and attendance"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        # If no student profile exists, create one
        student = Student.objects.create(
            user=request.user,
            name=request.user.get_full_name() or request.user.username,
            matric_no=request.user.username
        )
    
    # Get enrolled courses
    enrolled_courses = CourseEnrollment.objects.filter(student=student)
    
    # Get attendance records
    attendance_records = AttendanceRecord.objects.filter(student=student).order_by('-attendance_session__date')
    
    # Get recent network sessions (for information)
    recent_sessions = NetworkSession.objects.filter(
        course__in=[enrollment.course for enrollment in enrolled_courses]
    ).order_by('-date')[:5]
    
    context = {
        'student': student,
        'enrolled_courses': enrolled_courses,
        'attendance_records': attendance_records,
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'admin_ui/student_dashboard.html', context)

# 📋 Attendance Form
@login_required
def course_attendance(request, assigned_id):
    assigned_course = get_object_or_404(AssignedCourse, id=assigned_id, lecturer=request.user)
    enrolled_students = Student.objects.filter(
        courseenrollment__course=assigned_course.course
    ).distinct()

    if request.method == 'POST':
        date_str = request.POST.get('date')
        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('course_attendance', assigned_id=assigned_id)

        session_obj, _ = AttendanceSession.objects.get_or_create(
            course=assigned_course.course,
            lecturer=request.user,
            session=assigned_course.session,
            semester=assigned_course.semester,
            date=attendance_date
        )

        for student in enrolled_students:
            status = request.POST.get(f'status_{student.matric_no}', 'absent')
            AttendanceRecord.objects.update_or_create(
                attendance_session=session_obj,
                student=student,
                defaults={'status': status}
            )

        messages.success(request, "✅ Attendance submitted successfully.")
        return redirect('admin_ui:dashboard')

    return render(request, 'admin_ui/course_attendance.html', {
        'assigned_course': assigned_course,
        'enrolled_students': enrolled_students
    })

# 📊 Superuser Attendance Dashboard
@login_required
@user_passes_test(lambda u: u.is_superuser)
def attendance_dashboard(request):
    students = Student.objects.all()
    return render(request, 'admin_ui/attendance.html', {'students': students})

# 📦 View All Assigned Courses
@login_required
@user_passes_test(lambda u: u.is_superuser)
def view_assignments(request):
    all_assignments = AssignedCourse.objects.all()
    return render(request, 'admin_ui/view_assignments.html', {'assignments': all_assignments})

# 🚪 Logout View
def logout_view(request):
    logout(request)
    messages.success(request, "✅ You have been successfully logged out.")
    return redirect('superuser_login')

# 🛰️ ESP32 Network-Based Attendance System

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib.auth.models import User
from .forms import CSVUploadForm, StudentCSVUploadForm
from .models import (
    Student,
    FingerprintStudent,
    RegistrationOfficerAssignment,
    Course,
    ESP32Device,
    NetworkSession,
    ConnectedDevice,
    AttendanceSession,
    AttendanceRecord
)
from .utils import load_courses_from_csv
import csv
import os
from django.utils import timezone
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Lecturers').exists())
def esp32_device_list(request):
    """List ESP32 devices for superusers and lecturers"""
    devices = ESP32Device.objects.all().order_by('-created_at')
    return render(request, 'admin_ui/esp32_device_list.html', {
        'devices': devices
    })

@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Lecturers').exists())
def esp32_device_create(request):
    """Create a new ESP32 device"""
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        device_name = request.POST.get('device_name')
        ssid = request.POST.get('ssid')
        password = request.POST.get('password')
        location = request.POST.get('location')
        
        if ESP32Device.objects.filter(device_id=device_id).exists():
            messages.error(request, 'Device ID already exists!')
        elif ESP32Device.objects.filter(ssid=ssid).exists():
            messages.error(request, 'SSID already exists!')
        else:
            ESP32Device.objects.create(
                device_id=device_id,
                device_name=device_name,
                ssid=ssid,
                password=password,
                location=location
            )
            messages.success(request, 'ESP32 device created successfully!')
            return redirect('admin_ui:esp32_device_list')
    
    return render(request, 'admin_ui/esp32_device_create.html')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Lecturers').exists())
def esp32_device_edit(request, device_id):
    """Edit an existing ESP32 device"""
    device = get_object_or_404(ESP32Device, device_id=device_id)
    
    if request.method == 'POST':
        device.device_name = request.POST.get('device_name')
        device.ssid = request.POST.get('ssid')
        device.password = request.POST.get('password')
        device.location = request.POST.get('location')
        device.is_active = 'is_active' in request.POST
        device.save()
        
        messages.success(request, 'ESP32 device updated successfully!')
        return redirect('admin_ui:esp32_device_list')
    
    return render(request, 'admin_ui/esp32_device_edit.html', {
        'device': device
    })

@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Lecturers').exists())
def esp32_device_delete(request, device_id):
    """Delete an ESP32 device"""
    device = get_object_or_404(ESP32Device, device_id=device_id)
    device.delete()
    messages.success(request, 'ESP32 device deleted successfully!')
    return redirect('admin_ui:esp32_device_list')

# 🌐 Network Session List
@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Lecturers').exists())
def network_session_list(request):
    """List network sessions for lecturers and superusers"""
    if request.user.is_superuser:
        all_sessions = NetworkSession.objects.all().order_by('-date', '-start_time')
    else:
        all_sessions = NetworkSession.objects.filter(lecturer=request.user).order_by('-date', '-start_time')
    
    # Separate active and past sessions
    active_sessions = all_sessions.filter(is_active=True)
    past_sessions = all_sessions.filter(is_active=False)
    
    # Calculate duration for each session
    for session in all_sessions:
        if session.end_time and session.start_time:
            # Calculate duration in minutes using DateTimeField
            duration = session.end_time - session.start_time
            session.duration_minutes = int(duration.total_seconds() / 60)
            session.duration_formatted = f"{session.duration_minutes} min"
        elif session.start_time and not session.end_time:
            # Session is still active, calculate duration from start to now
            current_time = timezone.now()
            duration = current_time - session.start_time
            session.duration_minutes = int(duration.total_seconds() / 60)
            session.duration_formatted = f"{session.duration_minutes} min (Ongoing)"
        else:
            # Fallback case
            session.duration_minutes = 0
            session.duration_formatted = "N/A"
    
    return render(request, 'admin_ui/network_session_list.html', {
        'active_sessions': active_sessions,
        'past_sessions': past_sessions
    })

@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Lecturers').exists())
def network_session_create(request):
    """Create a new network session"""
    if request.method == 'POST':
        course_id = request.POST.get('course')
        session = request.POST.get('session')
        semester = request.POST.get('semester')
        esp32_device_id = request.POST.get('esp32_device')
        
        if course_id and session and semester and esp32_device_id:
            try:
                course = Course.objects.get(id=course_id)
                esp32_device = ESP32Device.objects.get(id=esp32_device_id)
                duration_minutes = int(request.POST.get('duration', 90))
                
                # Get current time in local timezone (GMT+1)
                current_time = timezone.now()
                end_time = current_time + timedelta(minutes=duration_minutes)
                
                network_session = NetworkSession.objects.create(
                    course=course,
                    lecturer=request.user,
                    session=session,
                    semester=semester,
                    esp32_device=esp32_device,
                    date=current_time.date(),
                    start_time=current_time,  # Store full datetime instead of just time
                    end_time=end_time,  # Calculate end time based on duration
                    is_active=True
                )
                
                messages.success(request, f'Network session for {course.code} created successfully! Duration: {duration_minutes} minutes')
                return redirect('admin_ui:network_session_list')
                
            except (Course.DoesNotExist, ESP32Device.DoesNotExist):
                messages.error(request, 'Invalid course or ESP32 device selected!')
            except ValueError:
                messages.error(request, 'Invalid duration value! Please enter a valid number of minutes.')
        else:
            messages.error(request, 'Please fill in all required fields!')
    
    # Get assigned courses for this lecturer
    assigned_courses = AssignedCourse.objects.filter(lecturer=request.user)
    esp32_devices = ESP32Device.objects.filter(is_active=True)
    
    return render(request, 'admin_ui/network_session_create.html', {
        'assigned_courses': assigned_courses,
        'esp32_devices': esp32_devices
    })

@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Lecturers').exists())
def network_session_end(request, session_id):
    """End a network session"""
    network_session = get_object_or_404(NetworkSession, id=session_id)
    
    # Check if user has permission to end this session
    if not request.user.is_superuser and network_session.lecturer != request.user:
        messages.error(request, 'You do not have permission to end this session!')
        return redirect('admin_ui:network_session_list')
    
    # Get current time in the same timezone as the session
    current_time = timezone.now()
    network_session.end_time = current_time  # Store full datetime instead of just time
    network_session.is_active = False
    network_session.save()
    
    messages.success(request, f'Network session for {network_session.course.code} ended!')
    return redirect('admin_ui:network_session_list')

# 🔌 API Endpoints for ESP32 Communication

@csrf_exempt
def api_device_heartbeat(request):
    """ESP32 sends heartbeat to Django"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            
            if device_id:
                # Update or create ESP32 device record
                device, created = ESP32Device.objects.get_or_create(
                    device_id=device_id,
                    defaults={
                        'device_name': f'ESP32 Device {device_id}',
                        'ssid': 'Unknown',
                        'password': '',
                        'location': 'Unknown'
                    }
                )
                
                # Update last heartbeat
                device.last_heartbeat = timezone.now()
                device.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Heartbeat received',
                    'device_id': device_id,
                    'created': created
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def api_device_connected(request):
    """ESP32 reports device connection"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            mac_address = data.get('mac_address')
            device_name = data.get('device_name', 'Unknown Device')
            ip_address = data.get('ip_address', 'Unknown')
            
            if device_id and mac_address:
                # Find the ESP32 device
                try:
                    esp32_device = ESP32Device.objects.get(device_id=device_id)
                except ESP32Device.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'ESP32 device not found'}, status=404)
                
                # Check if there's an active network session
                active_session = NetworkSession.objects.filter(
                    esp32_device=esp32_device,
                    is_active=True
                ).first()
                
                if active_session:
                    # Create or update connected device record
                    connected_device, created = ConnectedDevice.objects.get_or_create(
                        network_session=active_session,
                        mac_address=mac_address,
                        defaults={
                            'device_name': device_name,
                            'ip_address': ip_address,
                            'is_connected': True,
                            'connected_at': timezone.now()
                        }
                    )
                    
                    if not created:
                        # Update existing record
                        connected_device.device_name = device_name
                        connected_device.ip_address = ip_address
                        connected_device.is_connected = True
                        connected_device.connected_at = timezone.now()
                        connected_device.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Device connection recorded',
                        'mac_address': mac_address,
                        'created': created,
                        'course': active_session.course.code
                    })
                else:
                    # No active session, just log the connection
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Device connected but no active session',
                        'mac_address': mac_address,
                        'course': 'No active session'
                    })
            else:
                return JsonResponse({'status': 'error', 'message': 'Device ID and MAC address required'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def api_device_disconnected(request):
    """ESP32 reports device disconnection"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            mac_address = data.get('mac_address')
            
            if device_id and mac_address:
                # Find the ESP32 device
                try:
                    esp32_device = ESP32Device.objects.get(device_id=device_id)
                except ESP32Device.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'ESP32 device not found'}, status=404)
                
                # Find and update connected device record
                try:
                    connected_device = ConnectedDevice.objects.get(
                        network_session__esp32_device=esp32_device,
                        mac_address=mac_address,
                        is_connected=True
                    )
                    connected_device.is_connected = False
                    connected_device.disconnected_at = timezone.now()
                    connected_device.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Device disconnection recorded',
                        'mac_address': mac_address
                    })
                except ConnectedDevice.DoesNotExist:
                    return JsonResponse({
                        'status': 'warning',
                        'message': 'Device was not found in connected devices',
                        'mac_address': mac_address
                    })
            else:
                return JsonResponse({'status': 'error', 'message': 'Device ID and MAC address required'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def api_active_course(request):
    """ESP32 gets active course information for dynamic configuration"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            base_device_id = data.get('base_device_id', 'ESP32_')
            
            # Find active network session
            active_session = NetworkSession.objects.filter(
                is_active=True
            ).first()
            
            if active_session:
                # Generate dynamic device ID and SSID based on course
                course_code = active_session.course.code
                course_title = active_session.course.title
                session = active_session.session
                semester = active_session.semester
                
                # Create dynamic device ID: ESP32_CS101_001
                device_id = f"{base_device_id}{course_code}_{active_session.id:03d}"
                
                # Create dynamic SSID: CS101_Attendance
                ssid = f"{course_code}_Attendance"
                
                return JsonResponse({
                    'active_course': True,
                    'course_code': course_code,
                    'course_title': course_title,
                    'session': session,
                    'semester': semester,
                    'device_id': device_id,
                    'ssid': ssid,
                    'lecturer': active_session.lecturer.username,
                    'esp32_device': active_session.esp32_device.device_name if active_session.esp32_device else 'Unknown Device'
                })
            else:
                return JsonResponse({
                    'active_course': False,
                    'message': 'No active network session found'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

# 🔍 Network-Based Attendance Verification

def verify_network_attendance(student, course, date):
    """Verify if a student was connected to the ESP32 network during attendance"""
    try:
        # Find active network session for this course and date
        network_session = NetworkSession.objects.filter(
            course=course,
            date=date,
            is_active=True
        ).first()
        
        if not network_session:
            return False, None
        
        # Check if student's device was connected
        # For now, we'll use a simple approach - check if any device was connected
        # In a real implementation, you'd need to map student devices to MAC addresses
        connected_devices = ConnectedDevice.objects.filter(
            network_session=network_session,
            is_connected=True
        )
        
        return connected_devices.exists(), network_session.esp32_device
        
    except Exception as e:
        print(f"Error verifying network attendance: {e}")
        return False, None

# Update the existing course_attendance view to use network verification
@login_required
@user_passes_test(lambda u: u.groups.filter(name='Lecturers').exists())
def course_attendance(request, assigned_id):
    """Take attendance for a course with network verification"""
    assigned_course = get_object_or_404(AssignedCourse, id=assigned_id)
    
    # Check if user is assigned to this course
    if assigned_course.lecturer != request.user and not request.user.is_superuser:
        messages.error(request, "You are not assigned to this course.")
        return redirect('admin_ui:dashboard')
    
    if request.method == 'POST':
        if 'take_attendance' in request.POST:
            # Create attendance session
            attendance_session, created = AttendanceSession.objects.get_or_create(
                course=assigned_course.course,
                lecturer=request.user,
                session=assigned_course.session,
                semester=assigned_course.semester,
                date=timezone.now().date()
            )
            
            # Get all enrolled students
            enrolled_students = Student.objects.filter(
                courseenrollment__course=assigned_course.course
            )
            
            # Check network connectivity for each student
            for student in enrolled_students:
                status = request.POST.get(f'status_{student.matric_no}', 'absent')
                
                if status == 'present':
                    # Verify network connectivity
                    network_verified, esp32_device = verify_network_attendance(
                        student, 
                        assigned_course.course, 
                        timezone.now().date()
                    )
                    
                    # Create or update attendance record
                    attendance_record, created = AttendanceRecord.objects.get_or_create(
                        attendance_session=attendance_session,
                        student=student,
                        defaults={
                            'status': status,
                            'network_verified': network_verified,
                            'esp32_device': esp32_device
                        }
                    )
                    
                    if not created:
                        attendance_record.status = status
                        attendance_record.network_verified = network_verified
                        attendance_record.esp32_device = esp32_device
                        attendance_record.save()
                else:
                    # Mark as absent
                    attendance_record, created = AttendanceRecord.objects.get_or_create(
                        attendance_session=attendance_session,
                        student=student,
                        defaults={'status': status}
                    )
                    
                    if not created:
                        attendance_record.status = status
                        attendance_record.save()
            
            messages.success(request, f"Attendance taken for {assigned_course.course.code}")
            return redirect('admin_ui:course_attendance', assigned_id=assigned_id)
    
    # Get existing attendance for today
    today = timezone.now().date()
    existing_attendance = {}
    
    try:
        attendance_session = AttendanceSession.objects.get(
            course=assigned_course.course,
            date=today
        )
        for record in AttendanceRecord.objects.filter(attendance_session=attendance_session):
            existing_attendance[record.student.matric_no] = record
    except AttendanceSession.DoesNotExist:
        pass
    
    # Get enrolled students
    students = Student.objects.filter(
        courseenrollment__course=assigned_course.course
    ).order_by('name')
    
    # Check network connectivity status
    network_status = {}
    for student in students:
        network_verified, _ = verify_network_attendance(
            student, 
            assigned_course.course, 
            today
        )
        network_status[student.matric_no] = network_verified
    
    return render(request, 'admin_ui/course_attendance.html', {
        'assigned_course': assigned_course,
        'students': students,
        'existing_attendance': existing_attendance,
        'network_status': network_status,
        'today': today
    })


@csrf_exempt
def api_mark_attendance(request):
    """ESP32 marks attendance for a student with enrollment validation"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            matric_number = data.get('matric_number')
            course_code = data.get('course_code')
            course_name = data.get('course_name')
            session_id = data.get('session_id')
            device_id = data.get('device_id')
            timestamp = data.get('timestamp')
            
            # Validate required fields
            if not matric_number or not course_code:
                return JsonResponse({
                    'success': False,
                    'message': 'Matric number and course code are required'
                }, status=400)
            
            # Find the student
            try:
                student = Student.objects.get(matric_no=matric_number)
            except Student.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': f'Student with matric number {matric_number} not found'
                }, status=404)
            
            # Find the course
            try:
                course = Course.objects.get(code=course_code)
            except Course.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': f'Course {course_code} not found'
                }, status=404)
            
            # Check if student is enrolled in this course
            try:
                enrollment = CourseEnrollment.objects.get(
                    student=student,
                    course=course
                )
            except CourseEnrollment.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': f'Student {matric_number} is not enrolled in course {course_code}'
                }, status=403)
            
            # Find or create attendance session for today
            today = timezone.now().date()
            attendance_session, created = AttendanceSession.objects.get_or_create(
                course=course,
                date=today,
                defaults={
                    'lecturer': enrollment.lecturer if hasattr(enrollment, 'lecturer') else None,
                    'session': enrollment.session if hasattr(enrollment, 'session') else None,
                    'semester': enrollment.semester if hasattr(enrollment, 'semester') else None
                }
            )
            
            # Check if attendance already exists for this student today
            existing_attendance = AttendanceRecord.objects.filter(
                attendance_session=attendance_session,
                student=student
            ).first()
            
            if existing_attendance:
                # Update existing attendance
                existing_attendance.status = 'present'
                existing_attendance.network_verified = True
                existing_attendance.esp32_device = device_id
                existing_attendance.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Attendance updated for {student.name} in {course.code}',
                    'student_name': student.name,
                    'course_code': course.code,
                    'status': 'present',
                    'network_verified': True
                })
            else:
                # Create new attendance record
                AttendanceRecord.objects.create(
                    attendance_session=attendance_session,
                    student=student,
                    status='present',
                    network_verified=True,
                    esp32_device=device_id
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Attendance recorded for {student.name} in {course.code}',
                    'student_name': student.name,
                    'course_code': course.code,
                    'status': 'present',
                    'network_verified': True
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error recording attendance: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)
