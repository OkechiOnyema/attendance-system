from django.core.management.base import BaseCommand
from admin_ui.models import Course
from admin_ui.utils import load_courses_from_csv

class Command(BaseCommand):
    help = 'Load courses from courses.csv file into the database'

    def handle(self, *args, **options):
        self.stdout.write('Loading courses from courses.csv...')
        
        # Load courses from CSV
        courses_data = load_courses_from_csv('courses.csv')
        
        if not courses_data:
            self.stdout.write(self.style.ERROR('No courses found in courses.csv'))
            return
        
        created_count = 0
        updated_count = 0
        
        for course_data in courses_data:
            course, created = Course.objects.update_or_create(
                code=course_data['code'],
                defaults={'title': course_data['title']}
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created: {course.code} - {course.title}')
            else:
                updated_count += 1
                self.stdout.write(f'Updated: {course.code} - {course.title}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(courses_data)} courses. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
