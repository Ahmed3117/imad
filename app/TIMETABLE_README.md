# Timetable/Calendar Feature

## Overview
This feature provides a professional timetable/calendar system for viewing study group schedules with three role-based views:
- **Teacher View**: Shows only groups the teacher is teaching
- **Student View**: Shows only groups the student is enrolled in
- **Admin View**: Shows all groups with advanced filtering

## Features

### 1. View Modes
- **Week View**: See the entire week's schedule at a glance
- **Day View**: Focus on a single day's sessions

### 2. Filters
- **Date Navigation**: Navigate between days/weeks easily
- **Course Filter**: Filter by specific courses
- **Teacher Filter**: (Student & Admin only) Filter by specific teachers

### 3. Interactive Elements
- **Clickable Sessions**: Each group time card is clickable and navigates to the group's lecture page
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Hover Effects**: Visual feedback when hovering over sessions

### 4. Session Cards Display
Each session card shows:
- Time of the session
- Group name
- Course name and level
- Teacher name (for students and admins)
- Student count and capacity
- Track badge (if applicable)

## URLs

Access the timetables at:

### For Teachers
```
http://127.0.0.1:7777/subscriptions/timetable/teacher/
```

### For Students
```
http://127.0.0.1:7777/subscriptions/timetable/student/
```

### For Admins
```
http://127.0.0.1:7777/subscriptions/timetable/admin/
```

## Usage Examples

### View This Week's Schedule
Simply navigate to your role-specific URL (teacher/student/admin)

### View a Specific Day
1. Click the "Day" button in the view toggle
2. Select a date from the date picker
3. The schedule will update automatically

### Filter by Course
1. Use the "Course" dropdown
2. Select a specific course
3. Only sessions for that course will be displayed

### Filter by Teacher (Students & Admins only)
1. Use the "Teacher" dropdown
2. Select a specific teacher
3. Only sessions taught by that teacher will be displayed

### Navigate to Group Details
1. Click on any session card
2. You'll be redirected to that group's lecture page
3. URL format: `/accounts/profile/{teacher_id}/lectures?group={group_id}`

## Technical Details

### Files Modified/Created

1. **views.py** - Added three view functions:
   - `teacher_timetable()`
   - `student_timetable()`
   - `admin_timetable()`

2. **urls.py** - Added URL patterns for the three views

3. **templates/subscriptions/timetable.html** - Professional calendar template with:
   - Responsive design
   - Gradient headers
   - Interactive filters
   - Hover animations
   - Mobile-friendly layout

4. **templatetags/timetable_filters.py** - Custom template filter for dictionary access

### Design Features

- **Color Scheme**: Purple gradient theme (#667eea to #764ba2)
- **Card Design**: Smooth gradient backgrounds with hover transformations
- **Icons**: Font Awesome icons throughout for better UX
- **Shadows**: Subtle shadows for depth and professional appearance
- **Transitions**: Smooth animations on hover and interactions

### Data Flow

1. User selects filters (view type, date, course, teacher)
2. View function queries `StudyGroup` and `GroupTime` models
3. Filters are applied based on user role and selections
4. Timetable data is organized by day of week
5. Template renders the organized data in a professional table format

## Dependencies

- Django (already installed)
- Font Awesome (for icons - should be in base template)
- No additional Python packages required

## Browser Compatibility

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers (iOS Safari, Chrome Mobile)

## Future Enhancements (Optional)

- Export timetable to PDF
- iCal/Google Calendar integration
- Email reminders for upcoming sessions
- Conflict detection for overlapping sessions
- Print-friendly view
