from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, Q, Max
from django.utils import timezone
from assignment.models import Assignment, StudentAnswer
from subscriptions.models import LectureNote, StudyGroup
from collections import defaultdict
import json



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

