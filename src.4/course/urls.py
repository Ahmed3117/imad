from django.urls import path
from . import views

urlpatterns = [
    path("course-categories-list", views.CourseCategoryListView.as_view(), name="CourseCategoryListView-users"),
    path("course-list", views.CourseListView.as_view(), name="course_list_view"),
    path("course-details/<int:id>", views.CourseDetailView.as_view(), name="Course_detail_view"),
    path("unit-list/<int:course_id>", views.UnitListView.as_view(), name="unit_list_view"),
    path("unit-content/<int:unit_id>", views.UnitContent.as_view(), name="unit_content"),
    path("course-collection/list", views.CourseCollectionListView.as_view(), name="course_collection_list_view"),

]
