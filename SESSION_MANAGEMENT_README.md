# Session Management Features for Attendance System

## Overview
This document describes the enhanced session management features that ensure proper cleanup of network sessions and automatic refresh of attendance displays.

## Key Features

### 1. Enhanced Network Session Ending
- **Automatic Attendance Record Creation**: When a network session ends, all connected devices automatically create attendance records
- **Session Cleanup**: Ensures only one active session per course per date
- **Device Disconnection**: Automatically marks all connected devices as disconnected
- **Stale Session Prevention**: Prevents old sessions from interfering with new ones

### 2. Automatic Session Refresh
- **Dashboard Auto-refresh**: Sessions are automatically refreshed every 5 minutes
- **Manual Refresh Button**: Users can manually refresh sessions using the "Refresh Sessions" button
- **Real-time Status**: Shows current session status for each course
- **Connected Device Counts**: Displays real-time counts of connected devices

### 3. Session Management Utilities
- **`cleanup_expired_sessions()`**: Automatically cleans up sessions older than 4 hours
- **`refresh_active_sessions()`**: Ensures only one active session per course per date
- **Management Command**: `python manage.py cleanup_sessions` for manual cleanup

## How It Works

### When a Session Ends:
1. **Save Attendance Records**: Creates attendance records for all connected devices
2. **Disconnect Devices**: Marks all devices as disconnected with timestamp
3. **End Session**: Sets session as inactive with end time
4. **Clean Stale Sessions**: Deactivates any other active sessions for the same course/date
5. **Update Display**: Dashboard automatically refreshes to show current status

### Automatic Cleanup:
- Sessions older than 4 hours are automatically marked as inactive
- Only one active session per course per date is maintained
- Connected device counts are updated in real-time

## Usage

### For Lecturers:
1. **View Current Status**: Dashboard shows real-time session status for each course
2. **Manual Refresh**: Click "Refresh Sessions" button to force cleanup
3. **End Sessions**: Use "End Session" button to properly close network sessions
4. **Monitor Attendance**: View connected device counts and session durations

### For Administrators:
1. **Management Command**: Run `python manage.py cleanup_sessions` for manual cleanup
2. **API Endpoints**: Use `/api/sessions/refresh/` and `/api/sessions/status/` for programmatic access
3. **Force Cleanup**: Use `--force` flag with management command for immediate cleanup

## Management Commands

### Basic Cleanup:
```bash
python manage.py cleanup_sessions
```

### Dry Run (Preview):
```bash
python manage.py cleanup_sessions --dry-run
```

### Custom Expiration Time:
```bash
python manage.py cleanup_sessions --hours 6
```

### Force Cleanup:
```bash
python manage.py cleanup_sessions --force
```

## API Endpoints

### Refresh Sessions:
```
POST /api/sessions/refresh/
```
- Requires authentication
- Refreshes and cleans up all sessions
- Returns updated session counts

### Get Session Status:
```
GET /api/sessions/status/?course_id=<id>
```
- Requires authentication
- Returns current session status for a specific course
- Shows connected device counts and session duration

## Benefits

1. **Clean Session Management**: No more overlapping or stale sessions
2. **Automatic Attendance Tracking**: All connected devices are automatically recorded
3. **Real-time Updates**: Dashboard shows current session status
4. **Historical Records**: All attendance records are preserved in the database
5. **Automatic Cleanup**: Prevents sessions from staying active indefinitely
6. **Better User Experience**: Clear indication of current session status

## Technical Details

### Models Updated:
- `NetworkSession`: Enhanced with better session management
- `AttendanceRecord`: Links to network sessions for better tracking
- `ConnectedDevice`: Tracks device connection status

### Views Enhanced:
- `dashboard`: Auto-refresh and session status display
- `network_session_end`: Comprehensive session cleanup
- `network_session_list`: Real-time session information

### New Functions:
- `cleanup_expired_sessions()`: Automatic cleanup utility
- `refresh_active_sessions()`: Session refresh utility
- `api_refresh_sessions`: API endpoint for session refresh
- `api_get_session_status`: API endpoint for status checking

## Troubleshooting

### Common Issues:
1. **Sessions Not Refreshing**: Check if the management command is running
2. **Attendance Records Missing**: Ensure network sessions are properly ended
3. **Multiple Active Sessions**: Use the refresh button or management command

### Debug Commands:
```bash
# Check active sessions
python manage.py shell
>>> from admin_ui.models import NetworkSession
>>> NetworkSession.objects.filter(is_active=True).count()

# Check connected devices
>>> from admin_ui.models import ConnectedDevice
>>> ConnectedDevice.objects.filter(is_connected=True).count()
```

## Future Enhancements

1. **WebSocket Integration**: Real-time updates without page refresh
2. **Session Templates**: Predefined session configurations
3. **Advanced Analytics**: Session performance metrics
4. **Mobile App Integration**: Real-time session status on mobile devices
