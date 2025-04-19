from django.shortcuts import get_object_or_404
from analysis.models import CoursePermission
from course.models import Lesson
from exam.models import Exam, Result
from student.models import Student
from subscription.models import CourseSubscription
from view.models import LessonView

# Create your views here.

def check_course_subscription(student, course):
    return CourseSubscription.objects.filter(student=student, course=course, active=True).exists()

def check_lesson_watch(student, previous_lesson):
    return LessonView.objects.filter(student=student, lesson=previous_lesson, counter__gt=0).exists()

def check_exam_take(student, exam):
    return Result.objects.filter(student=student, exam=exam).exists()

def check_exam_pass(student, exam):
    result = Result.objects.filter(student=student, exam=exam).first()
    return result.is_succeeded if result else False

def get_previous_lesson(lesson):
    return Lesson.objects.filter(unit=lesson.unit, order__lt=lesson.order).last()

def get_exam_for_lesson(lesson):
    return Exam.objects.filter(lesson=lesson).first()

def has_permission_to_access_lesson(student_id, lesson_id):
    student = get_object_or_404(Student, id=student_id)
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.unit.course

    # Check if the student is subscribed to the course
    if not check_course_subscription(student, course):
        return False, "You are not subscribed to this course."

    # Get the course permission settings
    course_permission = get_object_or_404(CoursePermission, course=course)
    open_permission = course_permission.open_permission

    # Check the permission type
    if open_permission == 'no_permission':
        return True, "Permission granted."

    previous_lesson = get_previous_lesson(lesson)
    if not previous_lesson:
        return True, "Permission granted."

    if open_permission == 'lessonwatch':
        if not check_lesson_watch(student, previous_lesson):
            return False, "You must watch the previous lesson video first."

    elif open_permission == 'exam_take':
        exam = get_exam_for_lesson(previous_lesson)
        if exam and not check_exam_take(student, exam):
            return False, "You must take the exam for the previous lesson first."

    elif open_permission == 'exam_pass':
        exam = get_exam_for_lesson(previous_lesson)
        if exam and not check_exam_pass(student, exam):
            return False, "You must pass the exam for the previous lesson first."

    elif open_permission == 'all':
        exam = get_exam_for_lesson(previous_lesson)
        if exam and not check_exam_pass(student, exam):
            return False, "You must pass the exam for the previous lesson first."
        if not check_lesson_watch(student, previous_lesson):
            return False, "You must watch the previous lesson video first."

    return True, "Permission granted."






