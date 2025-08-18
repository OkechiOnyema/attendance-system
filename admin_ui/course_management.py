from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count
from django.core.paginator import Paginator
from .models import Course, Student, CourseEnrollment, AssignedCourse
from .forms import StudentCSVUploadForm
import csv
import io
from datetime import datetime
from django.http import HttpResponse

@login_required
def enhanced_dashboard(request):
    """
    Enhanced lecturer dashboard with multiple department uploads and course-specific student display
    """
    try:
        # Test database connection and model access
        print(f"DEBUG: User: {request.user.username}")
        print(f"DEBUG: User is authenticated: {request.user.is_authenticated}")
        
        # Get assigned courses for this lecturer
        assigned_courses = AssignedCourse.objects.filter(lecturer=request.user)
        print(f"DEBUG: Found {assigned_courses.count()} assigned courses")
        
        # Get course-specific enrollments for display
        course_enrollments = {}
        total_students = 0
        total_enrollments = 0
        unique_student_ids = set()  # Use a set to track unique students
        
        for assigned in assigned_courses:
            print(f"DEBUG: Processing course: {assigned.course.code}")
            # Get students enrolled in this specific course, session, and semester
            enrollments = CourseEnrollment.objects.filter(
                course=assigned.course,
                session=assigned.session,
                semester=assigned.semester
            ).select_related('student').order_by('student__name')
            
            print(f"DEBUG: Found {enrollments.count()} enrollments for {assigned.course.code}")
            
            course_enrollments[assigned.course.id] = {
                'course': assigned.course,
                'assigned': assigned,
                'enrollments': enrollments,
                'count': enrollments.count()
            }
            
            total_enrollments += enrollments.count()
            # Add student IDs to the set for unique counting
            for enrollment in enrollments:
                unique_student_ids.add(enrollment.student.matric_no)
        
        # Count unique students
        total_students = len(unique_student_ids)
        print(f"DEBUG: Total unique students: {total_students}")
        print(f"DEBUG: Total enrollments: {total_enrollments}")
        
        # Pagination for the first course (if any)
        page_obj = None
        if assigned_courses.exists() and course_enrollments:
            first_course = list(course_enrollments.values())[0]
            paginator = Paginator(first_course['enrollments'], 25)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
        
        context = {
            'assigned_courses': assigned_courses,
            'course_enrollments': course_enrollments,
            'first_course_students': page_obj,
            'total_students': total_students,
            'total_enrollments': total_enrollments,
            'active_sessions': 0,  # You can implement this based on your session model
        }
        
        return render(request, 'admin_ui/enhanced_dashboard.html', context)
        
    except Exception as e:
        print(f"ERROR in enhanced_dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return a simple error context
        context = {
            'assigned_courses': [],
            'course_enrollments': {},
            'first_course_students': None,
            'total_students': 0,
            'total_enrollments': 0,
            'active_sessions': 0,
            'error_message': f"An error occurred: {str(e)}"
        }
        
        return render(request, 'admin_ui/enhanced_dashboard.html', context)

@login_required
def upload_course_students(request):
    """
    Handle course-specific student uploads
    """
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        session = request.POST.get('session')
        semester = request.POST.get('semester')
        csv_file = request.FILES.get('csv_file')
        
        # Debug logging
        print(f"DEBUG: Upload request received")
        print(f"DEBUG: course_id = {course_id}")
        print(f"DEBUG: session = {session}")
        print(f"DEBUG: semester = {semester}")
        print(f"DEBUG: csv_file = {csv_file}")
        
        # Add file hash to prevent duplicate processing
        if csv_file:
            import hashlib
            file_content = csv_file.read()
            file_hash = hashlib.md5(file_content).hexdigest()
            csv_file.seek(0)  # Reset file pointer for processing
            print(f"DEBUG: File hash: {file_hash}")
            print(f"DEBUG: File size: {len(file_content)} bytes")
        
        if not csv_file:
            messages.error(request, 'Please select a CSV file')
            return redirect('admin_ui:enhanced_dashboard')
        
        if not course_id:
            messages.error(request, 'Course information is missing')
            return redirect('admin_ui:enhanced_dashboard')
        
        try:
            # Get the course and verify lecturer is assigned to it
            course = get_object_or_404(Course, id=course_id)
            assigned_course = get_object_or_404(
                AssignedCourse, 
                course=course, 
                lecturer=request.user
            )
            
            print(f"DEBUG: Course found: {course.code} - {course.title}")
            print(f"DEBUG: Assigned course session: {assigned_course.session}")
            print(f"DEBUG: Assigned course semester: {assigned_course.semester}")
            
            # Use the assigned course's session and semester if not provided
            if not session:
                session = assigned_course.session
            if not semester:
                semester = assigned_course.semester
            
            print(f"DEBUG: Final session: {session}")
            print(f"DEBUG: Final semester: {semester}")
            
            # Check current enrollments for this course BEFORE upload
            current_enrollments_before = CourseEnrollment.objects.filter(
                course=course,
                session=session,
                semester=semester
            ).count()
            print(f"DEBUG: Current enrollments for {course.code} BEFORE upload: {current_enrollments_before}")
            
            # Check ALL enrollments for this course (across all sessions/semesters)
            all_course_enrollments = CourseEnrollment.objects.filter(course=course)
            print(f"DEBUG: ALL enrollments for {course.code} (all sessions/semesters): {all_course_enrollments.count()}")
            for enrollment in all_course_enrollments[:5]:  # Show first 5
                print(f"DEBUG:   - {enrollment.student.matric_no} ({enrollment.session}, {enrollment.semester})")
            
            # Check if there are other courses that might be getting affected
            print(f"DEBUG: Checking for other courses that might be affected...")
            all_courses = Course.objects.all()
            for other_course in all_courses:
                if other_course.id != course.id:
                    other_enrollments = CourseEnrollment.objects.filter(course=other_course)
                    if other_enrollments.exists():
                        print(f"DEBUG: Course {other_course.code} has {other_enrollments.count()} enrollments")
                        # Show a few examples
                        for enrollment in other_enrollments[:3]:
                            print(f"DEBUG:   - {enrollment.student.matric_no} ({enrollment.session}, {enrollment.semester})")
            
            # Process the CSV and enroll students in this specific course
            success_count, error_count, errors = process_student_csv(
                csv_file, course, session, semester
            )
            
            print(f"DEBUG: Processed CSV - Success: {success_count}, Errors: {error_count}")
            
            # Check current enrollments for this course AFTER upload
            current_enrollments_after = CourseEnrollment.objects.filter(
                course=course,
                session=session,
                semester=semester
            ).count()
            print(f"DEBUG: Current enrollments for {course.code} AFTER upload: {current_enrollments_after}")
            print(f"DEBUG: Net change in enrollments: {current_enrollments_after - current_enrollments_before}")
            
            if success_count > 0:
                messages.success(
                    request,
                    f'✅ Successfully enrolled {success_count} students in {course.code} ({session}, {semester})'
                )
            
            if error_count > 0:
                messages.warning(
                    request,
                    f'⚠️ {error_count} students could not be enrolled. Check the details below.'
                )
                for error in errors[:5]:  # Show first 5 errors
                    messages.error(request, f"Error: {error}")
                    
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            messages.error(request, f'❌ Error processing CSV: {str(e)}')
    
    return redirect('admin_ui:enhanced_dashboard')

# REMOVED: process_course_csv function - using process_student_csv instead

@login_required
def course_management(request, course_id):
    """
    Course management page for lecturers to upload students and view enrollments
    """
    # Get the course and verify the lecturer is assigned to it
    course = get_object_or_404(Course, id=course_id)
    assigned_course = get_object_or_404(
        AssignedCourse, 
        course=course, 
        lecturer=request.user
    )
    
    # Get enrolled students for this SPECIFIC course, session, and semester
    enrolled_students = CourseEnrollment.objects.filter(
        course=course,
        session=assigned_course.session,
        semester=assigned_course.semester
    ).select_related('student').order_by('student__name')
    
    # Pagination
    paginator = Paginator(enrolled_students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Handle CSV upload
    if request.method == 'POST':
        form = StudentCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            session = form.cleaned_data.get('session') or assigned_course.session
            semester = form.cleaned_data.get('semester') or assigned_course.semester
            
            try:
                success_count, error_count, errors = process_student_csv(
                    csv_file, course, session, semester
                )
                
                if success_count > 0:
                    messages.success(
                        request, 
                        f'✅ Successfully enrolled {success_count} students in {course.code} ({session}, {semester})'
                    )
                
                if error_count > 0:
                    messages.warning(
                        request, 
                        f'⚠️ {error_count} students could not be enrolled. Check the details below.'
                    )
                    for error in errors[:5]:  # Show first 5 errors
                        messages.error(request, f"Error: {error}")
                
                return redirect('admin_ui:course_management', course_id=course_id)
                
            except Exception as e:
                messages.error(request, f'❌ Error processing CSV: {str(e)}')
    else:
        form = StudentCSVUploadForm(initial={
            'session': assigned_course.session,
            'semester': assigned_course.semester
        })
    
    context = {
        'course': course,
        'assigned_course': assigned_course,
        'enrolled_students': page_obj,
        'form': form,
        'total_enrolled': enrolled_students.count(),
    }
    
    return render(request, 'admin_ui/course_management.html', context)

@login_required
def remove_student_enrollment(request, course_id, matric_no):
    """
    Remove a student from a course enrollment
    """
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        student = get_object_or_404(Student, matric_no=matric_no)
        
        # Verify lecturer is assigned to this course
        assigned_course = get_object_or_404(
            AssignedCourse, 
            course=course, 
            lecturer=request.user
        )
        
        # Remove enrollment
        enrollment = CourseEnrollment.objects.filter(
            student=student,
            course=course,
            session=assigned_course.session,
            semester=assigned_course.semester
        ).first()
        
        if enrollment:
            enrollment.delete()
            messages.success(
                request, 
                f'✅ {student.name} removed from {course.code}'
            )
        else:
            messages.error(
                request, 
                f'❌ {student.name} is not enrolled in {course.code}'
            )
    
    return redirect('admin_ui:course_management', course_id=course_id)

def process_student_csv(csv_file, course, session, semester):
    """
    Process CSV file and enroll students in the specific course
    This function ensures students are only enrolled in the specified course per semester
    """
    success_count = 0
    error_count = 0
    errors = []
    
    print(f"DEBUG: process_student_csv called for course: {course.code}, session: {session}, semester: {semester}")
    
    # Read CSV content
    content = csv_file.read().decode('utf-8')
    print(f"DEBUG: CSV content length: {len(content)} characters")
    print(f"DEBUG: CSV content preview: {content[:200]}...")
    
    csv_reader = csv.DictReader(io.StringIO(content))
    print(f"DEBUG: CSV fieldnames: {csv_reader.fieldnames}")
    
    # Count total rows
    rows = list(csv_reader)
    print(f"DEBUG: Total CSV rows (excluding header): {len(rows)}")
    
    if not rows:
        print("DEBUG: No data rows found in CSV!")
        errors.append("No data rows found in CSV file")
        return 0, 1, errors
    
    # Reset for processing
    csv_reader = csv.DictReader(io.StringIO(content))
    
    with transaction.atomic():
        for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (1 is header)
            try:
                # Extract student data
                matric_no = row.get('matric_no', '').strip()
                name = row.get('name', '').strip()
                department = row.get('department', '').strip()
                level = row.get('level', '').strip()
                
                print(f"DEBUG: Processing row {row_num}: {matric_no} - {name}")
                
                # Validate required fields
                if not matric_no or not name:
                    errors.append(f"Row {row_num}: Missing matric_no or name")
                    error_count += 1
                    continue
                
                # Get or create student (this only affects the Student model, not enrollments)
                try:
                    student, created = Student.objects.get_or_create(
                        matric_no=matric_no,
                        defaults={
                            'name': name,
                            'department': department or 'General',
                            'level': level or '100'
                        }
                    )
                    
                    print(f"DEBUG: Student {'created' if created else 'found'}: {student.matric_no} - {student.name}")
                    print(f"DEBUG: Student object: {student}")
                    print(f"DEBUG: Student matric_no: {student.matric_no}")
                    
                    if not created:
                        # Update existing student info (this doesn't affect course enrollments)
                        student.name = name
                        if department:
                            student.department = department
                        if level:
                            student.level = level
                        student.save()
                        print(f"DEBUG: Updated existing student: {student}")
                        
                except Exception as e:
                    print(f"DEBUG: Error creating/finding student {matric_no}: {str(e)}")
                    errors.append(f"Row {row_num}: Error with student {matric_no}: {str(e)}")
                    error_count += 1
                    continue
                
                # Check if student is already enrolled in THIS SPECIFIC course for this session/semester
                existing_enrollment = CourseEnrollment.objects.filter(
                    student=student,
                    course=course,
                    session=session,
                    semester=semester
                ).first()
                
                print(f"DEBUG: Checking existing enrollment for {student.matric_no} in {course.code} for {session}, {semester}")
                print(f"DEBUG: Existing enrollment found: {existing_enrollment is not None}")
                
                if existing_enrollment:
                    # Student already enrolled in this specific course - count as success
                    print(f"DEBUG: Student {student.matric_no} already enrolled in {course.code}")
                    success_count += 1
                    continue
                
                # Check if student is enrolled in OTHER courses for this session/semester
                other_enrollments = CourseEnrollment.objects.filter(
                    student=student,
                    session=session,
                    semester=semester
                ).exclude(course=course)
                
                if other_enrollments.exists():
                    print(f"DEBUG: Student {student.matric_no} is also enrolled in other courses for {session}, {semester}")
                    for other_enrollment in other_enrollments:
                        print(f"DEBUG:   - Also enrolled in: {other_enrollment.course.code}")
                
                # Note: We don't delete other enrollments - students can be in multiple courses
                
                # Create NEW enrollment ONLY for this specific course
                print(f"DEBUG: Creating new enrollment for {student.matric_no} in {course.code}")
                try:
                    enrollment = CourseEnrollment.objects.create(
                        student=student,
                        course=course,
                        session=session,
                        semester=semester
                    )
                    print(f"DEBUG: Enrollment created successfully: {enrollment}")
                    print(f"DEBUG: Enrollment ID: {enrollment.id}")
                    print(f"DEBUG: Student matric_no: {student.matric_no}")
                    print(f"DEBUG: Course code: {course.code}")
                    
                    print(f"DEBUG: Successfully enrolled {student.matric_no} in {course.code}")
                    success_count += 1
                    
                except Exception as e:
                    print(f"DEBUG: Error creating enrollment for {student.matric_no}: {str(e)}")
                    errors.append(f"Row {row_num}: Error creating enrollment for {student.matric_no}: {str(e)}")
                    error_count += 1
                    continue
                
                # Log the total enrollments for this student in this session/semester
                total_enrollments = CourseEnrollment.objects.filter(
                    student=student,
                    session=session,
                    semester=semester
                ).count()
                print(f"DEBUG: Student {student.matric_no} now has {total_enrollments} total enrollments for {session}, {semester}")
                    
            except Exception as e:
                print(f"DEBUG: Error processing row {row_num}: {str(e)}")
                errors.append(f"Row {row_num}: {str(e)}")
                error_count += 1
    
    print(f"DEBUG: process_student_csv completed. Success: {success_count}, Errors: {error_count}")
    
    # Log summary of enrollments across all courses for this session/semester
    total_enrollments = CourseEnrollment.objects.filter(session=session, semester=semester).count()
    print(f"DEBUG: Total enrollments across ALL courses for {session}, {semester}: {total_enrollments}")
    
    # Show breakdown by course
    course_breakdown = CourseEnrollment.objects.filter(
        session=session, 
        semester=semester
    ).values('course__code').annotate(count=Count('id')).order_by('course__code')
    
    for course_info in course_breakdown:
        print(f"DEBUG: Course {course_info['course__code']}: {course_info['count']} students")
    
    return success_count, error_count, errors

@login_required
def test_database_connection(request):
    """
    Test database connection and basic operations
    """
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin required.')
        return redirect('admin_ui:enhanced_dashboard')
    
    debug_info = []
    
    try:
        # Test Student model
        student_count = Student.objects.count()
        debug_info.append(f"Student count: {student_count}")
        
        # Test Course model
        course_count = Course.objects.count()
        debug_info.append(f"Course count: {course_count}")
        
        # Test CourseEnrollment model
        enrollment_count = CourseEnrollment.objects.count()
        debug_info.append(f"Enrollment count: {enrollment_count}")
        
        # Test AssignedCourse model
        assigned_count = AssignedCourse.objects.count()
        debug_info.append(f"Assigned course count: {assigned_count}")
        
        # Test creating a test student
        try:
            test_student, created = Student.objects.get_or_create(
                matric_no='TEST001',
                defaults={
                    'name': 'Test Student',
                    'department': 'Test Department',
                    'level': '100'
                }
            )
            debug_info.append(f"Test student {'created' if created else 'found'}: {test_student.matric_no}")
            
            # Clean up test student
            if created:
                test_student.delete()
                debug_info.append("Test student cleaned up")
                
        except Exception as e:
            debug_info.append(f"Error with test student: {str(e)}")
        
        debug_info.append("Database connection test completed successfully")
        
    except Exception as e:
        debug_info.append(f"Database error: {str(e)}")
    
    context = {
        'debug_info': debug_info
    }
    
    return render(request, 'admin_ui/test_database.html', context)

@login_required
def view_all_enrollments(request):
    """
    View all enrollments across all courses for debugging purposes
    """
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin required.')
        return redirect('admin_ui:enhanced_dashboard')
    
    # Get all enrollments grouped by session and semester
    enrollments_by_session = {}
    
    all_enrollments = CourseEnrollment.objects.select_related(
        'student', 'course'
    ).order_by('session', 'semester', 'course__code', 'student__name')
    
    for enrollment in all_enrollments:
        session_key = f"{enrollment.session} - {enrollment.semester}"
        if session_key not in enrollments_by_session:
            enrollments_by_session[session_key] = {}
        
        course_code = enrollment.course.code
        if course_code not in enrollments_by_session[session_key]:
            enrollments_by_session[session_key][course_code] = []
        
        enrollments_by_session[session_key][course_code].append(enrollment)
    
    context = {
        'enrollments_by_session': enrollments_by_session,
        'total_enrollments': all_enrollments.count(),
        'total_students': Student.objects.count(),
        'total_courses': Course.objects.count(),
    }
    
    return render(request, 'admin_ui/view_all_enrollments.html', context)

@login_required
def download_enrollment_template(request, course_id):
    """
    Download CSV template for student enrollment
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Create CSV content
    csv_content = "matric_no,name,department,level\n"
    csv_content += "2021001,John Doe,Computer Science,100\n"
    csv_content += "2021002,Jane Smith,Computer Science,100\n"
    csv_content += "2021003,Bob Johnson,Computer Science,100\n"
    
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{course.code}_enrollment_template.csv"'
    
    return response
