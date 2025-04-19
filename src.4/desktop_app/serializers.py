from rest_framework import serializers
from subscription.models import *
from course.models import *
from view.models import LessonView
from exam.models import Exam,Result
from .models import *
# Students
class StudentListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    student_course_count = serializers.SerializerMethodField()
    year_name = serializers.CharField(source='year.name')
    type_education_name = serializers.CharField(source='type_education.name')

    class Meta:
        model = Student
        fields = [
            'id',
            'name',
            'username',
            'code',
            'year_name',
            'type_education_name',
            'parent_phone',
            'points',
            'created',
            'year',
            'student_course_count',
        ]
    
    def get_student_course_count(self,obj):
        return obj.coursesubscription_set.filter(active=True).count()


# Course
class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'id',
            'name',
            'description',
        ]   

class LessonListSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='unit.course.name')
    course_id = serializers.IntegerField(source='unit.course.id')
    class Meta:
        model = Lesson
        fields = [
            'id',
            'name',
            'description',
            'course_id',
            'course_name',
        ]

# lesson views
class LessonViewSerializer(serializers.ModelSerializer):
    lesson_id = serializers.IntegerField(source='lesson.id')
    video_duration = serializers.IntegerField(source='lesson.video_duration')
    
    lesson_views_quantity = serializers.IntegerField(source='counter')
    last_duration = serializers.IntegerField(source='total_watch_time')
    session_duration = serializers.SerializerMethodField()
    student_code = serializers.CharField(source='student.code')
    student_name = serializers.CharField(source='student.name')
    username = serializers.CharField(source='student.user.username')
    class Meta:
        model = LessonView
        fields = [
            'lesson_id',
            'lesson_views_quantity',
            'last_duration',
            'video_duration',
            'session_duration',
            'student_code',
            'student_name',
            'username',
        ]

    def get_session_duration(self, obj):
        # Check if 'obj' is an actual LessonView instance
        if isinstance(obj, LessonView):
            duration = 0
            for session in obj.viewsession_set.all():
                duration += session.watch_time
            return duration
        else:
            # Return 0 if it's a manual dictionary (student without a LessonView)
            return 0



# Exam
class ExamSerializer(serializers.ModelSerializer):
    course_name = serializers.SerializerMethodField()
    course_id = serializers.SerializerMethodField()
    question_quantity = serializers.SerializerMethodField()
    class Meta:
        model = Exam
        fields = [
            'id',
            'title',
            'question_quantity',
            'course_id',
            'course_name',
        ]

    def get_question_quantity(self,obj):
        return obj.calculate_number_of_questions()
    
    def get_course_id(self,obj):
        if obj.related_to == "UNIT":
            return obj.unit.course.id
        elif obj.related_to == "LESSON":
            return obj.lesson.unit.course.id
        else:
            return None

    def get_course_name(self,obj):
        if obj.related_to == "UNIT":
            return obj.unit.course.name
        elif obj.related_to == "LESSON":
            return obj.lesson.unit.course.name
        else:
            return None
    


class ExamResultSerializer(serializers.ModelSerializer):
    exam_id = serializers.IntegerField(source='exam.id', read_only=True)
    student_code = serializers.CharField(source='student.code')
    student_name = serializers.CharField(source='student.name')
    username = serializers.CharField(source='student.user.username')
    student_started_exam_at = serializers.SerializerMethodField()  # Fetch from ResultTrial
    student_submitted_exam_at = serializers.SerializerMethodField()  # Fetch from ResultTrial
    student_score = serializers.SerializerMethodField()
    class Meta:
        model = Result
        fields = [
            'exam_id',
            'student_code',
            'student_name',
            'username',
            'student_score',
            'student_started_exam_at',
            'student_submitted_exam_at',
        ]
    
    def get_student_started_exam_at(self, obj):
        """Fetch the start time from the active trial."""
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.student_started_exam_at
        return None

    def get_student_submitted_exam_at(self, obj):
        """Fetch the submission time from the active trial."""
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.student_submitted_exam_at
        return None

    def get_student_score(self, obj):
        """Fetch the student's score from the active trial."""
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.score
        return 0


# Attendance
class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Center
        fields = [
            'id',
            'name',
        ]

class LectureSerializer(serializers.ModelSerializer):
    center_name = serializers.CharField(source='center.name' , read_only=True)
    class Meta:
        model = Lecture
        fields = [
            'id',
            'name',
            'center',
            'center_name',
        ]

class AttendanceSerializer(serializers.ModelSerializer):
    student_code = serializers.CharField(source='student.code',read_only=True)
    student_name = serializers.CharField(source='student.name',read_only=True)
    lecture_name = serializers.CharField(source='lecture.name',read_only=True)
    lecture_center_name = serializers.CharField(source='lecture.center.name',read_only=True)
    class Meta:
        model = Attendance
        fields = [
            'id',
            'student_code',
            'student_name',
            'lecture',
            'lecture_name',
            'lecture_center_name',
            'status',
            'date'
        ]