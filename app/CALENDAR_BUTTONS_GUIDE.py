"""
CALENDAR NAVIGATION BUTTONS - VISUAL GUIDE
==========================================

WHERE TO FIND THE CALENDAR BUTTONS
==================================

1. NAVBAR (All pages except home)
   ┌─────────────────────────────────────────────────────────────┐
   │ Logo  Home  [📅 My Timetable]  Track Lectures  Library ... │
   └─────────────────────────────────────────────────────────────┘
   
   For Teachers:  📅 My Timetable
   For Students:  📅 My Schedule  
   For Admins:    📅 All Timetables


2. HOME PAGE - NAVBAR
   ┌─────────────────────────────────────────────────────────────┐
   │ Logo  Home  Who We Are  [📅 Calendar]  Customer Service ... │
   └─────────────────────────────────────────────────────────────┘


3. HOME PAGE - HERO SECTION (Most Prominent!)
   ┌─────────────────────────────────────────────────────────────┐
   │                                                              │
   │        Unlock Your Potential with Our E-Learning Platform   │
   │                                                              │
   │     Join thousands of learners worldwide and start your     │
   │              journey to success...                           │
   │                                                              │
   │  [Get Started]  [My Profile]  [📅 View My Timetable]  [Chat]│
   │                               ^^^^^^^^^^^^^^^^^^^^^^^^       │
   │                               NEW GREEN BUTTON!             │
   └─────────────────────────────────────────────────────────────┘


BUTTON APPEARANCE BY ROLE
=========================

TEACHER
-------
Navbar:         "My Timetable" with calendar icon
Hero Section:   Large green button "View My Timetable"
Links to:       /subscriptions/timetable/teacher/

STUDENT
-------
Navbar:         "My Schedule" with calendar icon
Hero Section:   Large green button "View My Schedule"
Links to:       /subscriptions/timetable/student/

ADMIN/SUPERUSER
---------------
Navbar:         "All Timetables" with calendar icon
Hero Section:   Large green button "View All Timetables"
Links to:       /subscriptions/timetable/admin/


VISIBILITY RULES
================
✓ Only authenticated users see the buttons
✓ Button text changes based on user role
✓ Non-authenticated users don't see calendar buttons
✓ Parent role users don't have timetable access yet


STYLING DETAILS
===============
Navbar Button:
- Standard nav-link style
- Font Awesome calendar icon (fa-calendar-alt)
- Bold font weight
- Matches other navbar links

Hero Section Button:
- Large size (btn-lg)
- Green color (btn-success)
- Calendar icon included
- Stands out as a call-to-action


TRANSLATIONS
============
English:
- my_timetable: "My Timetable"
- my_schedule: "My Schedule"
- all_timetables: "All Timetables"
- view_my_timetable: "View My Timetable"
- view_my_schedule: "View My Schedule"
- view_all_timetables: "View All Timetables"

Arabic:
- my_timetable: "جدولي التعليمي"
- my_schedule: "جدول حصصي"
- all_timetables: "كل الجداول"
- view_my_timetable: "عرض جدولي التعليمي"
- view_my_schedule: "عرض جدول حصصي"
- view_all_timetables: "عرض كل الجداول"


HOW TO TEST
===========
1. Login as teacher → See "My Timetable" in navbar
2. Go to home page → See green "View My Timetable" button
3. Click either button → Redirects to teacher timetable

4. Login as student → See "My Schedule" in navbar
5. Go to home page → See green "View My Schedule" button
6. Click either button → Redirects to student timetable

7. Login as admin → See "All Timetables" in navbar
8. Go to home page → See green "View All Timetables" button
9. Click either button → Redirects to admin timetable


FILES MODIFIED
==============
✓ templates/navbar.html - Added calendar button to main navbar
✓ about/templates/about/home.html - Added to home navbar & hero section
✓ static/translations/navbar/en.json - English navbar translations
✓ static/translations/navbar/ar.json - Arabic navbar translations
✓ static/translations/home/en.json - English home page translations
✓ static/translations/home/ar.json - Arabic home page translations


ACCESSIBILITY
=============
- Calendar icon provides visual context
- Text labels are clear and descriptive
- Links are keyboard accessible
- Works with screen readers
- Touch-friendly on mobile devices
"""
