from django.urls import path
from . import views
urlpatterns = [
    #*============================>Course<============================#*
    path("pay-with-center-code", views.PayWithCenterCode.as_view(), name="pay-with-center-code"),
    path("promo-code-discount", views.GetPromoCodeDiscount.as_view(), name="GetPromoCodeDiscount"),
    path("free-course", views.FreeCourse.as_view(), name="FreeCourse"),
    #*============================>Fawry<============================#*
    path("pay-with-fawry", views.PayWithFawry.as_view(), name="pay-with-fawry"),
    path("fawry-call-back/<str:api_key>", views.FawryCallBack.as_view(), name="fawry-call-back"),
    #*============================>Course Collection<============================#*
    path("pay-course-collection-with-code", views.PayCourseCollectionWithCenterCode.as_view(), name="PayCourseCollectionWithCenterCode"),
    #*============================>Lesson<============================#*
    path("pay-lesson-with-code", views.PayLessonWithCenterCode.as_view(), name="PayLessonWithCenterCode"),
    path("pay-any-lesson-with-code", views.PayAnyLessonWithCenterCode.as_view(), name="PayAnyLessonWithCenterCode"),
]