from django.db import models
from django.contrib.auth.models import User

# 📚 Course model
class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.code} – {self.title}"

    class Meta:
        ordering = ['code']
        verbose_name = "Course"
        verbose_name_plural = "Courses"

# 📌 Assigned course to a lecturer
class AssignedCourse(models.Model):
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    session = models.CharField(max_length=9)  # e.g. "2024/2025"
    semester = models.CharField(max_length=20)  # e.g. "1st Semester"

    def __str__(self):
        return f"{self.course.code} → {self.lecturer.username}"

    class Meta:
        ordering = ['session', 'semester', 'course__code']
        verbose_name = "Assigned Course"
        verbose_name_plural = "Assigned Courses"

# 🎓 Student model
class Student(models.Model):
    matric_no = models.CharField("Matriculation Number", max_length=20, primary_key=True)
    name = models.CharField("Full Name", max_length=100)
    department = models.CharField("Department", max_length=100, blank=True, null=True)
    level = models.CharField("Level", max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.matric_no})"

    @property
    def is_enrolled(self):
        try:
            fingerprint = getattr(self, 'fingerprintstudent', None)
            if fingerprint is None:
                # Try to get the related object directly
                fingerprint = FingerprintStudent.objects.filter(student=self).first()
            return fingerprint and fingerprint.fingerprint_data == 'enrolled'
        except Exception:
            # If there's any error, assume not enrolled
            return False

# 🔐 Fingerprint status choices
FINGERPRINT_STATUS = [
    ('not_enrolled', 'Not Enrolled'),
    ('enrolled', 'Enrolled'),
    ('error', 'Error'),
]

class FingerprintStudent(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    fingerprint_data = models.CharField(
        "Fingerprint Status",
        max_length=20,
        choices=FINGERPRINT_STATUS,
        default='not_enrolled'
    )

    def __str__(self):
        return f"Fingerprint for {self.student.name}"

# 📘 Course Enrollment
class CourseEnrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    session = models.CharField(max_length=9, default="2024/2025")  # e.g. "2024/2025"
    semester = models.CharField(max_length=20, default="1st Semester")  # e.g. "1st Semester"
    enrolled_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.course.code} ({self.session}, {self.semester})"

    class Meta:
        unique_together = ['student', 'course', 'session', 'semester']  # Student can be in multiple courses per semester
        verbose_name = "Course Enrollment"
        verbose_name_plural = "Course Enrollments"

# 🗓️ Attendance Session
class AttendanceSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.CharField(max_length=9)
    semester = models.CharField(max_length=20)
    date = models.DateField()

    def __str__(self):
        return f"{self.course.code} - {self.date}"

# ✅ Attendance Record
class AttendanceRecord(models.Model):
    attendance_session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
    ])
    marked_at = models.DateTimeField(auto_now_add=True)
    # New fields for network-based attendance
    network_verified = models.BooleanField(default=False, help_text="Whether student was connected to ESP32 network")
    device_mac = models.CharField(max_length=17, blank=True, null=True, help_text="Student device MAC address")
    esp32_device = models.ForeignKey('ESP32Device', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.attendance_session.date}: {self.status}"

# 🛰️ ESP32 Device Management
class ESP32Device(models.Model):
    device_id = models.CharField(max_length=50, unique=True, help_text="Unique identifier for ESP32 device")
    device_name = models.CharField(max_length=100, help_text="Human-readable name (e.g., 'CS101_Classroom_ESP32')")
    ssid = models.CharField(max_length=32, help_text="WiFi network name created by ESP32")
    password = models.CharField(max_length=64, help_text="WiFi password (if required)")
    location = models.CharField(max_length=200, help_text="Physical location (e.g., 'Computer Science Lab 1')")
    is_active = models.BooleanField(default=True, help_text="Whether this device is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True, help_text="Last time device was online")
    last_heartbeat = models.DateTimeField(null=True, blank=True, help_text="Last heartbeat received from ESP32")

    def __str__(self):
        return f"{self.device_name} ({self.ssid})"

    class Meta:
        verbose_name = "ESP32 Device"
        verbose_name_plural = "ESP32 Devices"

# 🌐 Network Session for Attendance
class NetworkSession(models.Model):
    esp32_device = models.ForeignKey(ESP32Device, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.CharField(max_length=9)  # e.g. "2024/2025"
    semester = models.CharField(max_length=20)  # e.g. "1st Semester"
    date = models.DateField()
    start_time = models.DateTimeField()  # Changed from TimeField to DateTimeField
    end_time = models.DateTimeField(null=True, blank=True)  # Changed from TimeField to DateTimeField
    is_active = models.BooleanField(default=True, help_text="Whether this network session is currently active")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.code} - {self.date} ({self.esp32_device.ssid})"

    class Meta:
        verbose_name = "Network Session"
        verbose_name_plural = "Network Sessions"

# 📱 Connected Device Tracking
class ConnectedDevice(models.Model):
    network_session = models.ForeignKey(NetworkSession, on_delete=models.CASCADE)
    mac_address = models.CharField(max_length=17, help_text="Device MAC address")
    device_name = models.CharField(max_length=100, blank=True, null=True, help_text="Device name if available")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)
    is_connected = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.mac_address} - {self.network_session.course.code}"

    class Meta:
        verbose_name = "Connected Device"
        verbose_name_plural = "Connected Devices"
        unique_together = ['network_session', 'mac_address']
