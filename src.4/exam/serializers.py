from rest_framework import serializers
from .models import Answer, Exam, ExamModelQuestion, ExamType, Question, Result, Submission
from django.utils import timezone

class ExamSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    related_name = serializers.CharField(source='get_related_name', read_only=True)
    number_of_questions = serializers.SerializerMethodField()
    class Meta:
        model = Exam
        fields = [
            'id',
            'title',
            'description',
            'number_of_questions',
            'time_limit',
            'score',
            'passing_percent',
            'start',
            'end',
            'time_limit',
            'status',
            'related_name',
            'order',
            'is_active',
            'show_answers_after_finish',
            'is_depends',
            'number_of_questions',
        ]
        
    def get_number_of_questions(self,obj):
        if obj.type == ExamType.RANDOM:
            return 'not_calculatable'
        elif obj.type in [ExamType.MANUAL, ExamType.BANK]:
            return obj.exam_questions.count()
        else:
            return 0



class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'image']

class QuestionSerializerWithoutCorrectAnswer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ['id', 'text', 'image', 'points', 'difficulty', 'category', 'lesson', 'unit', 'is_active', 'answers', 'question_type']


class StudentExamResultSerializer(serializers.ModelSerializer):
    result_id = serializers.IntegerField(source='id')
    exam_id = serializers.IntegerField(source='exam.id', read_only=True)
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    exam_description = serializers.CharField(source='exam.description', read_only=True)
    exam_related_to = serializers.CharField(source='exam.related_to', read_only=True)
    exam_unit = serializers.IntegerField(source='exam.unit.id', allow_null=True, read_only=True)
    exam_lesson = serializers.IntegerField(source='exam.lesson.id', allow_null=True, read_only=True)
    exam_course = serializers.SerializerMethodField()
    exam_score = serializers.SerializerMethodField()
    student_score = serializers.SerializerMethodField()
    number_of_allowed_trials = serializers.IntegerField(source='exam.number_of_allowed_trials', read_only=True)
    trials = serializers.IntegerField(source='trial')
    trials_finished = serializers.BooleanField(source='is_trials_finished', read_only=True)
    passing_percent = serializers.IntegerField(source='exam.passing_percent', read_only=True)
    is_succeeded = serializers.SerializerMethodField()
    correct_questions_count = serializers.SerializerMethodField()
    incorrect_questions_count = serializers.SerializerMethodField()
    insolved_questions_count = serializers.SerializerMethodField()
    number_of_questions = serializers.SerializerMethodField()
    allowed_to_show_result = serializers.SerializerMethodField()
    allowed_to_show_answers = serializers.BooleanField(source='is_allowed_to_show_answers', read_only=True)  # New field
    added_at = serializers.DateTimeField(source='added', read_only=True)
    start = serializers.DateTimeField(source='exam.start', read_only=True)
    end = serializers.DateTimeField(source='exam.end', read_only=True)
    student_id = serializers.IntegerField(source='student.id', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_phone = serializers.CharField(source='student.user.username', read_only=True)
    parent_phone = serializers.CharField(source='student.parent_phone', read_only=True)
    jwt_token = serializers.CharField(source='student.jwt_token', read_only=True)
    student_started_exam_at = serializers.SerializerMethodField() 
    student_submitted_exam_at = serializers.SerializerMethodField() 
    submit_type = serializers.SerializerMethodField()  

    class Meta:
        model = Result
        fields = [
            'result_id',
            'exam_id',
            'exam_title',
            'exam_description',
            'exam_related_to',
            'exam_unit',
            'exam_lesson',
            'exam_course',
            'exam_score',
            'student_score',
            'trials',
            'trials_finished',
            'number_of_allowed_trials',
            'is_succeeded',
            'correct_questions_count',
            'incorrect_questions_count',
            'insolved_questions_count',
            'number_of_questions',
            'allowed_to_show_result',
            'allowed_to_show_answers',  # New field
            'passing_percent',
            'added_at',
            'start',
            'end',
            'student_id',
            'student_name',
            'student_phone',
            'parent_phone',
            'jwt_token',
            'student_started_exam_at',
            'student_submitted_exam_at',
            'submit_type',
        ]

    def get_exam_course(self, obj):
        """Retrieve related course from the Exam model."""
        return obj.exam.get_related_course()

    def get_exam_score(self, obj):
        """Fetch the exam_score from the active trial."""
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.exam_score
        return 0

    def get_student_score(self, obj):
        """Fetch the student's score from the active trial."""
        if not obj.is_allowed_to_show_result:
            return "not_allowed_yet"
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.score
        return 0

    def get_correct_questions_count(self, obj):
        """Count correct submissions for the exam."""
        if not obj.is_allowed_to_show_result:
            return "not_allowed_yet"
        return Submission.objects.filter(
            student=obj.student, exam=obj.exam, is_correct=True
        ).count()

    def get_incorrect_questions_count(self, obj):
        """Count incorrect submissions for the exam."""
        if not obj.is_allowed_to_show_result:
            return "not_allowed_yet"
        return Submission.objects.filter(
            student=obj.student, exam=obj.exam, is_correct=False
        ).count()

    def get_insolved_questions_count(self, obj):
        """Count unsolved submissions for the exam."""
        if not obj.is_allowed_to_show_result:
            return "not_allowed_yet"
        return Submission.objects.filter(
            student=obj.student, exam=obj.exam, is_solved=False
        ).count()

    def get_number_of_questions(self, obj):
        """Get the total number of questions in the exam."""
        if obj.exam.type == ExamType.RANDOM and obj.exam_model:
            return ExamModelQuestion.objects.filter(exam_model=obj.exam_model).count()
        return Question.objects.filter(exam_questions__exam=obj.exam, is_active=True).count()

    def get_allowed_to_show_result(self, obj):
        """Check if the result can be shown."""
        return obj.is_allowed_to_show_result

    def get_is_succeeded(self, obj):
        """Determine if the student passed the exam."""
        if not obj.is_allowed_to_show_result:
            return "not_allowed_yet"
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.score >= (obj.exam.passing_percent / 100) * active_trial.exam_score
        return False

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

    def get_submit_type(self, obj):
        """Fetch the submit_type from the active trial."""
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.submit_type
        return None



