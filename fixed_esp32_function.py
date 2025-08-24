# Fixed ESP32 Student Verification API Function
# Replace the existing function in admin_ui/views.py

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
