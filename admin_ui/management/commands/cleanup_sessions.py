from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from admin_ui.models import NetworkSession, ConnectedDevice
from admin_ui.views import cleanup_expired_sessions, refresh_active_sessions


class Command(BaseCommand):
    help = 'Clean up expired network sessions and refresh active sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup even if sessions are recent',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=4,
            help='Number of hours after which sessions are considered expired (default: 4)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting network session cleanup...')
        )
        
        force = options['force']
        hours = options['hours']
        dry_run = options['dry_run']
        
        current_time = timezone.now()
        cutoff_time = current_time - timedelta(hours=hours)
        
        # Find expired sessions
        expired_sessions = NetworkSession.objects.filter(
            is_active=True,
            start_time__lt=cutoff_time
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would clean up {expired_sessions.count()} expired sessions'
                )
            )
            
            for session in expired_sessions:
                duration = current_time - session.start_time
                duration_hours = duration.total_seconds() / 3600
                self.stdout.write(
                    f'  - {session.course.code} ({session.lecturer.username}): '
                    f'{duration_hours:.1f} hours old'
                )
            
            return
        
        # Perform actual cleanup
        cleaned_sessions = 0
        for session in expired_sessions:
            try:
                # End the session
                session.is_active = False
                session.end_time = current_time
                session.save()
                
                # Disconnect all devices
                ConnectedDevice.objects.filter(
                    network_session=session,
                    is_connected=True
                ).update(
                    is_connected=False,
                    disconnected_at=current_time
                )
                
                cleaned_sessions += 1
                self.stdout.write(
                    f'  ✓ Cleaned up session: {session.course.code} ({session.lecturer.username})'
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error cleaning up session {session.id}: {str(e)}'
                    )
                )
        
        # Refresh active sessions
        self.stdout.write('Refreshing active sessions...')
        refresh_active_sessions()
        
        # Get final counts
        total_active = NetworkSession.objects.filter(is_active=True).count()
        total_past = NetworkSession.objects.filter(is_active=False).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleanup completed! '
                f'Cleaned up {cleaned_sessions} expired sessions. '
                f'Active sessions: {total_active}, Past sessions: {total_past}'
            )
        )
