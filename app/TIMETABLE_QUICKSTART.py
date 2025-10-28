"""
TIMETABLE SYSTEM - QUICK START GUIDE
====================================

URLS TO ACCESS:
--------------
Teachers:  http://127.0.0.1:7777/subscriptions/timetable/teacher/
Students:  http://127.0.0.1:7777/subscriptions/timetable/student/
Admins:    http://127.0.0.1:7777/subscriptions/timetable/admin/


FEATURES:
---------
✓ Week View / Day View toggle
✓ Filter by Course
✓ Filter by Teacher (students & admins only)
✓ Date navigation (previous/next)
✓ Clickable sessions → navigate to group lectures page
✓ Professional gradient design
✓ Responsive mobile layout
✓ Hover animations
✓ Real-time filtering


FILES CREATED/MODIFIED:
----------------------
✓ subscriptions/views.py - Added 3 timetable view functions
✓ subscriptions/urls.py - Added 3 URL patterns
✓ subscriptions/templates/subscriptions/timetable.html - Main template
✓ subscriptions/templatetags/timetable_filters.py - Custom filter for dict access
✓ subscriptions/templatetags/__init__.py - Template tags package


HOW IT WORKS:
-------------
1. User accesses role-specific URL (teacher/student/admin)
2. View queries StudyGroup and GroupTime models based on user role
3. Filters applied: course, teacher, date range
4. Data organized by day of week
5. Template renders professional calendar with clickable session cards
6. Clicking a session → redirects to: /accounts/profile/{teacher_id}/lectures?group={group_id}


SESSION CARD SHOWS:
------------------
- Time (e.g., "10:00 AM")
- Group name (e.g., "Group-1")
- Course name + level
- Teacher name (for students/admins)
- Student count / capacity
- Track badge


FILTERS AVAILABLE:
-----------------
- View Type: Week / Day
- Date: Date picker for navigation
- Course: Dropdown of available courses
- Teacher: Dropdown of teachers (students & admins only)


DESIGN:
-------
- Purple gradient theme (#667eea → #764ba2)
- Card-based layout
- Smooth hover effects (lift + color change)
- Font Awesome icons
- Box shadows for depth
- Mobile-responsive grid


TESTING:
--------
1. Login as teacher → visit /subscriptions/timetable/teacher/
2. Login as student → visit /subscriptions/timetable/student/
3. Login as admin → visit /subscriptions/timetable/admin/
4. Test filters: change view type, select dates, filter by course/teacher
5. Click on any session card → should redirect to lectures page
"""
