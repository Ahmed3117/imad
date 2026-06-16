from datetime import timedelta

from django.db.models import Count
from django.utils import timezone


def get_dashboard_data(request, context):
    from about.models import (
        AccountDeletionRequest,
        ContactMessage,
        FreeSession,
        HomePageFeature,
        HomePageVideoPoint,
        LegalPage,
    )
    from accounts.models import User
    from assignment.models import Assignment, StudentAnswer
    from chat.models import Message, Room
    from courses.models import Course, Level, Track
    from library.models import CourseLibrary, LibraryCategory
    from subscriptions.models import (
        JoinRequest,
        Lecture,
        StudyGroup,
        StudyGroupResource,
    )

    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    users = User.objects.all()
    students = users.filter(role="student")
    teachers = users.filter(role="teacher")

    data = {
        # ── Summary ──
        "total_users": users.count(),
        "active_users": users.filter(is_active=True).count(),
        "total_students": students.count(),
        "active_students": students.filter(is_active=True).count(),
        "total_teachers": teachers.count(),
        "active_teachers": teachers.filter(is_active=True).count(),
        "new_users_this_month": users.filter(
            date_joined__gte=start_of_month
        ).count(),
        "new_users_this_week": users.filter(
            date_joined__gte=start_of_week
        ).count(),

        # ── Requests ──
        "unhandled_freesessions": FreeSession.objects.filter(handled=False).count(),
        "total_freesessions": FreeSession.objects.count(),
        "unhandled_contacts": ContactMessage.objects.filter(handled=False).count(),
        "total_contacts": ContactMessage.objects.count(),
        "unhandled_joinrequests": JoinRequest.objects.filter(handled=False).count(),
        "total_joinrequests": JoinRequest.objects.count(),
        "pending_deletions": AccountDeletionRequest.objects.filter(
            status="pending"
        ).count(),
        "total_deletions": AccountDeletionRequest.objects.count(),
        "processed_deletions": AccountDeletionRequest.objects.filter(
            status="processed"
        ).count(),

        # ── Study Groups & Lectures ──
        "total_study_groups": StudyGroup.objects.count(),
        "lectures_today": Lecture.objects.filter(
            live_link_date__date=now.date()
        ).count(),
        "upcoming_lectures": Lecture.objects.filter(
            live_link_date__gte=now, is_finished=False
        ).count(),
        "finished_lectures": Lecture.objects.filter(is_finished=True).count(),
        "total_lectures": Lecture.objects.count(),
        "total_students_enrolled": sum(
            g.students.count() for g in StudyGroup.objects.all()
        ),
        "total_capacity": sum(
            g.capacity or 0 for g in StudyGroup.objects.all()
        ),

        # ── Courses ──
        "total_levels": Level.objects.count(),
        "total_tracks": Track.objects.count(),
        "total_courses": Course.objects.count(),

        # ── Library ──
        "total_library_categories": LibraryCategory.objects.count(),
        "total_library_resources": CourseLibrary.objects.count(),

        # ── Chat ──
        "active_chat_rooms": Room.objects.filter(status="active").count(),
        "opened_chat_rooms": Room.objects.filter(status="opened").count(),
        "total_chat_rooms": Room.objects.count(),
        "total_messages": Message.objects.count(),

        # ── Assignments ──
        "total_assignments": Assignment.objects.count(),
        "assignments_due_this_week": Assignment.objects.filter(
            due_at__gte=now, due_at__lte=now + timedelta(days=7)
        ).count(),
        "total_submissions": StudentAnswer.objects.count(),
        "graded_submissions": StudentAnswer.objects.filter(
            grade__isnull=False
        ).count(),

        # ── Content ──
        "total_legal_pages": LegalPage.objects.count(),
        "active_legal_pages": LegalPage.objects.filter(is_active=True).count(),
        "active_features": HomePageFeature.objects.filter(is_active=True).count(),
        "active_video_points": HomePageVideoPoint.objects.filter(
            is_active=True
        ).count(),

        # ── User role breakdown ──
        "user_roles": {
            role: count
            for role, count in (
                users.values_list("role")
                .annotate(count=Count("id"))
                .order_by()
            )
        },
    }

    context["dashboard_data"] = data
    return context
