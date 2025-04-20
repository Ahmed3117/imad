from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, Q
from assignment.models import Assignment, StudentAnswer
from subscriptions.models import LectureNote, StudyGroup
import json


class StudyGroupReportView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = StudyGroup
    template_name = 'subscriptions/studygroup_report.html'
    context_object_name = 'group'

    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()

        # Get all lectures with their notes and statistics
        lectures = group.lectures.annotate(
            note_count=Count('notes'),
            avg_rating=Avg('notes__rating', filter=Q(notes__rating__isnull=False)),
            teacher_status=Count('notes', filter=Q(notes__user__role='teacher'))
        ).prefetch_related('notes', 'notes__user').order_by('-live_link_date')

        # Calculate overall statistics
        total_lectures = lectures.count()
        finished_lectures = lectures.filter(is_finished=True).count()
        avg_group_rating = lectures.aggregate(
            overall_avg=Avg('avg_rating'))['overall_avg'] or 0

        # Get teacher notes separately
        teacher_notes = LectureNote.objects.filter(
            lecture__group=group,
            user__role='teacher'
        ).select_related('lecture', 'user')

        # Assignment data report
        assignments = Assignment.objects.filter(lecture__group=group)
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

        # Grade distribution for chart (example buckets: 90-100, 80-89, ..., <50)
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

        context.update({
            'lectures': lectures,
            'teacher_notes': teacher_notes,
            'total_lectures': total_lectures,
            'finished_lectures': finished_lectures,
            'avg_group_rating': avg_group_rating,
            'assignments': assignments,
            'report_data': report_data,
            'overall_average': overall_average,
            'grade_distribution': json.dumps(grade_distribution),
            'completion_status': json.dumps(completion_status),
        })

        return context








