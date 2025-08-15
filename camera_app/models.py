from django.db import models
from students.models import Student

class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student.name} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
