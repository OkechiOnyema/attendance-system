from django.contrib import admin
from .models import (
    Course, AssignedCourse, Student, FingerprintStudent, 
    CourseEnrollment, AttendanceSession, AttendanceRecord,
    ESP32Device, NetworkSession, ConnectedDevice
)

# Course Management
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'title']
    search_fields = ['code', 'title']
    ordering = ['code']

@admin.register(AssignedCourse)
class AssignedCourseAdmin(admin.ModelAdmin):
    list_display = ['course', 'lecturer', 'session', 'semester']
    list_filter = ['session', 'semester']
    search_fields = ['course__code', 'lecturer__username']

# Student Management
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['matric_no', 'name', 'department', 'level']
    search_fields = ['matric_no', 'name', 'department']
    list_filter = ['department', 'level']

@admin.register(FingerprintStudent)
class FingerprintStudentAdmin(admin.ModelAdmin):
    list_display = ['student', 'fingerprint_data']
    list_filter = ['fingerprint_data']

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'session', 'semester', 'enrolled_on']
    list_filter = ['session', 'semester', 'enrolled_on']
    search_fields = ['student__name', 'course__code']

# Attendance Management
@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['course', 'lecturer', 'session', 'semester', 'date']
    list_filter = ['session', 'semester', 'date']

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'attendance_session', 'status', 'marked_at', 'network_verified']
    list_filter = ['status', 'network_verified', 'marked_at']
    search_fields = ['student__name', 'student__matric_no']

# ESP32 Device Management
@admin.register(ESP32Device)
class ESP32DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'device_name', 'ssid', 'location', 'is_active', 'last_seen', 'last_heartbeat']
    list_filter = ['is_active', 'created_at']
    search_fields = ['device_id', 'device_name', 'ssid', 'location']
    readonly_fields = ['last_seen', 'last_heartbeat']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('device_id', 'device_name', 'ssid', 'password', 'location')
        }),
        ('Status', {
            'fields': ('is_active', 'last_seen', 'last_heartbeat')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(NetworkSession)
class NetworkSessionAdmin(admin.ModelAdmin):
    list_display = ['course', 'lecturer', 'esp32_device', 'session', 'semester', 'date', 'is_active']
    list_filter = ['session', 'semester', 'date', 'is_active']
    search_fields = ['course__code', 'lecturer__username', 'esp32_device__device_name']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('course', 'lecturer', 'session', 'semester', 'date')
        }),
        ('ESP32 Device', {
            'fields': ('esp32_device',)
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'is_active')
        }),
    )

@admin.register(ConnectedDevice)
class ConnectedDeviceAdmin(admin.ModelAdmin):
    list_display = ['network_session', 'mac_address', 'device_name', 'ip_address', 'is_connected', 'connected_at']
    list_filter = ['is_connected', 'connected_at']
    search_fields = ['mac_address', 'device_name', 'network_session__course__code']
