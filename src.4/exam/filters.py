from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from exam.models import Result

class RelatedCourseFilterBackend(DjangoFilterBackend):
    def filter_queryset(self, request, queryset, view):
        course_id = request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(exam__unit__course__id=course_id)
        return queryset
