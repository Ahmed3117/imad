from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, Q

from subscriptions.models import LectureNote, StudyGroup

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
            teacher_status=Count('notes__lecture_status', filter=Q(notes__user__role='teacher'))
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
        
        context.update({
            'lectures': lectures,
            'teacher_notes': teacher_notes,
            'total_lectures': total_lectures,
            'finished_lectures': finished_lectures,
            'avg_group_rating': avg_group_rating,
        })
        
        return context