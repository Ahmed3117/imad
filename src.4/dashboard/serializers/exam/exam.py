from rest_framework import serializers
from django.utils import timezone
from course.models import Course, Lesson, Unit
from dashboard.serializers.student.student import StudentSerializer
from exam.models import Answer, DifficultyLevel, Exam, ExamModel, ExamModelQuestion, ExamQuestion, ExamType, Question, QuestionCategory, QuestionType, RandomExamBank, RelatedToChoices, Result, EssaySubmission, ResultTrial, Submission
from student.models import Student

class ExamSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    related_year = serializers.SerializerMethodField()
    related_course = serializers.SerializerMethodField()
    related_unit = serializers.SerializerMethodField()
    related_unit_name = serializers.SerializerMethodField()
    related_lesson_name = serializers.SerializerMethodField()
    related_course_name = serializers.SerializerMethodField()
    related_year_name = serializers.SerializerMethodField()
    calculated_score = serializers.SerializerMethodField()
    calculated_number_of_questions = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            "id", "title", "description",
            "related_to", "related_course", "related_course_name",
            "related_year", "related_year_name",
            "unit", "related_unit", "related_unit_name",
            "lesson", "related_lesson_name",
            "type", "number_of_questions", "time_limit",
            "number_of_allowed_trials", "easy_questions_count",
            "medium_questions_count", "hard_questions_count",
            "show_answers_after_finish", "order", "is_active",
            "start", "end", "allow_show_results_at","allow_show_answers_at", "created",
            "passing_percent", "status", "calculated_score","calculated_number_of_questions",
            'is_depends',
        ]

        read_only_fields = ["id", "created", "status", "related_year", "related_course", "related_unit",
                            "related_unit_name", "related_lesson_name", "related_course_name","related_year_name","calculated_score","calculated_number_of_questions"]

    def get_status(self, obj):
        return obj.status()

    def get_related_year(self, obj):
        return obj.get_related_year()
    
    def get_related_year_name(self, obj):
        if obj.unit:
            return obj.unit.course.year.name
        elif obj.lesson:
            return obj.lesson.unit.course.year.name
        return None

    def get_related_course(self, obj):
        if obj.unit:
            return obj.unit.course.id
        elif obj.lesson:
            return obj.lesson.unit.course.id
        return None

    def get_related_unit(self, obj):
        if obj.unit:
            return obj.unit.id
        elif obj.lesson:
            return obj.lesson.unit.id
        return None

    def get_related_unit_name(self, obj):
        if obj.unit:
            return obj.unit.name
        return None

    def get_related_lesson_name(self, obj):
        if obj.lesson:
            return obj.lesson.name
        return None

    def get_related_course_name(self, obj):
        if obj.unit:
            return obj.unit.course.name
        elif obj.lesson:
            return obj.lesson.unit.course.name
        return None
    
    def get_calculated_score(self, obj):
        """
        Return the dynamically calculated score for the exam.
        """
        return obj.calculate_score()

    def get_calculated_number_of_questions(self, obj):
        return obj.calculate_number_of_questions()

    def validate(self, data):
        total_count = (
            data.get("easy_questions_count", 0) +
            data.get("medium_questions_count", 0) +
            data.get("hard_questions_count", 0)
        )
        if total_count > data.get("number_of_questions", 0):
            raise serializers.ValidationError("The total count of questions cannot exceed the number of questions.")

        related_to = data.get("related_to")
        unit = data.get("unit")
        lesson = data.get("lesson")

        if related_to == "UNIT" and not unit:
            raise serializers.ValidationError("Unit is required when related_to is 'UNIT'.")
        if related_to == "LESSON" and not lesson:
            raise serializers.ValidationError("Lesson is required when related_to is 'LESSON'.")
        if related_to == "UNIT" and lesson:
            raise serializers.ValidationError("it should be related to a unit but you selected a lesson.")
        if related_to == "LESSON" and unit:
            raise serializers.ValidationError("it should be related to a lesson but you selected a unit.")
        if related_to != "UNIT" and related_to != "LESSON":
            raise serializers.ValidationError("Exam must be related to either a unit or a lesson.")

        return data




class QuestionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionCategory
        fields = ['id', 'title', 'year']

class AnswerSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Answer
        fields = ['id', 'text', 'image', 'is_correct', 'question']
        read_only_fields = ['id']
        extra_kwargs = {
            'question': {'required': False},
            'is_correct': {'required': False, 'default': False}
        }

class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, required=False)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Question
        fields = [
            'id',
            'text',
            'image',
            'points',
            'difficulty',
            'category',
            'lesson',
            'unit',
            'is_active',
            'answers',
            'question_type',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        # Extract nested answers data
        answers_data = validated_data.pop('answers', [])
        
        # Create the Question object
        question = Question.objects.create(**validated_data)
        
        # Create Answer objects if provided
        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)
        
        return question
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['answers'] = AnswerSerializer(instance.answers.all(), many=True).data
        return representation


class EssaySubmissionSerializer(serializers.ModelSerializer):
    answer_file_url = serializers.SerializerMethodField()

    class Meta:
        model = EssaySubmission
        fields = ['id', 'student', 'exam', 'question', 'answer_text', 'answer_file', 'answer_file_url', 'score', 'is_scored', 'created', 'result_trial']
        extra_kwargs = {
            'answer_file': {'write_only': True}  # Don't include in response, use answer_file_url instead
        }

    def get_answer_file_url(self, obj):
        if obj.answer_file:
            return self.context['request'].build_absolute_uri(obj.answer_file.url)
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['student'] = instance.student.name
        representation['exam'] = instance.exam.title
        representation['question'] = instance.question.text
        return representation

class RandomExamBankSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = RandomExamBank
        fields = ['exam', 'questions']

class ExamModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamModel
        fields = '__all__'

    def validate_exam(self, value):
        if value.type != ExamType.RANDOM:
            raise serializers.ValidationError("The exam type must be 'RANDOM'.")
        return value

class ResultSerializer(serializers.ModelSerializer):
    result_id = serializers.IntegerField(source='id')
    exam_id = serializers.IntegerField(source='exam.id', read_only=True)
    # exam_title = serializers.CharField(source='exam.title', read_only=True)
    # exam_description = serializers.CharField(source='exam.description', read_only=True)
    # exam_related_to = serializers.CharField(source='exam.related_to', read_only=True)
    # exam_unit = serializers.IntegerField(source='exam.unit.id', allow_null=True, read_only=True)
    # exam_lesson = serializers.IntegerField(source='exam.lesson.id', allow_null=True, read_only=True)
    # exam_course = serializers.SerializerMethodField()
    exam_score = serializers.SerializerMethodField()
    student_score = serializers.SerializerMethodField()
    number_of_allowed_trials = serializers.IntegerField(source='exam.number_of_allowed_trials', read_only=True)
    trials = serializers.IntegerField(source='trial')
    # trials_finished = serializers.BooleanField(source='is_trials_finished', read_only=True)
    # passing_percent = serializers.IntegerField(source='exam.passing_percent', read_only=True)
    # is_succeeded = serializers.SerializerMethodField()
    correct_questions_count = serializers.SerializerMethodField()
    incorrect_questions_count = serializers.SerializerMethodField()
    insolved_questions_count = serializers.SerializerMethodField()
    # number_of_questions = serializers.SerializerMethodField()
    allowed_to_show_result = serializers.SerializerMethodField()
    # added_at = serializers.DateTimeField(source='added', read_only=True)
    # start = serializers.DateTimeField(source='exam.start', read_only=True)
    # end = serializers.DateTimeField(source='exam.end', read_only=True)
    student_id = serializers.IntegerField(source='student.id', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_phone = serializers.CharField(source='student.user.username', read_only=True)
    parent_phone = serializers.CharField(source='student.parent_phone', read_only=True)
    jwt_token = serializers.CharField(source='student.jwt_token', read_only=True)
    student_started_exam_at = serializers.SerializerMethodField()  # Fetch from ResultTrial
    student_submitted_exam_at = serializers.SerializerMethodField()  # Fetch from ResultTrial
    submit_type = serializers.SerializerMethodField()
    class Meta:
        model = Result
        fields = [
            'result_id',
            'exam_id',
            # 'exam_title',
            # 'exam_description',
            # 'exam_related_to',
            # 'exam_unit',
            # 'exam_lesson',
            # 'exam_course',
            'exam_score',
            'student_score',
            'trials',
            # 'trials_finished',
            'number_of_allowed_trials',
            # 'is_succeeded',
            'correct_questions_count',
            'incorrect_questions_count',
            'insolved_questions_count',
            # 'number_of_questions',
            'allowed_to_show_result',
            # 'passing_percent',
            # 'added_at',
            # 'start',
            # 'end',
            
            'student_id',
            'student_name',
            'student_phone',
            'parent_phone',
            'jwt_token',
            'student_started_exam_at',
            'student_submitted_exam_at',
            'submit_type',
        ]

    # def get_exam_course(self, obj):
    #     """Retrieve related course from the Exam model."""
    #     return obj.exam.get_related_course()

    def get_exam_score(self, obj):
        """Fetch the exam_score from the active trial."""
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.exam_score
        return 0

    def get_student_score(self, obj):
        """Fetch the student's score from the active trial."""
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.score
        return 0

    def get_correct_questions_count(self, obj):
        """Count correct submissions for the exam."""
        return Submission.objects.filter(
            student=obj.student, exam=obj.exam, is_correct=True
        ).count()

    def get_incorrect_questions_count(self, obj):
        """Count incorrect submissions for the exam."""
        return Submission.objects.filter(
            student=obj.student, exam=obj.exam, is_correct=False
        ).count()

    def get_insolved_questions_count(self, obj):
        """Count unsolved submissions for the exam."""
        return Submission.objects.filter(
            student=obj.student, exam=obj.exam, is_solved=False
        ).count()

    # def get_number_of_questions(self, obj):
    #     """Get the total number of questions in the exam."""
    #     if obj.exam.type == ExamType.RANDOM and obj.exam_model:
    #         return ExamModelQuestion.objects.filter(exam_model=obj.exam_model).count()
    #     return Question.objects.filter(exam_questions__exam=obj.exam, is_active=True).count()

    def get_allowed_to_show_result(self, obj):
        """Check if the result can be shown."""
        return obj.exam.allow_show_results_at <= timezone.now()

    # def get_is_succeeded(self, obj):
    #     """Determine if the student passed the exam."""
    #     active_trial = obj.active_trial
    #     if active_trial:
    #         return active_trial.score >= (obj.exam.passing_percent / 100) * active_trial.exam_score
    #     return False

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



class ResultTrialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultTrial
        fields = [
            'trial',
            'score',
            'submit_type',
            'student_started_exam_at',
            'student_submitted_exam_at'
        ]
        
class BriefedResultSerializer(serializers.ModelSerializer):
    examscore = serializers.SerializerMethodField()
    student_score = serializers.SerializerMethodField()
    issucceeded = serializers.BooleanField(source='is_succeeded')
    exam_title = serializers.SerializerMethodField()
    trials = serializers.SerializerMethodField()

    class Meta:
        model = Result
        fields = [
            'id',
            'exam',
            'exam_title',
            'examscore',
            'student_score',
            'trial',
            'is_trials_finished',
            'issucceeded',
            'added',
            'trials'
        ]

    def get_exam_title(self, obj):
        return obj.exam.title if obj.exam else None

    def get_examscore(self, obj):
        # Fetch exam_score from the active trial
        active_trial = obj.active_trial
        return active_trial.exam_score if active_trial else 0

    def get_student_score(self, obj):
        # Fetch student_score from the active trial
        active_trial = obj.active_trial
        return active_trial.score if active_trial else 0

    def get_trials(self, obj):
        trials = obj.trials.all()
        return ResultTrialSerializer(trials, many=True).data


class CombinedStudentResultSerializer(serializers.ModelSerializer):
    result = BriefedResultSerializer(source='result_set', many=True, read_only=True)
    student = StudentSerializer(source='*')

    class Meta:
        model = Student
        fields = [
            'student',
            'result'
        ]


class CopyExamSerializer(serializers.Serializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all(), required=False, allow_null=True)
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all(), required=False, allow_null=True)
    related_to = serializers.ChoiceField(choices=RelatedToChoices.choices)






