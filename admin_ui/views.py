# views.py — Part 1: Authentication & Lecturer Registration

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from urllib.parse import unquote
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import models
import json
from .forms import (
    LecturerLoginForm,
    AdminCreationForm,
    AdminLoginForm,
    OfficerLoginForm,
    CSVUploadForm,
    StudentCSVUploadForm
)
from .models import (
    FingerprintStudent,
    AssignedCourse,
    Student,
    Course,
    CourseEnrollment,
    NetworkSession,
    AttendanceSession,
    AttendanceRecord,
    ESP32Device,
    ConnectedDevice
)
from .utils import load_courses_from_csv
from datetime import datetime, timedelta
from django.utils import timezone

# Import course management views
from .course_management import (
    course_management,
    remove_student_enrollment,
    download_enrollment_template,
    enhanced_dashboard,
    upload_course_students,
    view_all_enrollments,
    test_database_connection
)

# 🔐 Admin Login
def admin_login_view(request):
    form = AdminLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user and user.is_superuser:
            login(request, user)
            messages.success(request, 'Welcome, Admin!')
            return redirect('admin_ui:register_lecturer')
        messages.error(request, 'Invalid credentials or not an Admin.')
    return render(request, 'admin_ui/admin_login.html', {'form': form})

# 🧾 Admin Creation
def create_admin_view(request):
    form = AdminCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if form.cleaned_data['passkey'] == settings.SUPERUSER_PASSKEY:
            User.objects.create_superuser(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            messages.success(request, '✅ Admin created successfully!')
            return redirect('admin_login')
        messages.error(request, '❌ Invalid passkey.')
    return render(request, 'admin_ui/create_admin.html', {'form': form})

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

        return redirect('admin_ui:register_lecturer')

    context = {
        'courses': courses,
        'lecturers': lecturers,
        'departments': departments,
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
from .models import Student, FingerprintStudent, Course
from .utils import load_courses_from_csv
import csv
import os

# 🗂 Registration Officer functionality has been removed
# Lecturers now directly manage their course enrollments through the course management system

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
    
    # Get all available courses for display (but don't auto-enroll)
    courses = load_courses_from_csv('courses.csv')

    if request.method == 'POST':
        # Only handle fingerprint enrollment, not course enrollment
        fingerprint.fingerprint_data = "fingerprint_enrolled_hash"
        fingerprint.save()
        
        messages.success(request, f"✅ Fingerprint saved for {student.name}")
        
        # Redirect to enhanced dashboard to manage course enrollments
        return redirect('admin_ui:enhanced_dashboard')

    # Show current enrollments without modifying them
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

# 📊 Admin Attendance Dashboard
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
    return redirect('admin_login')

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
    """List ESP32 devices for Admins and lecturers"""
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
    """List network sessions for lecturers and Admins"""
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
    """ESP32 sends heartbeat to Django and receives dynamic configuration"""
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
                
                # 🔌 DYNAMIC CONFIGURATION RESPONSE
                # Check if this device has an active network session
                active_session = NetworkSession.objects.filter(
                    esp32_device=device,
                    is_active=True
                ).first()
                
                if active_session:
                    # Device is in an active session - send configuration
                    course = active_session.course
                    session = active_session.session
                    semester = active_session.semester
                    
                    # Generate dynamic configuration
                    course_code = course.code
                    session_id = f"{session}_{semester}".replace(" ", "_").replace("/", "_")
                    
                    # Dynamic device ID and SSID
                    dynamic_device_id = f"ESP32_{course_code}_{session_id}"
                    dynamic_ssid = f"{course_code}_Attendance_{session.replace('/', '_')}"
                    
                    # Update device with session-specific configuration
                    device.device_name = f"{course_code} - {course.title}"
                    device.ssid = dynamic_ssid
                    device.password = ""  # Open network
                    device.location = f"{course_code} Classroom - {session} {semester}"
                    device.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Heartbeat received - Active session configuration applied',
                        'device_id': device_id,
                        'created': created,
                        'configuration': {
                            'active_session': True,
                            'course_code': course_code,
                            'course_title': course.title,
                            'session': session,
                            'semester': semester,
                            'device_id': dynamic_device_id,
                            'ssid': dynamic_ssid,
                            'password': "",
                            'lecturer': active_session.lecturer.username,
                            'session_id': active_session.id
                        }
                    })
                else:
                    # No active session - device is idle
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Heartbeat received - Device idle',
                        'device_id': device_id,
                        'created': created,
                        'configuration': {
                            'active_session': False,
                            'message': 'No active session - device in standby mode'
                        }
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
            # Get time from form and parse it
            time_from_form = request.POST.get('time', '09:00:00')
            
            # Parse the time string to a time object
            try:
                from datetime import datetime
                if ':' in time_from_form:
                    # Handle both "09:00" and "09:00:00" formats
                    if time_from_form.count(':') == 1:
                        time_from_form += ':00'
                    parsed_time = datetime.strptime(time_from_form, '%H:%M:%S').time()
                else:
                    parsed_time = datetime.strptime(time_from_form, '%H:%M:%S').time()
            except ValueError:
                # Default to 09:00 if parsing fails
                parsed_time = datetime.strptime('09:00:00', '%H:%M:%S').time()
            
            # Create attendance session with time
            attendance_session, created = AttendanceSession.objects.get_or_create(
                course=assigned_course.course,
                lecturer=request.user,
                session=assigned_course.session,
                semester=assigned_course.semester,
                date=timezone.now().date(),
                time=parsed_time
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
                            'esp32_device': esp32_device,
                            'marked_by': request.user
                        }
                    )
                    
                    if not created:
                        attendance_record.status = status
                        attendance_record.network_verified = network_verified
                        attendance_record.esp32_device = esp32_device
                        attendance_record.marked_by = request.user
                        attendance_record.save()
                else:
                    # Mark as absent
                    attendance_record, created = AttendanceRecord.objects.get_or_create(
                        attendance_session=attendance_session,
                        student=student,
                        defaults={
                            'status': status,
                            'marked_by': request.user
                        }
                    )
                    
                    if not created:
                        attendance_record.status = status
                        attendance_record.marked_by = request.user
                        attendance_record.save()
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Return updated attendance data for real-time table update
                today = timezone.now().date()
                attendance_records = AttendanceRecord.objects.filter(
                    attendance_session__course=assigned_course.course,
                    attendance_session__session=assigned_course.session,
                    attendance_session__semester=assigned_course.semester
                ).select_related('student', 'attendance_session', 'marked_by', 'esp32_device').order_by('-attendance_session__date', '-attendance_session__time', 'student__name')
                
                # Prepare data for JSON response
                records_data = []
                for record in attendance_records:
                    records_data.append({
                        'date': record.attendance_session.date.strftime('%b %d, %Y'),
                        'time': record.attendance_session.time.strftime('%I:%M %p'),
                        'student_name': record.student.name,
                        'matric_no': record.student.matric_no,
                        'status': record.status,
                        'network_verified': record.network_verified,
                        'esp32_device': record.esp32_device.device_name if record.esp32_device else '-',
                        'marked_by': record.marked_by.username if record.marked_by else 'System',
                        'marked_at': record.marked_at.strftime('%I:%M %p') if record.marked_at else '-'
                    })
                
                return JsonResponse({
                    'success': True,
                    'message': f"Attendance taken for {assigned_course.course.code}",
                    'attendance_records': records_data,
                    'total_records': len(records_data)
                })
            
            messages.success(request, f"Attendance taken for {assigned_course.course.code}")
            return redirect('admin_ui:course_attendance', assigned_id=assigned_id)
    
    # Get existing attendance for today
    today = timezone.now().date()
    existing_attendance = {}
    
    try:
        # Get the most recent attendance session for today (in case there are multiple)
        attendance_session = AttendanceSession.objects.filter(
            course=assigned_course.course,
            date=today
        ).order_by('-created_at').first()
        
        if attendance_session:
            for record in AttendanceRecord.objects.filter(attendance_session=attendance_session):
                existing_attendance[record.student.matric_no] = record
    except Exception as e:
        print(f"Error getting existing attendance: {e}")
        pass
    
    # Get enrolled students (use distinct to avoid duplicates)
    students = Student.objects.filter(
        courseenrollment__course=assigned_course.course,
        courseenrollment__session=assigned_course.session,
        courseenrollment__semester=assigned_course.semester
    ).distinct().order_by('name')
    
    # Check network connectivity status
    network_status = {}
    for student in students:
        network_verified, _ = verify_network_attendance(
            student, 
            assigned_course.course, 
            today
        )
        network_status[student.matric_no] = network_verified
    
    # Get all attendance records for this course (for the records table)
    attendance_records = AttendanceRecord.objects.filter(
        attendance_session__course=assigned_course.course,
        attendance_session__session=assigned_course.session,
        attendance_session__semester=assigned_course.semester
    ).select_related('student', 'attendance_session', 'marked_by').order_by('-attendance_session__date', '-attendance_session__time', 'student__name')
    
    return render(request, 'admin_ui/course_attendance.html', {
        'assigned_course': assigned_course,
        'students': students,
        'existing_attendance': existing_attendance,
        'network_status': network_status,
        'today': today,
        'attendance_records': attendance_records
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

# 🎯 ESP32-Based Attendance Marking System

@login_required
def start_network_session_view(request):
    """Start a new network attendance session with automatic ESP32 configuration"""
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        session = request.POST.get('session')
        semester = request.POST.get('semester')
        
        try:
            course = Course.objects.get(id=course_id)
            # Check if lecturer is assigned to this course
            if not AssignedCourse.objects.filter(
                lecturer=request.user, 
                course=course, 
                session=session, 
                semester=semester
            ).exists():
                messages.error(request, "❌ You are not assigned to this course for the specified session/semester.")
                return redirect('admin_ui:dashboard')
            
            # 🔌 AUTOMATIC ESP32 CONFIGURATION
            # Find available ESP32 devices that are online (have recent heartbeat)
            available_devices = ESP32Device.objects.filter(
                is_active=True,
                last_heartbeat__gte=timezone.now() - timedelta(minutes=5)  # Online in last 5 minutes
            ).order_by('-last_heartbeat')
            
            if not available_devices.exists():
                messages.error(request, "❌ No ESP32 devices are currently online. Please check device connectivity.")
                return redirect('admin_ui:dashboard')
            
            # Select the most recently active ESP32 device
            selected_device = available_devices.first()
            
            # Generate dynamic configuration for the ESP32
            course_code = course.code
            session_id = f"{session}_{semester}".replace(" ", "_").replace("/", "_")
            
            # Create dynamic device ID: ESP32_CS101_2024_2025_1st_Semester
            dynamic_device_id = f"ESP32_{course_code}_{session_id}"
            
            # Create dynamic SSID: CS101_Attendance_2024_2025
            dynamic_ssid = f"{course_code}_Attendance_{session.replace('/', '_')}"
            
            # Update ESP32 device with dynamic configuration
            selected_device.device_name = f"{course_code} - {course.title}"
            selected_device.ssid = dynamic_ssid
            selected_device.password = ""  # Open network for easy student access
            selected_device.location = f"{course_code} Classroom - {session} {semester}"
            selected_device.save()
            
            # Create network session with the configured ESP32 device
            network_session = NetworkSession.objects.create(
                esp32_device=selected_device,  # Now automatically configured
                course=course,
                lecturer=request.user,
                session=session,
                semester=semester,
                date=timezone.now().date(),
                start_time=timezone.now(),
                is_active=True
            )
            
            messages.success(request, f"✅ Network session started for {course.code}! ESP32 '{selected_device.device_name}' configured and ready.")
            return redirect('admin_ui:network_session_active', session_id=network_session.id)
            
        except Course.DoesNotExist:
            messages.error(request, "❌ Course not found.")
        except Exception as e:
            messages.error(request, f"❌ Error starting session: {str(e)}")
    
    # Get lecturer's assigned courses
    assigned_courses = AssignedCourse.objects.filter(lecturer=request.user)
    
    # Get available ESP32 devices for display
    available_devices = ESP32Device.objects.filter(
        is_active=True,
        last_heartbeat__gte=timezone.now() - timedelta(minutes=5)
    ).order_by('-last_heartbeat')
    
    context = {
        'assigned_courses': assigned_courses,
        'current_session': "2024/2025",
        'current_semester': "1st Semester",
        'available_esp32_devices': available_devices,  # Show available devices
        'esp32_status': {
            'total_devices': ESP32Device.objects.filter(is_active=True).count(),
            'online_devices': available_devices.count(),
            'offline_devices': ESP32Device.objects.filter(
                is_active=True,
                last_heartbeat__lt=timezone.now() - timedelta(minutes=5)
            ).count()
        }
    }
    return render(request, 'admin_ui/start_network_session.html', context)

@login_required
def network_session_active_view(request, session_id):
    """Active network session dashboard"""
    network_session = get_object_or_404(NetworkSession, id=session_id, lecturer=request.user)
    
    # Get connected devices
    connected_devices = ConnectedDevice.objects.filter(
        network_session=network_session,
        is_connected=True
    ).order_by('-connected_at')
    
    # Get attendance records for this session
    attendance_records = AttendanceRecord.objects.filter(
        attendance_session__course=network_session.course,
        attendance_session__date=network_session.date
    ).select_related('student')
    
    context = {
        'network_session': network_session,
        'connected_devices': connected_devices,
        'attendance_records': attendance_records,
        'total_enrolled': CourseEnrollment.objects.filter(
            course=network_session.course,
            session=network_session.session,
            semester=network_session.semester
        ).count(),
        'present_count': attendance_records.filter(status='present').count()
    }
    return render(request, 'admin_ui/network_session_active.html', context)

@login_required
def end_network_session_view(request, session_id):
    """End the network session"""
    network_session = get_object_or_404(NetworkSession, id=session_id, lecturer=request.user)
    
    if request.method == 'POST':
        network_session.end_time = timezone.now()
        network_session.is_active = False
        network_session.save()
        
        # Disconnect all devices
        ConnectedDevice.objects.filter(network_session=network_session).update(
            is_connected=False,
            disconnected_at=timezone.now()
        )
        
        messages.success(request, f"✅ Network session ended for {network_session.course.code}")
        return redirect('admin_ui:dashboard')
    
    return render(request, 'admin_ui/end_network_session.html', {'network_session': network_session})

def student_attendance_marking_view(request):
    """Public view for students to mark attendance via ESP32 WiFi"""
    if request.method == 'POST':
        matric_no = request.POST.get('matric_no')
        name = request.POST.get('name')
        device_mac = request.POST.get('device_mac', '')
        
        try:
            student = Student.objects.get(matric_no=matric_no)
            
            # Check if student is enrolled in any active course
            active_enrollments = CourseEnrollment.objects.filter(
                student=student,
                session="2024/2025",  # Current session
                semester="1st Semester"  # Current semester
            )
            
            if not active_enrollments.exists():
                return JsonResponse({
                    'success': False,
                    'message': '❌ You are not enrolled in any courses for the current session.'
                })
            
            # Find active network session for enrolled courses
            active_sessions = NetworkSession.objects.filter(
                course__in=[enrollment.course for enrollment in active_enrollments],
                is_active=True,
                date=timezone.now().date()
            )
            
            if not active_sessions.exists():
                return JsonResponse({
                    'success': False,
                    'message': '❌ No active attendance session found for your courses.'
                })
            
            # Mark attendance for each active session
            attendance_created = False
            for network_session in active_sessions:
                # Check if attendance already exists
                existing_attendance = AttendanceRecord.objects.filter(
                    student=student,
                    attendance_session__course=network_session.course,
                    attendance_session__date=network_session.date
                ).first()
                
                if not existing_attendance:
                    # Create attendance session if it doesn't exist
                    attendance_session, created = AttendanceSession.objects.get_or_create(
                        course=network_session.course,
                        lecturer=network_session.lecturer,
                        session=network_session.session,
                        semester=network_session.semester,
                        date=network_session.date
                    )
                    
                    # Create attendance record
                    AttendanceRecord.objects.create(
                        attendance_session=attendance_session,
                        student=student,
                        status='present',
                        network_verified=True,
                        device_mac=device_mac,
                        esp32_device=network_session.esp32_device
                    )
                    attendance_created = True
                    
                    # Record device connection
                    ConnectedDevice.objects.get_or_create(
                        network_session=network_session,
                        mac_address=device_mac,
                        defaults={
                            'device_name': f"{student.name}'s Device",
                            'ip_address': request.META.get('REMOTE_ADDR', ''),
                            'is_connected': True
                        }
                    )
            
            if attendance_created:
                return JsonResponse({
                    'success': True,
                    'message': f'✅ Attendance marked successfully for {student.name}!',
                    'student_name': student.name,
                    'matric_no': student.matric_no
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': '⚠️ Attendance already marked for today.'
                })
                
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '❌ Student not found. Please check your matriculation number.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'❌ Error: {str(e)}'
            })
    
    # GET request - show attendance marking form
    return render(request, 'admin_ui/student_attendance_marking.html')

# ESP32 API Endpoints for device communication
@csrf_exempt
def api_device_heartbeat(request):
    """ESP32 device heartbeat endpoint"""
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        ssid = request.POST.get('ssid')
        
        try:
            device = ESP32Device.objects.get(device_id=device_id)
            device.last_heartbeat = timezone.now()
            device.last_seen = timezone.now()
            device.ssid = ssid
            device.save()
            
            return JsonResponse({'status': 'ok', 'message': 'Heartbeat received'})
        except ESP32Device.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Device not found'}, status=404)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def api_device_connected(request):
    """ESP32 device connection endpoint"""
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        course_code = request.POST.get('course_code')
        
        try:
            device = ESP32Device.objects.get(device_id=device_id)
            course = Course.objects.get(code=course_code)
            
            # Find or create active network session
            network_session, created = NetworkSession.objects.get_or_create(
                esp32_device=device,
                course=course,
                date=timezone.now().date(),
                is_active=True,
                defaults={
                    'lecturer': device.assigned_lecturer if hasattr(device, 'assigned_lecturer') else None,
                    'session': "2024/2025",
                    'semester': "1st Semester",
                    'start_time': timezone.now()
                }
            )
            
            if not created:
                network_session.esp32_device = device
                network_session.is_active = True
                network_session.save()
            
            return JsonResponse({
                'status': 'ok', 
                'message': f'Connected to {course.code}',
                'session_id': network_session.id
            })
        except (ESP32Device.DoesNotExist, Course.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Device or course not found'}, status=404)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def api_mark_attendance(request):
    """API endpoint for marking attendance via ESP32"""
    if request.method == 'POST':
        matric_no = request.POST.get('matric_no')
        device_id = request.POST.get('device_id')
        
        try:
            student = Student.objects.get(matric_no=matric_no)
            device = ESP32Device.objects.get(device_id=device_id)
            
            # Find active network session for this device
            network_session = NetworkSession.objects.filter(
                esp32_device=device,
                is_active=True,
                date=timezone.now().date()
            ).first()
            
            if not network_session:
                return JsonResponse({
                    'success': False,
                    'message': 'No active session found for this device.'
                })
            
            # Check if student is enrolled
            if not CourseEnrollment.objects.filter(
                student=student,
                course=network_session.course,
                session=network_session.session,
                semester=network_session.semester
            ).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Student not enrolled in this course.'
                })
            
            # Mark attendance
            attendance_session, created = AttendanceSession.objects.get_or_create(
                course=network_session.course,
                lecturer=network_session.lecturer,
                session=network_session.session,
                semester=network_session.semester,
                date=timezone.now().date()
            )
            
            attendance_record, created = AttendanceRecord.objects.get_or_create(
                attendance_session=attendance_session,
                student=student,
                defaults={
                    'status': 'present',
                    'network_verified': True,
                    'esp32_device': device
                }
            )
            
            if created:
                return JsonResponse({
                    'success': True,
                    'message': f'Attendance marked for {student.name}',
                    'student_name': student.name
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Attendance already marked for today.'
                })
                
        except (Student.DoesNotExist, ESP32Device.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Student or device not found.'
            })
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

# ========================================
# ESP32 ATTENDANCE SYSTEM IMPLEMENTATION
# ========================================

@login_required
def start_esp32_session_view(request):
    """Start an ESP32-based attendance session"""
    try:
        # Get lecturer's assigned courses
        assigned_courses = AssignedCourse.objects.filter(lecturer=request.user)
        
        if request.method == 'POST':
            course_id = request.POST.get('course_id')
            session_name = request.POST.get('session_name')
            semester = request.POST.get('semester')
            
            if course_id and session_name and semester:
                course = Course.objects.get(id=course_id)
                
                # Create or get ESP32 device for this lecturer
                esp32_device, created = ESP32Device.objects.get_or_create(
                    assigned_lecturer=request.user,
                    defaults={
                        'device_id': f'ESP32_{request.user.username}_{course.code}',
                        'device_name': f'{course.code}_Attendance_Device',
                        'location': 'Classroom',
                        'is_active': True
                    }
                )
                
                # Create network session
                network_session = NetworkSession.objects.create(
                    course=course,
                    lecturer=request.user,
                    session=session_name,
                    semester=semester,
                    date=timezone.now().date(),
                    start_time=timezone.now(),
                    is_active=True,
                    esp32_device=esp32_device
                )
                
                messages.success(request, f'ESP32 session started for {course.code}! Students can now connect to the ESP32 WiFi network.')
                return redirect('admin_ui:esp32_session_active', session_id=network_session.id)
        
        context = {
            'assigned_courses': assigned_courses,
            'semesters': ['1st Semester', '2nd Semester', 'Summer'],
            'current_session': f"{timezone.now().year}/{timezone.now().year + 1}"
        }
        return render(request, 'admin_ui/start_esp32_session.html', context)
        
    except Exception as e:
        messages.error(request, f'Error starting ESP32 session: {str(e)}')
        return redirect('admin_ui:dashboard')

@login_required
def esp32_session_active_view(request, session_id):
    """Monitor active ESP32 attendance session"""
    try:
        network_session = NetworkSession.objects.get(
            id=session_id,
            lecturer=request.user,
            is_active=True
        )
        
        # Get attendance records for this session
        attendance_records = AttendanceRecord.objects.filter(
            attendance_session__course=network_session.course,
            attendance_session__date=network_session.date,
            network_verified=True
        ).select_related('student', 'attendance_session')
        
        # Get connected devices count
        connected_devices = ConnectedDevice.objects.filter(
            esp32_device=network_session.esp32_device,
            is_connected=True
        ).count()
        
        context = {
            'network_session': network_session,
            'attendance_records': attendance_records,
            'connected_devices': connected_devices,
            'total_students': network_session.course.students.count(),
            'present_count': attendance_records.count(),
            'absent_count': network_session.course.students.count() - attendance_records.count()
        }
        return render(request, 'admin_ui/esp32_session_active.html', context)
        
    except NetworkSession.DoesNotExist:
        messages.error(request, 'Session not found or not active.')
        return redirect('admin_ui:dashboard')

@login_required
def end_esp32_session_view(request, session_id):
    """End ESP32 attendance session"""
    try:
        network_session = NetworkSession.objects.get(
            id=session_id,
            lecturer=request.user,
            is_active=True
        )
        
        if request.method == 'POST':
            # End the session
            network_session.is_active = False
            network_session.end_time = timezone.now()
            network_session.save()
            
            # Deactivate ESP32 device
            if network_session.esp32_device:
                network_session.esp32_device.is_active = False
                network_session.esp32_device.save()
            
            messages.success(request, f'ESP32 session ended for {network_session.course.code}.')
            return redirect('admin_ui:dashboard')
        
        context = {'network_session': network_session}
        return render(request, 'admin_ui/end_esp32_session.html', context)
        
    except NetworkSession.DoesNotExist:
        messages.error(request, 'Session not found.')
        return redirect('admin_ui:dashboard')

@login_required
def esp32_device_management_view(request):
    """Manage ESP32 devices"""
    try:
        # Get lecturer's ESP32 devices
        esp32_devices = ESP32Device.objects.filter(assigned_lecturer=request.user)
        
        if request.method == 'POST':
            action = request.POST.get('action')
            device_id = request.POST.get('device_id')
            
            if action == 'activate' and device_id:
                device = ESP32Device.objects.get(id=device_id, assigned_lecturer=request.user)
                device.is_active = True
                device.save()
                messages.success(request, f'Device {device.device_name} activated.')
            elif action == 'deactivate' and device_id:
                device = ESP32Device.objects.get(id=device_id, assigned_lecturer=request.user)
                device.is_active = False
                device.save()
                messages.success(request, f'Device {device.device_name} deactivated.')
        
        context = {'esp32_devices': esp32_devices}
        return render(request, 'admin_ui/esp32_device_management.html', context)
        
    except Exception as e:
        messages.error(request, f'Error managing ESP32 devices: {str(e)}')
        return redirect('admin_ui:dashboard')

# ========================================
# ESP32 API ENDPOINTS
# ========================================

@csrf_exempt
def esp32_heartbeat_api(request):
    """ESP32 heartbeat to check server connectivity and get dynamic configuration"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            wifi_ssid = data.get('wifi_ssid', '')
            connected_students = data.get('connected_students', 0)
        except json.JSONDecodeError:
            # Fallback to POST data for compatibility
            device_id = request.POST.get('device_id')
            wifi_ssid = request.POST.get('wifi_ssid', '')
            connected_students = request.POST.get('connected_students', 0)
        
        try:
            device = ESP32Device.objects.get(device_id=device_id)
            device.last_heartbeat = timezone.now()
            device.connected_wifi = wifi_ssid
            device.connected_students_count = int(connected_students)
            device.save()
            
            # Check for active session and send dynamic configuration
            active_session = NetworkSession.objects.filter(
                esp32_device=device,
                is_active=True,
                date=timezone.now().date()
            ).first()
            
            if active_session:
                # Send dynamic configuration with lecturer's WiFi credentials
                return JsonResponse({
                    'status': 'ok',
                    'message': 'Heartbeat received - Active session found',
                    'server_time': timezone.now().isoformat(),
                    'active_session': True,
                    'config': {
                        'device_id': device.device_id,
                        'device_name': device.device_name,
                        'ssid': device.ssid,
                        'password': device.password,
                        'location': device.location,
                        'course': active_session.course.code,
                        'lecturer': active_session.lecturer.username,
                        'session_id': active_session.id,
                        'start_time': active_session.start_time.isoformat(),
                        'lecturer_ssid': data.get('lecturer_wifi_ssid', ''),
                        'lecturer_password': data.get('lecturer_wifi_password', '')
                    }
                })
            else:
                # No active session - standby mode
                return JsonResponse({
                    'status': 'ok',
                    'message': 'Heartbeat received - No active session',
                    'server_time': timezone.now().isoformat(),
                    'active_session': False,
                    'config': {
                        'device_id': device.device_id,
                        'device_name': device.device_name,
                        'ssid': 'Attendance_Standby',
                        'password': '12345678',
                        'location': 'Standby Mode'
                    }
                })
                
        except ESP32Device.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Device not registered'
            }, status=404)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def esp32_check_session_api(request):
    """ESP32 checks for active session"""
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        
        try:
            device = ESP32Device.objects.get(device_id=device_id)
            
            # Check for active session
            active_session = NetworkSession.objects.filter(
                esp32_device=device,
                is_active=True,
                date=timezone.now().date()
            ).first()
            
            if active_session:
                return JsonResponse({
                    'status': 'ok',
                    'has_session': True,
                    'session_data': {
                        'course_code': active_session.course.code,
                        'course_name': active_session.course.name,
                        'lecturer': active_session.lecturer.get_full_name(),
                        'session': active_session.session,
                        'semester': active_session.semester,
                        'start_time': active_session.start_time.isoformat()
                    }
                })
            else:
                return JsonResponse({
                    'status': 'ok',
                    'has_session': False,
                    'message': 'No active session'
                })
                
        except ESP32Device.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Device not registered'
            }, status=404)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def esp32_mark_attendance_api(request):
    """ESP32 submits student attendance"""
    if request.method == 'POST':
        matric_no = request.POST.get('matric_no')
        student_name = request.POST.get('student_name')
        device_id = request.POST.get('device_id')
        
        try:
            # Find student by matric number or name
            student = Student.objects.filter(
                matric_no=matric_no
            ).first() or Student.objects.filter(
                name__icontains=student_name
            ).first()
            
            if not student:
                return JsonResponse({
                    'success': False,
                    'message': 'Student not found. Please check your details.'
                })
            
            device = ESP32Device.objects.get(device_id=device_id)
            
            # Find active network session for this device
            network_session = NetworkSession.objects.filter(
                esp32_device=device,
                is_active=True,
                date=timezone.now().date()
            ).first()
            
            if not network_session:
                return JsonResponse({
                    'success': False,
                    'message': 'No active session found. Please contact your lecturer.'
                })
            
            # Check if student is enrolled in the course
            if not CourseEnrollment.objects.filter(
                student=student,
                course=network_session.course,
                session=network_session.session,
                semester=network_session.semester
            ).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'You are not enrolled in {network_session.course.code}.'
                })
            
            # Check if attendance already marked
            existing_record = AttendanceRecord.objects.filter(
                student=student,
                attendance_session__course=network_session.course,
                attendance_session__date=network_session.date
            ).first()
            
            if existing_record:
                return JsonResponse({
                    'success': False,
                    'message': 'Attendance already marked for today.'
                })
            
            # Create attendance session if not exists
            attendance_session, created = AttendanceSession.objects.get_or_create(
                course=network_session.course,
                lecturer=network_session.lecturer,
                session=network_session.session,
                semester=network_session.semester,
                date=network_session.date,
                defaults={'start_time': network_session.start_time}
            )
            
            # Mark attendance
            attendance_record = AttendanceRecord.objects.create(
                attendance_session=attendance_session,
                student=student,
                status='present',
                network_verified=True,
                esp32_device=device,
                timestamp=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Attendance marked successfully for {student.name}!',
                'student_name': student.name,
                'course': network_session.course.code,
                'timestamp': attendance_record.timestamp.isoformat()
            })
                
        except ESP32Device.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not registered'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error marking attendance: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

def esp32_register_device_api(request):
    """Register new ESP32 device"""
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        device_name = request.POST.get('device_name')
        lecturer_username = request.POST.get('lecturer_username')
        
        try:
            lecturer = User.objects.get(username=lecturer_username)
            
            # Check if lecturer is assigned to any courses
            if not AssignedCourse.objects.filter(lecturer=lecturer).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Lecturer not assigned to any courses'
                }, status=400)
            
            # Create or update device
            device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': device_name,
                    'assigned_lecturer': lecturer,
                    'is_active': True,
                    'last_heartbeat': timezone.now()
                }
            )
            
            if not created:
                device.device_name = device_name
                device.assigned_lecturer = lecturer
                device.is_active = True
                device.save()
            
            return JsonResponse({
                'status': 'ok',
                'message': 'Device registered successfully',
                'device_id': device.device_id,
                'assigned_lecturer': lecturer.username
            })
            
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Lecturer not found'
            }, status=404)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def dynamic_esp32_session_view(request):
    """Dynamic ESP32 session management - creates sessions with real-time ESP32 configuration"""
    if not request.user.is_authenticated:
        return redirect('admin_ui:lecturer_login')
    
    # Get lecturer's assigned courses
    assigned_courses = AssignedCourse.objects.filter(lecturer=request.user)
    
    if request.method == 'POST':
        course_id = request.POST.get('course')
        session = request.POST.get('session')
        semester = request.POST.get('semester')
        start_time = request.POST.get('start_time')
        
        if course_id and session and semester and start_time:
            course = get_object_or_404(Course, id=course_id)
            
            # Find available ESP32 device (online within last 5 minutes)
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            available_device = ESP32Device.objects.filter(
                is_active=True,
                last_heartbeat__gte=five_minutes_ago
            ).first()
            
            if available_device:
                # Generate dynamic configuration
                device_id = f"ESP32_{course.code}_{timezone.now().strftime('%Y%m%d_%H%M')}"
                ssid = f"Attendance_{course.code}_{request.user.username}_{timezone.now().strftime('%H%M')}"
                device_name = f"{course.code}_{request.user.username}_{timezone.now().strftime('%H%M')}"
                location = f"{course.title} - {request.user.get_full_name() or request.user.username}"
                
                # Update ESP32 device with dynamic config
                available_device.device_id = device_id
                available_device.device_name = device_name
                available_device.ssid = ssid
                available_device.password = "12345678"  # Default password
                available_device.location = location
                available_device.save()
                
                # Create network session
                start_datetime = datetime.strptime(f"{timezone.now().date()} {start_time}", "%Y-%m-%d %H:%M")
                start_datetime = timezone.make_aware(start_datetime)
                
                network_session = NetworkSession.objects.create(
                    esp32_device=available_device,
                    course=course,
                    lecturer=request.user,
                    session=session,
                    semester=semester,
                    date=timezone.now().date(),
                    start_time=start_datetime,
                    is_active=True
                )
                
                messages.success(request, f'✅ Dynamic ESP32 session created! WiFi: {ssid}')
                return redirect('admin_ui:esp32_session_active', session_id=network_session.id)
            else:
                messages.error(request, '❌ No available ESP32 devices. Please check device status.')
    
    # Get ESP32 device status
    total_devices = ESP32Device.objects.filter(is_active=True).count()
    online_devices = ESP32Device.objects.filter(
        is_active=True,
        last_heartbeat__gte=timezone.now() - timedelta(minutes=5)
    ).count()
    offline_devices = total_devices - online_devices
    
    # Get available devices
    available_devices = ESP32Device.objects.filter(
        is_active=True,
        last_heartbeat__gte=timezone.now() - timedelta(minutes=5)
    ).order_by('-last_heartbeat')
    
    context = {
        'assigned_courses': assigned_courses,
        'total_devices': total_devices,
        'online_devices': online_devices,
        'offline_devices': offline_devices,
        'available_devices': available_devices,
    }
    
    return render(request, 'admin_ui/dynamic_esp32_session.html', context)

def correct_esp32_session_view(request):
    """Correct ESP32 flow: Lecturer provides WiFi credentials for ESP32 internet access"""
    if not request.user.is_authenticated:
        return redirect('admin_ui:lecturer_login')
    
    # Get lecturer's assigned courses
    assigned_courses = AssignedCourse.objects.filter(lecturer=request.user)
    
    if request.method == 'POST':
        course_id = request.POST.get('course')
        session = request.POST.get('session')
        semester = request.POST.get('semester')
        start_time = request.POST.get('start_time')
        lecturer_wifi_ssid = request.POST.get('lecturer_wifi_ssid')
        lecturer_wifi_password = request.POST.get('lecturer_wifi_password')
        
        if course_id and session and semester and start_time and lecturer_wifi_ssid:
            course = get_object_or_404(Course, id=course_id)
            
            # Find available ESP32 device (online within last 5 minutes)
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            available_device = ESP32Device.objects.filter(
                is_active=True,
                last_heartbeat__gte=five_minutes_ago
            ).first()
            
            if available_device:
                # Generate dynamic configuration
                device_id = f"ESP32_{course.code}_{timezone.now().strftime('%Y%m%d_%H%M')}"
                ssid = f"Attendance_{course.code}_{request.user.username}_{timezone.now().strftime('%H%M')}"
                device_name = f"{course.code}_{request.user.username}_{timezone.now().strftime('%H%M')}"
                location = f"{course.title} - {request.user.get_full_name() or request.user.username}"
                
                # Update ESP32 device with dynamic config
                available_device.device_id = device_id
                available_device.device_name = device_name
                available_device.ssid = ssid
                available_device.password = "12345678"  # Student WiFi password
                available_device.location = location
                available_device.save()
                
                # Create network session
                start_datetime = datetime.strptime(f"{timezone.now().date()} {start_time}", "%Y-%m-%d %H:%M")
                start_datetime = timezone.make_aware(start_datetime)
                
                network_session = NetworkSession.objects.create(
                    esp32_device=available_device,
                    course=course,
                    lecturer=request.user,
                    session=session,
                    semester=semester,
                    date=timezone.now().date(),
                    start_time=start_datetime,
                    is_active=True
                )
                
                messages.success(request, f'✅ ESP32 session created! Students connect to WiFi: {ssid}')
                return redirect('admin_ui:esp32_session_active', session_id=network_session.id)
            else:
                messages.error(request, '❌ No available ESP32 devices. Please check device status.')
    
    # Get ESP32 device status
    total_devices = ESP32Device.objects.filter(is_active=True).count()
    online_devices = ESP32Device.objects.filter(
        is_active=True,
        last_heartbeat__gte=timezone.now() - timedelta(minutes=5)
    ).count()
    offline_devices = total_devices - online_devices
    
    # Get available devices
    available_devices = ESP32Device.objects.filter(
        is_active=True,
        last_heartbeat__gte=timezone.now() - timedelta(minutes=5)
    ).order_by('-last_heartbeat')
    
    context = {
        'assigned_courses': assigned_courses,
        'total_devices': total_devices,
        'online_devices': online_devices,
        'offline_devices': offline_devices,
        'available_devices': available_devices,
    }
    
    return render(request, 'admin_ui/correct_esp32_session.html', context)

# 🔐 SECURE ATTENDANCE API ENDPOINTS FOR ESP32
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import hashlib
import hmac
import time
from django.core.exceptions import ValidationError
from django.db import transaction

# API Authentication and Security
def verify_api_token(request):
    """Verify the API token for secure ESP32 communication"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False, "Missing or invalid authorization header"
    
    token = auth_header.split(' ')[1]
    
    # Check if token exists in ESP32Device
    try:
        device = ESP32Device.objects.get(device_id=token, is_active=True)
        return True, device
    except ESP32Device.DoesNotExist:
        return False, "Invalid or inactive device token"
    
    return False, "Invalid token"

def verify_request_signature(request, secret_key):
    """Verify request signature for additional security"""
    signature = request.headers.get('X-Signature')
    timestamp = request.headers.get('X-Timestamp')
    
    if not signature or not timestamp:
        return False, "Missing signature or timestamp"
    
    # Check if timestamp is recent (within 5 minutes)
    current_time = int(time.time())
    if abs(current_time - int(timestamp)) > 300:  # 5 minutes
        return False, "Request timestamp expired"
    
    # Verify signature
    expected_signature = hmac.new(
        secret_key.encode(),
        f"{timestamp}{request.body.decode()}".encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature), "Signature verified"

# 📡 ESP32 Session Management API
@csrf_exempt
@require_http_methods(["POST"])
def esp32_start_session_api(request):
    """ESP32 API endpoint to start a network session"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        course_code = data.get('course_code')
        
        if not device_id or not course_code:
            return JsonResponse({'error': 'Missing device_id or course_code'}, status=400)
        
        # Get or create ESP32 device
        esp32_device, created = ESP32Device.objects.get_or_create(
            device_id=device_id,
            defaults={
                'device_name': f"{course_code} Classroom ESP32",
                'ssid': f"{course_code}_Attendance",
                'password': 'attendance123',
                'location': f"Classroom {course_code}",
                'is_active': True
            }
        )
        
        # End any existing active sessions for this device
        NetworkSession.objects.filter(
            esp32_device=esp32_device,
            is_active=True
        ).update(is_active=False, end_time=timezone.now())
        
        # Create new network session
        network_session = NetworkSession.objects.create(
            esp32_device=esp32_device,
            course=Course.objects.get(code=course_code),
            lecturer=User.objects.get(username='lecturer1'),  # Default lecturer
            session='2024/2025',
            semester='1st Semester',
            date=timezone.now().date(),
            start_time=timezone.now(),
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'session_id': network_session.id,
            'message': f'Session started for {course_code}'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
def esp32_record_attendance_api(request):
    """ESP32 API endpoint to record attendance"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        matric_no = data.get('matric_no')
        student_name = data.get('student_name')
        course_code = data.get('course_code')
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not all([matric_no, student_name, course_code, device_id]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Get course and student
        try:
            course = Course.objects.get(code=course_code)
            student = Student.objects.get(matric_no=matric_no)
        except (Course.DoesNotExist, Student.DoesNotExist):
            return JsonResponse({'error': 'Course or student not found'}, status=400)
        
        # Check if student is enrolled in this course
        if not CourseEnrollment.objects.filter(
            student=student,
            course=course,
            session='2024/2025',
            semester='1st Semester'
        ).exists():
            return JsonResponse({'error': 'Student not enrolled in this course'}, status=400)
        
        # Check if attendance already marked today
        today = timezone.now().date()
        if AttendanceRecord.objects.filter(
            student=student,
            attendance_session__course=course,
            attendance_session__date=today
        ).exists():
            return JsonResponse({'error': 'Attendance already marked today'}, status=400)
        
        # Create attendance session if not exists
        attendance_session, created = AttendanceSession.objects.get_or_create(
            course=course,
            date=today,
            session='2024/2025',
            semester='1st Semester',
            defaults={'lecturer': User.objects.get(username='lecturer1')}
        )
        
        # Record attendance
        attendance_record = AttendanceRecord.objects.create(
            student=student,
            attendance_session=attendance_session,
            status='present',
            marked_at=timezone.now(),
            device_mac=mac_address or 'Unknown'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Attendance recorded for {student_name}',
            'attendance_id': attendance_record.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
def esp32_heartbeat_api(request):
    """ESP32 API endpoint for heartbeat"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        
        if not device_id:
            return JsonResponse({'error': 'Missing device_id'}, status=400)
        
        # Update device heartbeat
        ESP32Device.objects.filter(device_id=device_id).update(
            last_heartbeat=timezone.now()
        )
        
        return JsonResponse({'success': True, 'message': 'Heartbeat received'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["GET"])
def esp32_session_status_api(request):
    """ESP32 API endpoint to get session status"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        device_id = request.GET.get('device_id')
        
        if not device_id:
            return JsonResponse({'error': 'Missing device_id parameter'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if active_session:
            # Get connected devices count
            connected_count = ConnectedDevice.objects.filter(
                network_session=active_session,
                is_connected=True
            ).count()
            
            return JsonResponse({
                'success': True,
                'session_active': True,
                'course_code': active_session.course.code,
                'course_title': active_session.course.title,
                'lecturer': active_session.lecturer.username,
                'start_time': active_session.start_time.isoformat(),
                'connected_devices': connected_count,
                'session_id': active_session.id
            })
        else:
            return JsonResponse({
                'success': True,
                'session_active': False,
                'message': 'No active session found'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
def esp32_verify_student_api(request):
    """ESP32 API endpoint to verify student enrollment"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        matric_no = data.get('matric_no')
        course_code = data.get('course_code')
        
        if not matric_no or not course_code:
            return JsonResponse({'error': 'Missing matric_no or course_code'}, status=400)
        
        # Check if student exists
        try:
            student = Student.objects.get(matric_no=matric_no)
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Student not found',
                'enrolled': False
            })
        
        # Check if course exists
        try:
            course = Course.objects.get(code=course_code)
        except Course.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Course not found',
                'enrolled': False
            })
        
        # Check if student is enrolled in this course
        is_enrolled = CourseEnrollment.objects.filter(
            student=student,
            course=course,
            session='2024/2025',
            semester='1st Semester'
        ).exists()
        
        if is_enrolled:
            return JsonResponse({
                'success': True,
                'message': 'Student verified and enrolled',
                'enrolled': True,
                'student_name': student.name,
                'matric_no': student.matric_no,
                'course_code': course.code,
                'course_title': course.title
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Student not enrolled in this course',
                'enrolled': False,
                'student_name': student.name,
                'matric_no': student.matric_no
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

# 🔧 ESP32 Setup and Management Views
def esp32_setup_view(request):
    """ESP32 WiFi setup and configuration for lecturers"""
    if not request.user.is_authenticated:
        return redirect('admin_ui:lecturer_login')
    
    # Check if user is a lecturer
    if not AssignedCourse.objects.filter(lecturer=request.user).exists():
        messages.error(request, "❌ Access denied. You are not assigned to any courses.")
        return redirect('admin_ui:lecturer_login')
    
    # Get lecturer's assigned courses
    assigned_courses = AssignedCourse.objects.filter(lecturer=request.user)
    
    # Check if ESP32 is already configured
    esp32_status = check_esp32_status(request.user)
    
    # Get or generate API key
    api_key = get_or_create_api_key()
    
    context = {
        'lecturer': request.user,
        'assigned_courses': assigned_courses,
        'esp32_status': esp32_status,
        'esp32_ip': '192.168.4.1',  # ESP32 default IP
        'setup_ssid': 'ESP32_Setup',
        'setup_password': 'setup123',
        'api_key': api_key,  # Add API key to context
    }
    
    return render(request, 'admin_ui/esp32_setup.html', context)

def check_esp32_status(lecturer):
    """Check ESP32 connection status for lecturer"""
    try:
        # Check if there's an active ESP32 session for this lecturer
        active_session = NetworkSession.objects.filter(
            lecturer=lecturer,
            is_active=True
        ).first()
        
        if active_session:
            return {
                'connected': True,
                'device_name': active_session.esp32_device.device_name,
                'course': active_session.course.code,
                'session_id': active_session.id,
                'connected_devices': active_session.connecteddevice_set.filter(is_connected=True).count()
            }
        else:
            return {
                'connected': False,
                'message': 'No active ESP32 session'
            }
    except Exception as e:
        return {
            'connected': False,
            'message': f'Error checking status: {str(e)}'
        }

def esp32_start_session_view(request):
    """Start ESP32 attendance session"""
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        session = request.POST.get('session', '2024/2025')
        semester = request.POST.get('semester', '1st Semester')
        
        try:
            course = Course.objects.get(id=course_id)
            
            # Check if lecturer is assigned to this course
            if not AssignedCourse.objects.filter(
                lecturer=request.user,
                course=course,
                session=session,
                semester=semester
            ).exists():
                messages.error(request, "❌ You are not assigned to this course.")
                return redirect('admin_ui:esp32_setup')
            
            # Create or get ESP32 device for this location
            device_location = f"Classroom {course.code}"
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=f"ESP32_{course.code}_001",
                defaults={
                    'device_name': f"{course.code} Classroom ESP32",
                    'ssid': f"{course.code}_Attendance",
                    'password': 'attendance123',
                    'location': device_location,
                    'is_active': True
                }
            )
            
            # End any existing active sessions for this device
            NetworkSession.objects.filter(
                esp32_device=esp32_device,
                is_active=True
            ).update(is_active=False, end_time=timezone.now())
            
            # Create new network session
            network_session = NetworkSession.objects.create(
                esp32_device=esp32_device,
                course=course,
                lecturer=request.user,
                session=session,
                semester=semester,
                date=timezone.now().date(),
                start_time=timezone.now(),
                is_active=True
            )
            
            messages.success(request, f"✅ ESP32 session started for {course.code}!")
            return redirect('admin_ui:esp32_session_active', session_id=network_session.id)
            
        except Course.DoesNotExist:
            messages.error(request, "❌ Course not found.")
        except Exception as e:
            messages.error(request, f"❌ Error starting session: {str(e)}")
    
    return redirect('admin_ui:esp32_setup')

def esp32_session_active_view(request, session_id):
    """Active ESP32 session monitoring"""
    try:
        network_session = NetworkSession.objects.get(
            id=session_id,
            lecturer=request.user,
            is_active=True
        )
        
        # Get connected devices
        connected_devices = ConnectedDevice.objects.filter(
            network_session=network_session,
            is_connected=True
        )
        
        # Get attendance records for today
        today = timezone.now().date()
        attendance_records = AttendanceRecord.objects.filter(
            attendance_session__course=network_session.course,
            attendance_session__date=today
        )
        
        context = {
            'session': network_session,
            'connected_devices': connected_devices,
            'attendance_records': attendance_records,
            'total_enrolled': CourseEnrollment.objects.filter(
                course=network_session.course,
                session=network_session.session,
                semester=network_session.semester
            ).count()
        }
        
        return render(request, 'admin_ui/esp32_session_active.html', context)
        
    except NetworkSession.DoesNotExist:
        messages.error(request, "❌ Session not found or not active.")
        return redirect('admin_ui:esp32_setup')

def esp32_end_session_view(request, session_id):
    """End ESP32 attendance session"""
    try:
        network_session = NetworkSession.objects.get(
            id=session_id,
            lecturer=request.user,
            is_active=True
        )
        
        # End the session
        network_session.is_active = False
        network_session.end_time = timezone.now()
        network_session.save()
        
        messages.success(request, f"✅ ESP32 session ended for {network_session.course.code}")
        return redirect('admin_ui:esp32_setup')
        
    except NetworkSession.DoesNotExist:
        messages.error(request, "❌ Session not found.")
    
    return redirect('admin_ui:esp32_setup')

# 🔑 API Key Management for ESP32
def generate_api_key():
    """Generate a simple API key for ESP32 devices"""
    import secrets
    return secrets.token_hex(16)  # 32 character hex string

def get_or_create_api_key():
    """Get existing API key or create new one"""
    from django.core.cache import cache
    
    api_key = cache.get('esp32_api_key')
    if not api_key:
        api_key = generate_api_key()
        cache.set('esp32_api_key', api_key, timeout=31536000)  # 1 year
    
    return api_key

def verify_api_key(request):
    """Verify API key from ESP32 requests"""
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return False
    
    api_key = auth_header.split(' ')[1]
    expected_key = get_or_create_api_key()
    
    return api_key == expected_key

@csrf_exempt
@require_http_methods(["POST"])
def esp32_end_session_api(request):
    """ESP32 API endpoint to end a network session"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        
        if not device_id:
            return JsonResponse({'error': 'Missing device_id'}, status=400)
        
        # Find and end active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if active_session:
            active_session.is_active = False
            active_session.end_time = timezone.now()
            active_session.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Session ended for {active_session.course.code}',
                'session_id': active_session.id
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No active session found for this device'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_connected_api(request):
    """ESP32 API endpoint for device connection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        ip_address = data.get('ip_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Create or update connected device record
        connected_device, created = ConnectedDevice.objects.get_or_create(
            network_session=active_session,
            mac_address=mac_address,
            defaults={
                'ip_address': ip_address,
                'is_connected': True
            }
        )
        
        if not created:
            # Update existing record
            connected_device.ip_address = ip_address
            connected_device.is_connected = True
            connected_device.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Device {mac_address} connected',
            'device_id': connected_device.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["GET"])
def esp32_session_status_api(request):
    """ESP32 API endpoint to get session status"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        device_id = request.GET.get('device_id')
        
        if not device_id:
            return JsonResponse({'error': 'Missing device_id parameter'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if active_session:
            # Get connected devices count
            connected_count = ConnectedDevice.objects.filter(
                network_session=active_session,
                is_connected=True
            ).count()
            
            return JsonResponse({
                'success': True,
                'session_active': True,
                'course_code': active_session.course.code,
                'course_title': active_session.course.title,
                'lecturer': active_session.lecturer.username,
                'start_time': active_session.start_time.isoformat(),
                'connected_devices': connected_count,
                'session_id': active_session.id
            })
        else:
            return JsonResponse({
                'success': True,
                'session_active': False,
                'message': 'No active session found'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
def esp32_verify_student_api(request):
    """ESP32 API endpoint to verify student enrollment"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        matric_no = data.get('matric_no')
        course_code = data.get('course_code')
        
        if not matric_no or not course_code:
            return JsonResponse({'error': 'Missing matric_no or course_code'}, status=400)
        
        # Check if student exists
        try:
            student = Student.objects.get(matric_no=matric_no)
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Student not found',
                'enrolled': False
            })
        
        # Check if course exists
        try:
            course = Course.objects.get(code=course_code)
        except Course.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Course not found',
                'enrolled': False
            })
        
        # Check if student is enrolled in this course
        is_enrolled = CourseEnrollment.objects.filter(
            student=student,
            course=course,
            session='2024/2025',
            semester='1st Semester'
        ).exists()
        
        if is_enrolled:
            return JsonResponse({
                'success': True,
                'message': 'Student verified and enrolled',
                'enrolled': True,
                'student_name': student.name,
                'matric_no': student.matric_no,
                'course_code': course.code,
                'course_title': course.title
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Student not enrolled in this course',
                'enrolled': False,
                'student_name': student.name,
                'matric_no': student.matric_no
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found in active session'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== ESP32 PRESENCE VERIFICATION SYSTEM (METHOD 2) =====

@csrf_exempt
def esp32_presence_update_api(request):
    """
    ESP32 sends list of connected devices for presence verification
    This is used with Method 2: Simple presence verification system
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            connected_devices = data.get('connected_devices', [])
            timestamp = data.get('timestamp')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)
            
            # Find or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_name': f'Presence Verification Device {device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Update last heartbeat
            esp32_device.last_heartbeat = timezone.now()
            esp32_device.save()
            
            # Store connected devices for presence verification
            cache_key = f'esp32_presence_{device_id}'
            from django.core.cache import cache
            cache.set(cache_key, {
                'connected_devices': connected_devices,
                'timestamp': timezone.now().isoformat(),
                'device_count': len(connected_devices)
            }, timeout=300)  # Cache for 5 minutes
            
            print(f"📥 Presence update: {len(connected_devices)} devices connected")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Presence data updated for {len(connected_devices)} devices',
                'device_id': device_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def verify_student_presence(student_id=None, device_id="ESP32_PRESENCE_001"):
    """
    Check if a student is physically present in the classroom
    Returns (bool, message) tuple
    """
    try:
        from django.core.cache import cache
        cache_key = f'esp32_presence_{device_id}'
        presence_data = cache.get(cache_key)
        
        if not presence_data:
            return False, "No presence data available from ESP32"
        
        connected_devices = presence_data.get('connected_devices', [])
        device_count = len(connected_devices)
        
        if device_count > 0:
            return True, f"Presence verified - {device_count} devices connected to classroom WiFi"
        else:
            return False, "No devices connected to classroom network"
            
    except Exception as e:
        return False, f"Error checking presence: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def esp32_device_disconnected_api(request):
    """ESP32 API endpoint for device disconnection notification"""
    # Verify API key
    if not verify_api_key(request):
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id or not mac_address:
            return JsonResponse({'error': 'Missing device_id or mac_address'}, status=400)
        
        # Find active session for this device
        active_session = NetworkSession.objects.filter(
            esp32_device__device_id=device_id,
            is_active=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active session found for this device'}, status=400)
        
        # Update connected device record to disconnected
        try:
            connected_device = ConnectedDevice.objects.get(
                network_session=active_session,
                mac_address=mac_address
            )
            connected_device.is_connected = False
            connected_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Device {mac_address} disconnected',
                'device_id': connected_device.id
            })
        except ConnectedDevice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'Device {mac_address} not found in active session'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def esp32_presence_verify_api(request):
    """
    Verify if a student device was present at a specific time
    Used by the attendance system to check ESP32 presence
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_device_id = data.get('student_device_id')
            timestamp = data.get('timestamp')
            esp32_device_id = data.get('esp32_device_id')
            
            if not all([student_device_id, timestamp, esp32_device_id]):
                return JsonResponse({'error': 'Missing required parameters'}, status=400)
            
            # Check cache for presence data
            from django.core.cache import cache
            cache_key = f'esp32_presence_{esp32_device_id}'
            presence_data = cache.get(cache_key)
            
            if not presence_data:
                return JsonResponse({
                    'present': False,
                    'reason': 'No ESP32 presence data available'
                })
            
            # Check if student device was connected
            was_present = student_device_id in presence_data.get('connected_devices', [])
            
            return JsonResponse({
                'present': was_present,
                'timestamp': presence_data.get('timestamp'),
                'esp32_device': esp32_device_id,
                'total_devices': presence_data.get('device_count', 0)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def esp32_device_management(request):
    """
    Admin interface for managing ESP32 devices and viewing presence data
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin:login')
    
    # Get all ESP32 devices
    esp32_devices = ESP32Device.objects.all().order_by('-last_heartbeat')
    
    # Get presence data from cache
    from django.core.cache import cache
    presence_data = {}
    for device in esp32_devices:
        cache_key = f'esp32_presence_{device.device_id}'
        data = cache.get(cache_key)
        if data:
            presence_data[device.device_id] = data
    
    context = {
        'esp32_devices': esp32_devices,
        'presence_data': presence_data,
        'total_devices': len(esp32_devices),
        'active_devices': esp32_devices.filter(is_active=True).count()
    }
    
    return render(request, 'admin_ui/esp32_management.html', context)

# 🎯 Student Attendance Marking System - ESP32 Integration
@login_required
def student_attendance_marking_view(request):
    """Student view to mark attendance for active sessions"""
    try:
        # Get the student profile for the current user
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact administrator.")
        return redirect('admin_ui:dashboard')
    
    # Get all active network sessions where this student is enrolled
    active_sessions = NetworkSession.objects.filter(
        is_active=True,
        course__courseenrollment__student=student
    ).select_related('course', 'lecturer', 'esp32_device').distinct()
    
    # Get today's date
    today = timezone.now().date()
    
    # Get existing attendance records for today
    existing_attendance = {}
    try:
        attendance_sessions = AttendanceSession.objects.filter(
            course__courseenrollment__student=student,
            date=today
        )
        for session in attendance_sessions:
            try:
                record = AttendanceRecord.objects.get(
                    attendance_session=session,
                    student=student
                )
                existing_attendance[session.course.code] = record
            except AttendanceRecord.DoesNotExist:
                pass
    except Exception as e:
        print(f"Error getting existing attendance: {e}")
    
    # Check network connectivity status for each active session
    network_status = {}
    for session in active_sessions:
        # Check if student's device was connected to ESP32 network
        connected_device = ConnectedDevice.objects.filter(
            network_session=session,
            is_connected=True
        ).first()
        
        network_status[session.id] = {
            'connected': connected_device is not None,
            'device_mac': connected_device.mac_address if connected_device else None,
            'connected_at': connected_device.connected_at if connected_device else None
        }
    
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        action = request.POST.get('action')
        
        if session_id and action:
            try:
                network_session = NetworkSession.objects.get(id=session_id)
                
                # Verify student is enrolled in this course
                if not CourseEnrollment.objects.filter(
                    student=student,
                    course=network_session.course
                ).exists():
                    messages.error(request, "You are not enrolled in this course.")
                    return redirect('admin_ui:student_attendance_marking')
                
                if action == 'mark_present':
                    # 🚨 ENFORCE ESP32 CONNECTION - Block attendance without physical presence
                    if not network_status[network_session.id]['connected']:
                        messages.error(request, f"❌ CANNOT MARK ATTENDANCE: You must connect to ESP32 WiFi network '{network_session.esp32_device.wifi_ssid if network_session.esp32_device else 'Classroom_Attendance'}' to verify physical presence. Please connect to the classroom WiFi first, then try again.")
                        return redirect('admin_ui:student_attendance_marking')
                    
                    # Check if attendance already exists for today
                    attendance_session, created = AttendanceSession.objects.get_or_create(
                        course=network_session.course,
                        lecturer=network_session.lecturer,
                        session=network_session.session,
                        semester=network_session.semester,
                        date=today
                    )
                    
                    # Check if attendance record already exists
                    attendance_record, record_created = AttendanceRecord.objects.get_or_create(
                        attendance_session=attendance_session,
                        student=student,
                        defaults={
                            'status': 'present',
                            'network_verified': True,  # Always True since we enforced connection
                            'device_mac': network_status[network_session.id]['device_mac'],
                            'esp32_device': network_session.esp32_device
                        }
                    )
                    
                    if not record_created:
                        # Update existing record
                        attendance_record.status = 'present'
                        attendance_record.network_verified = True  # Always True since we enforced connection
                        attendance_record.device_mac = network_status[network_session.id]['device_mac']
                        attendance_record.esp32_device = network_session.esp32_device
                        attendance_record.save()
                    
                    messages.success(request, f"✅ Attendance marked as PRESENT for {network_session.course.code} - ESP32 Network Verified!")
                    
                elif action == 'mark_absent':
                    # Mark as absent
                    attendance_session, created = AttendanceSession.objects.get_or_create(
                        course=network_session.course,
                        lecturer=network_session.lecturer,
                        session=network_session.session,
                        semester=network_session.semester,
                        date=today
                    )
                    
                    attendance_record, record_created = AttendanceRecord.objects.get_or_create(
                        attendance_session=attendance_session,
                        student=student,
                        defaults={
                            'status': 'absent',
                            'network_verified': False
                        }
                    )
                    
                    if not record_created:
                        attendance_record.status = 'absent'
                        attendance_record.network_verified = False
                        attendance_record.save()
                    
                    messages.success(request, f"❌ Attendance marked as ABSENT for {network_session.course.code}")
                
                return redirect('admin_ui:student_attendance_marking')
                
            except NetworkSession.DoesNotExist:
                messages.error(request, "Session not found.")
            except Exception as e:
                messages.error(request, f"Error marking attendance: {str(e)}")
    
    return render(request, 'admin_ui/student_attendance_marking.html', {
        'student': student,
        'active_sessions': active_sessions,
        'existing_attendance': existing_attendance,
        'network_status': network_status,
        'today': today
    })

# 🔌 ESP32 Student Verification API
@csrf_exempt
def esp32_student_verification_api(request):
    """API for ESP32 to verify student enrollment and mark attendance"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            matric_number = data.get('matric_number')
            course_code = data.get('course_code')
            device_mac = data.get('device_mac', 'ESP32_DIRECT')
            esp32_device_id = data.get('esp32_device_id', 'ESP32_PRESENCE_001')
            action = data.get('action', 'mark_present')
            session = data.get('session', '2024/2025')
            semester = data.get('semester', '1st Semester')
            
            if not all([matric_number, course_code]):
                return JsonResponse({
                    'success': False,
                    'message': 'Missing required fields: matric_number, course_code'
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
                # Try to find enrollment with specific session and semester
                enrollment = CourseEnrollment.objects.filter(
                    student=student,
                    course=course,
                    session=session,
                    semester=semester
                ).first()
                
                if not enrollment:
                    # Try to find any enrollment for this course
                    enrollment = CourseEnrollment.objects.filter(
                        student=student,
                        course=course
                    ).first()
                
                if not enrollment:
                    return JsonResponse({
                        'success': False,
                        'message': f'Student {matric_number} is not enrolled in course {course_code}'
                    }, status=403)
                    
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error checking enrollment: {str(e)}'
                }, status=500)
            
            # Get or create ESP32 device
            esp32_device, created = ESP32Device.objects.get_or_create(
                device_id=esp32_device_id,
                defaults={
                    'device_name': f'ESP32_{esp32_device_id}',
                    'ssid': 'Classroom_Attendance',
                    'password': '',
                    'location': 'Classroom',
                    'is_active': True
                }
            )
            
            # Create or get active network session for today
            today = timezone.now().date()
            network_session, created = NetworkSession.objects.get_or_create(
                esp32_device=esp32_device,
                course=course,
                date=today,
                is_active=True,
                defaults={
                    'lecturer': User.objects.filter(is_staff=True).first() or User.objects.first(),
                    'session': enrollment.session,
                    'semester': enrollment.semester,
                    'start_time': timezone.now(),
                    'is_active': True
                }
            )
            
            # Create or get attendance session
            attendance_session, created = AttendanceSession.objects.get_or_create(
                course=course,
                lecturer=network_session.lecturer,
                session=enrollment.session,
                semester=enrollment.semester,
                date=today,
                defaults={}
            )
            
            # Check if attendance already exists
            attendance_record, record_created = AttendanceRecord.objects.get_or_create(
                attendance_session=attendance_session,
                student=student,
                defaults={
                    'status': 'present',
                    'network_verified': True,
                    'device_mac': device_mac,
                    'esp32_device': esp32_device
                }
            )
            
            if not record_created:
                # Update existing record
                attendance_record.status = 'present'
                attendance_record.network_verified = True
                attendance_record.device_mac = device_mac
                attendance_record.esp32_device = esp32_device
                attendance_record.save()
            
            # Update ESP32 device last seen
            esp32_device.last_seen = timezone.now()
            esp32_device.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Attendance recorded for {student.name} in {course.code}',
                'student_name': student.name,
                'course_code': course.code,
                'status': 'present',
                'network_verified': True,
                'device_mac': device_mac,
                'timestamp': timezone.now().isoformat()
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



@login_required
def start_attendance_session(request):
    """Allow lecturers to start an attendance session with ESP32"""
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        session = request.POST.get('session', '2024/2025')
        semester = request.POST.get('semester', '1st Semester')
        
        try:
            course = Course.objects.get(id=course_id)
            
            # Check if lecturer is assigned to this course
            if not AssignedCourse.objects.filter(lecturer=request.user, course=course).exists():
                messages.error(request, "❌ You are not assigned to this course.")
                return redirect('admin_ui:dashboard')
            
            # Create or get attendance session
            attendance_session, created = AttendanceSession.objects.get_or_create(
                course=course,
                lecturer=request.user,
                session=session,
                semester=semester,
                date=timezone.now().date(),
                defaults={}
            )
            
            # Create network session for ESP32
            esp32_device = ESP32Device.objects.filter(is_active=True).first()
            if esp32_device:
                network_session, created = NetworkSession.objects.get_or_create(
                    esp32_device=esp32_device,
                    course=course,
                    lecturer=request.user,
                    session=session,
                    semester=semester,
                    date=timezone.now().date(),
                    start_time=timezone.now(),
                    is_active=True
                )
                
                messages.success(request, f"✅ Attendance session started for {course.code}!")
                messages.info(request, f"📱 Students can now connect to ESP32 WiFi: {esp32_device.ssid}")
                messages.info(request, f"🌐 ESP32 will automatically serve attendance page")
                
            else:
                messages.warning(request, "⚠️ No active ESP32 device found. Attendance session created but ESP32 integration disabled.")
            
            return redirect('admin_ui:dashboard')
            
        except Course.DoesNotExist:
            messages.error(request, "❌ Course not found.")
        except Exception as e:
            messages.error(request, f"❌ Error starting session: {str(e)}")
    
    # Get courses assigned to this lecturer
    assigned_courses = Course.objects.filter(
        assignedcourse__lecturer=request.user
    ).distinct()
    
    context = {
        'assigned_courses': assigned_courses,
        'current_session': '2024/2025',
        'current_semester': '1st Semester'
    }
    
    return render(request, 'admin_ui/start_attendance_session.html', context)

# ============================================================================
# LECTURER ATTENDANCE MANAGEMENT SYSTEM
# ============================================================================

@login_required
def lecturer_attendance_dashboard(request):
    """Dashboard for lecturers to manage attendance"""
    # Get courses assigned to this lecturer with enrollment counts
    assigned_courses = AssignedCourse.objects.filter(
        lecturer=request.user
    ).select_related('course').annotate(
        enrolled_count=models.Count('course__courseenrollment', filter=models.Q(
            courseenrollment__session=models.F('session'),
            courseenrollment__semester=models.F('semester')
        ))
    ).order_by('session', 'semester', 'course__code')
    
    # Get today's attendance sessions
    today = timezone.now().date()
    today_sessions = AttendanceSession.objects.filter(
        lecturer=request.user,
        date=today
    ).select_related('course')
    
    # Get active sessions (sessions from today that haven't been completed)
    active_sessions = AttendanceSession.objects.filter(
        lecturer=request.user,
        date=today
    ).select_related('course')
    
    # Get recent sessions (last 5 sessions)
    recent_sessions = AttendanceSession.objects.filter(
        lecturer=request.user
    ).select_related('course').order_by('-date', '-id')[:5]
    
    # Add attendance statistics to recent sessions
    for session in recent_sessions:
        attendance_records = AttendanceRecord.objects.filter(attendance_session=session)
        session.total_count = attendance_records.count()
        session.present_count = attendance_records.filter(status='present').count()
        session.absent_count = attendance_records.filter(status='absent').count()
        session.is_active = session.date == today
    
    context = {
        'assigned_courses': assigned_courses,
        'today_sessions': today_sessions,
        'active_sessions': active_sessions,
        'recent_sessions': recent_sessions,
        'today': today
    }
    
    return render(request, 'admin_ui/lecturer_attendance_dashboard.html', context)

@login_required
def start_attendance_session_view(request):
    """View to start a new attendance session"""
    if request.method == 'POST':
        course_id = request.POST.get('course')
        session = request.POST.get('session')
        semester = request.POST.get('semester')
        date = request.POST.get('date')
        time = request.POST.get('time')
        session_type = request.POST.get('session_type', 'manual')
        
        if not all([course_id, session, semester, date, time]):
            messages.error(request, "❌ Please fill in all required fields.")
            return redirect('admin_ui:start_attendance_session_new')
        
        try:
            course = Course.objects.get(id=course_id)
            
            # Check if lecturer is assigned to this course
            if not AssignedCourse.objects.filter(lecturer=request.user, course=course).exists():
                messages.error(request, "❌ You are not assigned to this course.")
                return redirect('admin_ui:lecturer_attendance_dashboard')
            
            # Check if session already exists for this course, date, and time
            existing_session = AttendanceSession.objects.filter(
                course=course,
                lecturer=request.user,
                date=date,
                time=time
            ).first()
            
            if existing_session:
                messages.info(request, f"ℹ️ Attendance session already exists for {course.code} on {date} at {time}.")
                return redirect('admin_ui:mark_attendance', session_id=existing_session.id)
            
            # Create attendance session
            attendance_session = AttendanceSession.objects.create(
                course=course,
                lecturer=request.user,
                session=session,
                semester=semester,
                date=date,
                time=time
            )
            
            messages.success(request, f"✅ Attendance session started for {course.code} on {date} at {time}!")
            return redirect('admin_ui:mark_attendance', session_id=attendance_session.id)
            
        except Course.DoesNotExist:
            messages.error(request, "❌ Course not found.")
        except Exception as e:
            messages.error(request, f"❌ Error starting session: {str(e)}")
    
    # Get courses assigned to this lecturer with session and semester info
    assigned_courses = AssignedCourse.objects.filter(
        lecturer=request.user
    ).select_related('course').order_by('course__code')
    
    context = {
        'assigned_courses': assigned_courses,
        'today_date': timezone.now().date()
    }
    
    return render(request, 'admin_ui/start_attendance_session.html', context)

@login_required
def mark_attendance_view(request, session_id):
    """View for lecturers to mark student attendance"""
    try:
        attendance_session = AttendanceSession.objects.get(
            id=session_id,
            lecturer=request.user
        )
    except AttendanceSession.DoesNotExist:
        messages.error(request, "❌ Attendance session not found.")
        return redirect('admin_ui:lecturer_attendance_dashboard')
    
    if request.method == 'POST':
        # Handle attendance marking
        for key, value in request.POST.items():
            if key.startswith('student_'):
                student_matric_no = key.replace('student_', '')
                status = value
                
                try:
                    student = Student.objects.get(matric_no=student_matric_no)
                    
                    # Check if student is enrolled in this course
                    enrollment = CourseEnrollment.objects.filter(
                        student=student,
                        course=attendance_session.course,
                        session=attendance_session.session,
                        semester=attendance_session.semester
                    ).first()
                    
                    if enrollment:
                        # Create or update attendance record
                        attendance_record, created = AttendanceRecord.objects.get_or_create(
                            attendance_session=attendance_session,
                            student=student,
                            defaults={
                                'status': status,
                                'network_verified': False,
                                'marked_by': request.user
                            }
                        )
                        
                        if not created:
                            attendance_record.status = status
                            attendance_record.marked_by = request.user
                            attendance_record.save()
                    
                except Student.DoesNotExist:
                    continue
        
        messages.success(request, "✅ Attendance marked successfully!")
        return redirect('admin_ui:view_attendance_session', session_id=session_id)
    
    # Get enrolled students for this course
    enrolled_students = CourseEnrollment.objects.filter(
        course=attendance_session.course,
        session=attendance_session.session,
        semester=attendance_session.semester
    ).select_related('student').order_by('student__name')
    
    # Get existing attendance records
    existing_records = AttendanceRecord.objects.filter(
        attendance_session=attendance_session
    ).select_related('student')
    
    # Create a dictionary of existing records for easy lookup
    attendance_dict = {record.student.matric_no: record.status for record in existing_records}
    
    context = {
        'attendance_session': attendance_session,
        'enrolled_students': enrolled_students,
        'attendance_dict': attendance_dict
    }
    
    return render(request, 'admin_ui/mark_attendance.html', context)

@login_required
def view_attendance_session_view(request, session_id):
    """View to see attendance results for a session"""
    try:
        attendance_session = AttendanceSession.objects.get(
            id=session_id,
            lecturer=request.user
        )
    except AttendanceSession.DoesNotExist:
        messages.error(request, "❌ Attendance session not found.")
        return redirect('admin_ui:lecturer_dashboard')
    
    # Get attendance records
    attendance_records = AttendanceRecord.objects.filter(
        attendance_session=attendance_session
    ).select_related('student').order_by('student__name')
    
    # Calculate statistics
    total_students = attendance_records.count()
    present_count = attendance_records.filter(status='present').count()
    absent_count = attendance_records.filter(status='absent').count()
    
    context = {
        'attendance_session': attendance_session,
        'attendance_records': attendance_records,
        'total_students': total_students,
        'present_count': present_count,
        'absent_count': absent_count
    }
    
    return render(request, 'admin_ui/view_attendance_session.html', context)

@login_required
def lecturer_attendance_history_view(request):
    """View to see all attendance sessions by this lecturer"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    # Get filter parameters
    selected_course = request.GET.get('course')
    selected_session = request.GET.get('session')
    selected_semester = request.GET.get('semester')
    selected_date_range = request.GET.get('date_range')
    
    # Base query
    attendance_sessions = AttendanceSession.objects.filter(
        lecturer=request.user
    ).select_related('course')
    
    # Apply filters
    if selected_course:
        attendance_sessions = attendance_sessions.filter(course_id=selected_course)
    
    if selected_session:
        attendance_sessions = attendance_sessions.filter(session=selected_session)
    
    if selected_semester:
        attendance_sessions = attendance_sessions.filter(semester=selected_semester)
    
    if selected_date_range:
        today = timezone.now().date()
        if selected_date_range == 'today':
            attendance_sessions = attendance_sessions.filter(date=today)
        elif selected_date_range == 'week':
            week_ago = today - timedelta(days=7)
            attendance_sessions = attendance_sessions.filter(date__gte=week_ago)
        elif selected_date_range == 'month':
            month_ago = today - timedelta(days=30)
            attendance_sessions = attendance_sessions.filter(date__gte=month_ago)
        elif selected_date_range == 'semester':
            # Assuming semester is roughly 4 months
            semester_ago = today - timedelta(days=120)
            attendance_sessions = attendance_sessions.filter(date__gte=semester_ago)
    
    # Order by date (newest first)
    attendance_sessions = attendance_sessions.order_by('-date', '-id')
    
    # Add attendance statistics to each session
    for session in attendance_sessions:
        attendance_records = AttendanceRecord.objects.filter(attendance_session=session)
        session.total_students = attendance_records.count()
        session.present_count = attendance_records.filter(status='present').count()
        session.absent_count = attendance_records.filter(status='absent').count()
        session.attendance_rate = (session.present_count / session.total_students * 100) if session.total_students > 0 else 0
    
    # Pagination
    paginator = Paginator(attendance_sessions, 20)  # 20 sessions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available filter options
    available_courses = Course.objects.filter(
        assignedcourse__lecturer=request.user
    ).distinct().order_by('code')
    
    available_sessions = AttendanceSession.objects.filter(
        lecturer=request.user
    ).values_list('session', flat=True).distinct().order_by('-session')
    
    available_semesters = AttendanceSession.objects.filter(
        lecturer=request.user
    ).values_list('semester', flat=True).distinct().order_by('semester')
    
    # Calculate overall statistics
    all_records = AttendanceRecord.objects.filter(
        attendance_session__lecturer=request.user
    )
    
    total_sessions = attendance_sessions.count()
    total_students_present = all_records.filter(status='present').count()
    total_students_absent = all_records.filter(status='absent').count()
    overall_attendance_rate = (total_students_present / (total_students_present + total_students_absent) * 100) if (total_students_present + total_students_absent) > 0 else 0
    
    context = {
        'attendance_sessions': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'available_courses': available_courses,
        'available_sessions': available_sessions,
        'available_semesters': available_semesters,
        'selected_course': selected_course,
        'selected_session': selected_session,
        'selected_semester': selected_semester,
        'selected_date_range': selected_date_range,
        'total_sessions': total_sessions,
        'total_students_present': total_students_present,
        'total_students_absent': total_students_absent,
        'overall_attendance_rate': overall_attendance_rate,
        'today_date': timezone.now().date()
    }
    
    return render(request, 'admin_ui/lecturer_attendance_history.html', context)
