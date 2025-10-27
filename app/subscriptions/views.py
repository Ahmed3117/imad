from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, Q, Max
from django.utils import timezone
from django.utils.translation import gettext as _
from assignment.models import Assignment, StudentAnswer
from subscriptions.models import LectureNote, StudyGroup, GroupTime
from collections import defaultdict
import json
from django.shortcuts import render
from datetime import datetime, timedelta
from courses.models import Course
from django.contrib.auth import get_user_model

User = get_user_model()



# subscriptions/views.py
from django.shortcuts import redirect
from django.urls import reverse
from django import forms
from django.utils import timezone
from datetime import datetime
from .models import StudyGroup, StudyGroupReport  # Import the new model

class DateFilterForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )

class StudyGroupReportView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = StudyGroup
    template_name = 'subscriptions/studygroup_report.html'
    context_object_name = 'group'

    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        group = self.get_object()
        form = DateFilterForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            # Handle "Save Last Reported Date" button
            if 'save_last_reported_date' in request.POST and end_date:
                report, created = StudyGroupReport.objects.get_or_create(study_group=group)
                report.last_reported_date = end_date
                report.save()

        # Redirect to the same page with the filtered dates
        return redirect(
            reverse('subscriptions:studygroup_report', kwargs={'pk': group.pk}) +
            f'?start_date={start_date or ""}&end_date={end_date or ""}'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()

        # Initialize the date filter form
        form = DateFilterForm(self.request.GET)
        start_date = None
        end_date = None
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

        # Get the last reported date
        last_reported_date = None
        try:
            report = StudyGroupReport.objects.get(study_group=group)
            last_reported_date = report.last_reported_date
        except StudyGroupReport.DoesNotExist:
            pass

        # Filter lectures by date range
        lectures = group.lectures.annotate(
            note_count=Count('notes'),
            visit_count=Count('visit_history'),
            avg_rating=Avg('notes__rating', filter=Q(notes__rating__isnull=False)),
            teacher_status=Count('notes', filter=Q(notes__user__role='teacher')),
            last_visit=Max('visit_history__visited_at')
        ).prefetch_related(
            'notes',
            'notes__user',
            'visit_history',
            'visit_history__user'
        )

        # Apply date filtering if provided
        if start_date:
            lectures = lectures.filter(live_link_date__gte=start_date)
        if end_date:
            # Include the end of the day for end_date
            end_date = datetime.combine(end_date, datetime.max.time())
            end_date = timezone.make_aware(end_date)
            lectures = lectures.filter(live_link_date__lte=end_date)

        lectures = lectures.order_by('-live_link_date')

        # Calculate overall statistics
        total_lectures = lectures.count()
        finished_lectures = lectures.filter(is_finished=True).count()
        avg_group_rating = lectures.aggregate(
            overall_avg=Avg('avg_rating'))['overall_avg'] or 0
        total_visits = sum(lecture.visit_count for lecture in lectures)

        # Visit statistics for charts
        visit_data = {
            'by_day': defaultdict(int),
            'by_hour': [0] * 24
        }

        # Process visit data for charts
        for lecture in lectures:
            for visit in lecture.visit_history.all():
                visit_date = timezone.localtime(visit.visited_at)
                # Only include visits within the date range
                if (not start_date or visit_date.date() >= start_date) and \
                   (not end_date or visit_date <= end_date):
                    visit_data['by_day'][visit_date.date()] += 1
                    visit_data['by_hour'][visit_date.hour] += 1

        # Convert visit data to chart-friendly formats
        visit_days = sorted(visit_data['by_day'].items())
        visit_day_labels = [day.strftime('%Y-%m-%d') for day, _ in visit_days]
        visit_day_counts = [count for _, count in visit_days]

        # Assignment data report
        assignments = Assignment.objects.filter(lecture__group=group)
        if start_date:
            assignments = assignments.filter(lecture__live_link_date__gte=start_date)
        if end_date:
            end_date_aware = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
            assignments = assignments.filter(lecture__live_link_date__lte=end_date_aware)

        students = group.students.all()

        report_data = []
        total_grades = []
        assignment_grades_map = {assignment.id: [] for assignment in assignments}

        completion_counts = {
            'completed': 0,
            'partial': 0,
            'not_started': 0
        }

        for student in students:
            student_data = {
                'student': student,
                'assignments': [],
                'average_grade': None
            }
            grades = []
            total_answered = 0

            for assignment in assignments:
                answer = StudentAnswer.objects.filter(
                    assignment=assignment,
                    student=student
                ).first()

                grade = answer.grade if answer else None

                student_data['assignments'].append({
                    'assignment': assignment,
                    'answer': answer,
                    'grade': grade
                })

                if answer and grade is not None:
                    grades.append(grade)
                    assignment_grades_map[assignment.id].append(grade)
                    total_answered += 1

            if grades:
                avg = sum(grades) / len(grades)
                student_data['average_grade'] = avg
                total_grades.append(avg)

                if total_answered == assignments.count():
                    completion_counts['completed'] += 1
                elif total_answered > 0:
                    completion_counts['partial'] += 1
                else:
                    completion_counts['not_started'] += 1

            report_data.append(student_data)

        # Calculate average grade for each assignment
        for assignment in assignments:
            assignment_grades = assignment_grades_map[assignment.id]
            if assignment_grades:
                assignment.average_grade = sum(assignment_grades) / len(assignment_grades)
            else:
                assignment.average_grade = None

        # Grade distribution for chart
        grade_distribution = [0] * 6
        for avg in total_grades:
            if avg >= 90:
                grade_distribution[0] += 1
            elif avg >= 80:
                grade_distribution[1] += 1
            elif avg >= 70:
                grade_distribution[2] += 1
            elif avg >= 60:
                grade_distribution[3] += 1
            elif avg >= 50:
                grade_distribution[4] += 1
            else:
                grade_distribution[5] += 1

        # Completion chart data
        completion_status = [
            completion_counts['completed'],
            completion_counts['partial'],
            completion_counts['not_started']
        ]

        # Overall average
        overall_average = sum(total_grades) / len(total_grades) if total_grades else None

        # Prepare visit details for each lecture
        lecture_visit_details = []
        for lecture in lectures:
            visits = lecture.visit_history.all().order_by('visited_at')
            visit_details = []
            prev_visit = None
            for visit in visits:
                visit_time = timezone.localtime(visit.visited_at)
                # Only include visits within the date range
                if (not start_date or visit_time.date() >= start_date) and \
                   (not end_date or visit_time <= end_date):
                    duration = None
                    if prev_visit:
                        duration = (visit_time - prev_visit).total_seconds() / 60.0
                    visit_details.append({
                        'user': visit.user.get_full_name() or visit.user.username,
                        'user_role': visit.user.role,
                        'visited_at': visit_time.isoformat(),
                        'duration': duration
                    })
                    prev_visit = visit_time
            lecture_visit_details.append({
                'lecture_id': lecture.id,
                'title': lecture.title,
                'visits': visit_details
            })

        context.update({
            'lectures': lectures,
            'teacher_notes': LectureNote.objects.filter(
                lecture__group=group,
                user__role='teacher'
            ).select_related('lecture', 'user'),
            'total_lectures': total_lectures,
            'finished_lectures': finished_lectures,
            'avg_group_rating': avg_group_rating,
            'total_visits': total_visits,
            'assignments': assignments,
            'report_data': report_data,
            'overall_average': overall_average,
            'grade_distribution': json.dumps(grade_distribution),
            'completion_status': json.dumps(completion_status),
            'visit_day_labels': json.dumps(visit_day_labels),
            'visit_day_counts': json.dumps(visit_day_counts),
            'visit_hour_counts': json.dumps(visit_data['by_hour']),
            'lecture_visit_details': json.dumps(lecture_visit_details),
            'form': form,
            'last_reported_date': last_reported_date,
        })

        return context


# Timetable/Calendar Views

def teacher_timetable(request):
    """Timetable view for teachers - shows only their groups"""
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return redirect('accounts:login')
    
    # Get filter parameters
    view_type = request.GET.get('view', 'week')  # 'day' or 'week'
    course_id = request.GET.get('course', '')
    selected_day = request.GET.get('day', 'MON')  # Default to Monday for day view
    
    # Get teacher's groups
    groups = StudyGroup.objects.filter(teacher=request.user).select_related('course', 'course__level', 'course__track')
    
    # Filter by course if selected
    if course_id:
        groups = groups.filter(course_id=course_id)
    
    # Get all group times for these groups
    group_times = GroupTime.objects.filter(group__in=groups).select_related('group', 'group__course')
    
    # Build timetable structure
    days_of_week = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    day_names = [_('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'), _('Friday'), _('Saturday'), _('Sunday')]
    
    if view_type == 'day':
        # Single day view
        day_times = group_times.filter(day=selected_day).order_by('time')
        timetable = {selected_day: list(day_times)}
        display_days = [(selected_day, day_names[days_of_week.index(selected_day)])]
    else:
        # Week view
        timetable = {day: [] for day in days_of_week}
        for gt in group_times.order_by('day', 'time'):
            timetable[gt.day].append(gt)
        display_days = list(zip(days_of_week, day_names))
    
    # Get unique courses for filter dropdown
    teacher_courses = Course.objects.filter(study_groups__teacher=request.user).distinct()
    
    context = {
        'timetable': timetable,
        'display_days': display_days,
        'view_type': view_type,
        'selected_day': selected_day,
        'courses': teacher_courses,
        'selected_course': course_id,
        'user_role': 'teacher',
    }
    
    return render(request, 'subscriptions/timetable.html', context)


def student_timetable(request):
    """Timetable view for students - shows groups they're enrolled in"""
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('accounts:login')
    
    # Get filter parameters
    view_type = request.GET.get('view', 'week')
    course_id = request.GET.get('course', '')
    teacher_id = request.GET.get('teacher', '')
    selected_day = request.GET.get('day', 'MON')
    
    # Get student's enrolled groups
    groups = request.user.study_groups.all().select_related('course', 'course__level', 'course__track', 'teacher')
    
    # Filter by course if selected
    if course_id:
        groups = groups.filter(course_id=course_id)
    
    # Filter by teacher if selected
    if teacher_id:
        groups = groups.filter(teacher_id=teacher_id)
    
    # Get all group times for these groups
    group_times = GroupTime.objects.filter(group__in=groups).select_related('group', 'group__course', 'group__teacher')
    
    # Build timetable structure
    days_of_week = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    day_names = [_('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'), _('Friday'), _('Saturday'), _('Sunday')]
    
    if view_type == 'day':
        day_times = group_times.filter(day=selected_day).order_by('time')
        timetable = {selected_day: list(day_times)}
        display_days = [(selected_day, day_names[days_of_week.index(selected_day)])]
    else:
        timetable = {day: [] for day in days_of_week}
        for gt in group_times.order_by('day', 'time'):
            timetable[gt.day].append(gt)
        display_days = list(zip(days_of_week, day_names))
    
    # Get unique courses and teachers for filter dropdowns
    student_courses = Course.objects.filter(study_groups__students=request.user).distinct()
    student_teachers = User.objects.filter(teaching_groups__students=request.user, role='teacher').distinct()
    
    context = {
        'timetable': timetable,
        'display_days': display_days,
        'view_type': view_type,
        'selected_day': selected_day,
        'courses': student_courses,
        'teachers': student_teachers,
        'selected_course': course_id,
        'selected_teacher': teacher_id,
        'user_role': 'student',
    }
    
    return render(request, 'subscriptions/timetable.html', context)


def admin_timetable(request):
    """Timetable view for admins - shows all groups with advanced filtering"""
    if not request.user.is_authenticated or (request.user.role != 'admin' and not request.user.is_superuser):
        return redirect('accounts:login')
    
    # Get filter parameters
    view_type = request.GET.get('view', 'week')
    course_id = request.GET.get('course', '')
    teacher_id = request.GET.get('teacher', '')
    selected_day = request.GET.get('day', 'MON')
    
    # Get all groups
    groups = StudyGroup.objects.all().select_related('course', 'course__level', 'course__track', 'teacher')
    
    # Filter by course if selected
    if course_id:
        groups = groups.filter(course_id=course_id)
    
    # Filter by teacher if selected
    if teacher_id:
        groups = groups.filter(teacher_id=teacher_id)
    
    # Get all group times for these groups
    group_times = GroupTime.objects.filter(group__in=groups).select_related('group', 'group__course', 'group__teacher')
    
    # Build timetable structure
    days_of_week = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    day_names = [_('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'), _('Friday'), _('Saturday'), _('Sunday')]
    
    if view_type == 'day':
        day_times = group_times.filter(day=selected_day).order_by('time')
        timetable = {selected_day: list(day_times)}
        display_days = [(selected_day, day_names[days_of_week.index(selected_day)])]
    else:
        timetable = {day: [] for day in days_of_week}
        for gt in group_times.order_by('day', 'time'):
            timetable[gt.day].append(gt)
        display_days = list(zip(days_of_week, day_names))
    
    # Get all courses and teachers for filter dropdowns
    all_courses = Course.objects.filter(study_groups__isnull=False).distinct()
    all_teachers = User.objects.filter(role='teacher', teaching_groups__isnull=False).distinct()
    
    context = {
        'timetable': timetable,
        'display_days': display_days,
        'view_type': view_type,
        'selected_day': selected_day,
        'courses': all_courses,
        'teachers': all_teachers,
        'selected_course': course_id,
        'selected_teacher': teacher_id,
        'user_role': 'admin',
    }
    
    return render(request, 'subscriptions/timetable.html', context)
