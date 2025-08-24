from django.urls import path, re_path
from .views import (
    # Admin
admin_login_view,
create_admin_view,

    # Lecturer
    lecturer_login_view,
    student_login_view,
    dashboard,
    student_dashboard,
    register_lecturer_view,
    course_attendance,

    # Course Management (New)
    course_management,
    remove_student_enrollment,
    download_enrollment_template,
    
    # Enhanced Dashboard
    enhanced_dashboard,
    upload_course_students,
    view_all_enrollments,
    test_database_connection,

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
    api_mark_attendance,

    # 📋 View Assignments
    view_assignments,
    
    # 🎯 ESP32-Based Attendance Marking
    start_network_session_view,
    network_session_active_view,
    end_network_session_view,
    student_attendance_marking_view,

    # 🚀 NEW ESP32 ATTENDANCE SYSTEM URLs
    start_esp32_session_view,
    esp32_session_active_view,
    end_esp32_session_view,
    esp32_device_management_view,
    dynamic_esp32_session_view,
    
    # 🎯 Correct ESP32 Flow (Lecturer provides WiFi)
    correct_esp32_session_view,
    
    # 🔌 ESP32 API ENDPOINTS
    esp32_heartbeat_api,
    esp32_check_session_api,
    esp32_mark_attendance_api,
    esp32_register_device_api,

    # ESP32 Secure Attendance API Endpoints
    esp32_start_session_api,
    esp32_end_session_api,
    esp32_device_connected_api,
    esp32_device_disconnected_api,
    esp32_record_attendance_api,
    esp32_heartbeat_api,
    esp32_session_status_api,
    esp32_verify_student_api,
    esp32_presence_update_api,
    esp32_presence_verify_api,
    esp32_device_management,

    # ESP32 Setup and Management
    esp32_setup_view,
    esp32_start_session_view,
    esp32_session_active_view,
    esp32_end_session_view,
    
    # 🎯 Student Attendance Marking System
    student_attendance_marking_view,
    esp32_student_verification_api,
    
    # 🎯 Lecturer Attendance Session Management
    start_attendance_session,
    lecturer_attendance_dashboard,
    start_attendance_session_view,
    mark_attendance_view,
    view_attendance_session_view,
    lecturer_attendance_history_view,
)

app_name = 'admin_ui'

urlpatterns = [
    # 👤 Admin login and creation
    path('admin-login/', admin_login_view, name='admin_login'),
    path('create-admin/', create_admin_view, name='create_admin'),

    # 👨‍🏫 Lecturer login and dashboard
    path('lecturer-login/', lecturer_login_view, name='lecturer_login'),
    path('student-login/', student_login_view, name='student_login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('student-dashboard/', student_dashboard, name='student_dashboard'),
    path('register-lecturer/', register_lecturer_view, name='register_lecturer'),

    # 📚 Course Management (New)
    path('course/<int:course_id>/manage/', course_management, name='course_management'),
    re_path(r'^course/(?P<course_id>[0-9]+)/remove-student/(?P<matric_no>.+)/$', remove_student_enrollment, name='remove_student_enrollment'),
    path('course/<int:course_id>/download-template/', download_enrollment_template, name='download_enrollment_template'),
    
    # 🎯 Enhanced Dashboard
    path('enhanced-dashboard/', enhanced_dashboard, name='enhanced_dashboard'),
    path('upload-course-students/', upload_course_students, name='upload_course_students'),
    path('debug/enrollments/', view_all_enrollments, name='view_all_enrollments'),
    path('debug/test-database/', test_database_connection, name='test_database'),

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
    path('api/esp32/connected/', api_device_connected, name='api_device_connected'),
    path('api/esp32/disconnected/', api_device_disconnected, name='api_device_disconnected'),
    path('api/esp32/active-course/', api_active_course, name='api_active_course'),
    path('api/esp32/mark-attendance/', api_mark_attendance, name='api_mark_attendance'),

    # 📋 View Assignments
    path('assignments/', view_assignments, name='view_assignments'),
    
    # 🎯 ESP32-Based Attendance Marking
    path('start-network-session/', start_network_session_view, name='start_network_session'),
    path('network-session/<int:session_id>/active/', network_session_active_view, name='network_session_active'),
    path('network-session/<int:session_id>/end/', end_network_session_view, name='end_network_session'),
    path('student-attendance-marking/', student_attendance_marking_view, name='student_attendance_marking'),
    
    # 🚀 Dynamic ESP32 Session Management
    path('dynamic-esp32-session/', dynamic_esp32_session_view, name='dynamic_esp32_session'),
    
    # 🎯 Correct ESP32 Flow (Lecturer provides WiFi)
    path('correct-esp32-session/', correct_esp32_session_view, name='correct_esp32_session'),

    # 🚀 NEW ESP32 ATTENDANCE SYSTEM URLs
    path('esp32/start-session/', start_esp32_session_view, name='start_esp32_session'),
    path('esp32/session/<int:session_id>/active/', esp32_session_active_view, name='esp32_session_active'),
    path('esp32/session/<int:session_id>/end/', end_esp32_session_view, name='end_esp32_session'),
    path('esp32/devices/', esp32_device_management_view, name='esp32_device_management'),
    
    # 🔌 ESP32 API ENDPOINTS
    path('api/esp32/heartbeat/', esp32_heartbeat_api, name='esp32_heartbeat_api'),
    path('api/esp32/check-session/', esp32_check_session_api, name='esp32_check_session_api'),
    path('api/esp32/mark-attendance/', esp32_mark_attendance_api, name='esp32_mark_attendance_api'),
    path('api/esp32/register/', esp32_register_device_api, name='esp32_register_device_api'),

    # ESP32 Secure Attendance API Endpoints
    path('api/esp32/start-session/', esp32_start_session_api, name='esp32_start_session_api'),
    path('api/esp32/end-session/', esp32_end_session_api, name='esp32_end_session_api'),
    path('api/esp32/device-connected/', esp32_device_connected_api, name='esp32_device_connected_api'),
    path('api/esp32/device-disconnected/', esp32_device_disconnected_api, name='esp32_device_disconnected_api'),
    path('api/esp32/record-attendance/', esp32_record_attendance_api, name='esp32_record_attendance_api'),
    path('api/esp32/session-status/', esp32_session_status_api, name='esp32_session_status_api'),
    path('api/esp32/verify-student/', esp32_verify_student_api, name='esp32_verify_student_api'),
    
    # ESP32 Presence Verification System (Method 2)
    path('api/esp32/presence-update/', esp32_presence_update_api, name='esp32_presence_update_api'),
    path('api/esp32/presence-verify/', esp32_presence_verify_api, name='esp32_presence_verify_api'),
    path('esp32-management/', esp32_device_management, name='esp32_device_management'),

    # ESP32 Setup and Management
    path('esp32-setup/', esp32_setup_view, name='esp32_setup'),
    path('esp32-start-session/', esp32_start_session_view, name='esp32_start_session'),
    path('esp32-session-active/<int:session_id>/', esp32_session_active_view, name='esp32_session_active'),
    path('esp32-end-session/<int:session_id>/', esp32_end_session_view, name='esp32_end_session'),
    
    # 🎯 Student Attendance Marking System
    path('student-attendance-marking/', student_attendance_marking_view, name='student_attendance_marking'),
    path('api/esp32/student-verification/', esp32_student_verification_api, name='esp32_student_verification_api'),
    
    # 🎯 Lecturer Attendance Session Management
    path('start-attendance-session/', start_attendance_session, name='start_attendance_session'),
    
    # 🎯 NEW: Lecturer Manual Attendance Management System
    path('lecturer-attendance/', lecturer_attendance_dashboard, name='lecturer_attendance_dashboard'),
    path('start-attendance-session-new/', start_attendance_session_view, name='start_attendance_session_new'),
    path('mark-attendance/<int:session_id>/', mark_attendance_view, name='mark_attendance'),
    path('view-attendance-session/<int:session_id>/', view_attendance_session_view, name='view_attendance_session'),
    path('lecturer-attendance-history/', lecturer_attendance_history_view, name='lecturer_attendance_history'),
]
