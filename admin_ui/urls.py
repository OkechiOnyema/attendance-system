from django.urls import path, re_path
from .views import (
    # Superuser
    superuser_login_view,
    create_superuser_view,

    # Lecturer
    lecturer_login_view,
    student_login_view,
    dashboard,
    student_dashboard,
    register_lecturer_view,
    course_attendance,

    # Registration Officer
    registration_officer_login,
    registration_officer_dashboard,

    # Fingerprint & Enrollment
    enroll_fingerprint_view,
    de_enroll_student,
    
    # Authentication
    logout_view,

    # 🛰️ ESP32 Network-Based Attendance URLs
    esp32_device_list,
    esp32_device_create,
    esp32_device_edit,
    esp32_device_delete,

    # 🌐 Network Session Management
    network_session_list,
    network_session_create,
    network_session_end,

    # 🔌 ESP32 API Endpoints (no authentication required for device communication)
    api_device_heartbeat,
    api_device_connected,
    api_device_disconnected,
    api_active_course,

    # 📋 View Assignments
    view_assignments,
)

app_name = 'admin_ui'

urlpatterns = [
    # 👤 Superuser login and creation
    path('superuser-login/', superuser_login_view, name='superuser_login'),
    path('create-superuser/', create_superuser_view, name='create_superuser'),

    # 👨‍🏫 Lecturer login and dashboard
    path('lecturer-login/', lecturer_login_view, name='lecturer_login'),
    path('student-login/', student_login_view, name='student_login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('student-dashboard/', student_dashboard, name='student_dashboard'),
    path('register-lecturer/', register_lecturer_view, name='register_lecturer'),

    # 🗂️ Registration officer
    path('registration-officer-login/', registration_officer_login, name='registration_officer_login'),
    path('registration-officer-dashboard/', registration_officer_dashboard, name='registration_officer_dashboard'),

    # 🖐️ Fingerprint enrollment and de-enrollment
    re_path(r'^enroll-fingerprint/(?P<matric_no>.+)/$', enroll_fingerprint_view, name='enroll_fingerprint'),
    re_path(r'^de-enroll/(?P<matric_no>.+)/$', de_enroll_student, name='de_enroll_student'),

    # 🚪 Logout
    path('logout/', logout_view, name='logout'),

    # 📋 Attendance tracking
    path('course/<int:assigned_id>/attendance/', course_attendance, name='course_attendance'),

    # 🛰️ ESP32 Network-Based Attendance URLs
    path('esp32-devices/', esp32_device_list, name='esp32_device_list'),
    path('esp32-devices/create/', esp32_device_create, name='esp32_device_create'),
    path('esp32-devices/<str:device_id>/edit/', esp32_device_edit, name='esp32_device_edit'),
    path('esp32-devices/<str:device_id>/delete/', esp32_device_delete, name='esp32_device_delete'),

    # 🌐 Network Session Management
    path('network-sessions/', network_session_list, name='network_session_list'),
    path('network-sessions/create/', network_session_create, name='network_session_create'),
    path('network-sessions/<int:session_id>/end/', network_session_end, name='network_session_end'),

    # 🔌 ESP32 API Endpoints (no authentication required for device communication)
    path('api/esp32/heartbeat/', api_device_heartbeat, name='api_device_heartbeat'),
    path('api/esp32/connected/', api_device_connected, name='api_device_connected'),
    path('api/esp32/disconnected/', api_device_disconnected, name='api_device_disconnected'),
    path('api/esp32/active-course/', api_active_course, name='api_active_course'),

    # 📋 View Assignments
    path('view-assignments/', view_assignments, name='view_assignments'),
]
