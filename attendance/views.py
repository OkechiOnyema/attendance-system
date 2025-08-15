
from django.shortcuts import render
from .models import Student
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect

@login_required
def attendance_view(request):
    return render(request, 'attendance.html')

@login_required
def attendance_dashboard(request):
    students = Student.objects.all()
    return render(request, 'attendance/attendance.html', {'students': students})

def custom_logout_view(request):
    logout(request)
    messages.success(request, "✅ You have been logged out successfully.")
    return redirect('superuser_login')  # or any named URL you prefer

def mark_attendance(request, student_id):
    # your attendance logic here
    messages.success(request, 'Attendance marked for student.')
    return redirect('attendance_page')