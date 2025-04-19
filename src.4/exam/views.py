# RestFrameWork lib
import random
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q, Case, When, BooleanField, Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch
import logging
# custom filters
from exam.filters import RelatedCourseFilterBackend
#celery
from celery import shared_task
# Models
from .serializers import QuestionSerializerWithoutCorrectAnswer, StudentExamResultSerializer
from .models import Answer, EssaySubmission, Exam, ExamModel, ExamModelQuestion, ExamQuestion, ExamType, Question, QuestionType, Result, ResultTrial, Submission
from course.models import Course
from subscription.models import CourseSubscription


class StartExam(APIView):
    permission_classes = [IsAuthenticated]

    def _has_active_subscription(self, student, course):
        return CourseSubscription.objects.filter(student=student, course=course, active=True).exists()

    def _get_exam_questions(self, exam, result):
        if exam.type == ExamType.RANDOM:
            return self._get_random_exam_questions(exam, result)
        else:
            return self._get_manual_exam_questions(exam)

    def _get_random_exam_questions(self, exam, result):
        exam_models = ExamModel.objects.filter(exam=exam, is_active=True)
        if not exam_models.exists():
            return Response(
                {"error": "No models available for this random exam"},
                status=status.HTTP_400_BAD_REQUEST
            )

        exam_model = exam_models.order_by('?').first()
        result.exam_model = exam_model
        result.save()

        questions = [mq.question for mq in exam_model.model_questions.filter(is_active=True)]
        random.shuffle(questions)  # Shuffle the questions
        return questions, exam_model

    def _get_manual_exam_questions(self, exam):
        questions = [eq.question for eq in ExamQuestion.objects.filter(exam=exam, question__is_active=True)]
        random.shuffle(questions)  # Shuffle the questions
        return questions, None

    def get(self, request, exam_id: int) -> Response:
        student = request.user.student
        exam = get_object_or_404(Exam, pk=exam_id)
        course = get_object_or_404(Course, id=exam.get_related_course())

        # Verify subscription (if needed)
        # if not self._has_active_subscription(student, course):
        #     return Response(
        #         {"error": "You do not have access permissions"},
        #         status=status.HTTP_401_UNAUTHORIZED,
        #     )

        # Ensure the exam is active
        exam_status = exam.status()
        if exam_status != "active":
            return Response(
                {"error": f"Exam is {exam_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch or create Result object
        result, created = Result.objects.get_or_create(
            student=student,
            exam=exam,
            defaults={"trial": 1}
        )

        # Only check if trials are finished if the result is being updated (not created)
        if not created and result.is_trials_finished:
            return Response(
                {"error": "You have finished your allowed trials for this exam"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Increment trials if this is not the first attempt
        if not created:
            result.trial += 1
            result.save()

        # Fetch or create the ResultTrial for the current trial
        result_trial, created = ResultTrial.objects.get_or_create(
            result=result,
            trial=result.trial,
            defaults={
                "exam_model": result.exam_model,
                "student_started_exam_at": timezone.now()
            }
        )

        # Fetch questions based on exam type
        questions, exam_model = self._get_exam_questions(exam, result)

        # Serialize questions
        question_data = [QuestionSerializerWithoutCorrectAnswer(q).data for q in questions]

        return Response(
            {
                "exam_id": exam.id,
                "exam_title": exam.title,
                "exam_time_limit": exam.time_limit,
                "questions": question_data,
                "exam_model": {
                    "id": exam_model.id,
                    "title": exam_model.title
                } if exam_model else None,
            },
            status=status.HTTP_200_OK
        )


class SubmitExam(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]  # Only need MultiPartParser for form-data

    def post(self, request, exam_id):
        student = request.user.student
        exam = get_object_or_404(Exam, pk=exam_id)
        submit_type = request.data.get("submit_type", "student_submit")

        # Get all unique question IDs from the request
        question_ids = set()
        for key in request.data.keys():
            if key.startswith('question_id_'):
                question_ids.add(int(key.split('_')[-1]))
            elif key == 'question_id':  # Handle case where it's not numbered
                question_ids.add(int(request.data[key]))

        # Get or create Result and ResultTrial
        result = get_object_or_404(Result, student=student, exam=exam)
        result_trial = result.trials.filter(trial=result.trial).first()
        
        if not result_trial:
            return Response(
                {"error": "No active trial found for this exam"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process each question
        for question_id in question_ids:
            question = get_object_or_404(Question, pk=question_id)
            
            if question.question_type == QuestionType.MCQ:
                # Process MCQ answer
                selected_answer_id = request.data.get(f"selected_answer_id_{question_id}")
                
                selected_answer = None
                if selected_answer_id:
                    selected_answer = get_object_or_404(
                        Answer, 
                        pk=selected_answer_id, 
                        question=question
                    )
                
                Submission.objects.update_or_create(
                    student=student,
                    exam=exam,
                    question=question,
                    result_trial=result_trial,
                    defaults={
                        "selected_answer": selected_answer,
                        "is_solved": bool(selected_answer_id),
                        "is_correct": selected_answer.is_correct if selected_answer else False
                    }
                )
            
            elif question.question_type == QuestionType.ESSAY:
                # Process Essay answer
                essay_answer_text = request.data.get(f"essay_answer_text_{question_id}", "")
                
                # Handle file upload
                essay_answer_file = request.FILES.get(f"essay_file_{question_id}")
                
                EssaySubmission.objects.update_or_create(
                    student=student,
                    exam=exam,
                    question=question,
                    result_trial=result_trial,
                    defaults={
                        "answer_text": essay_answer_text,
                        "answer_file": essay_answer_file,
                        "is_scored": False,
                        "score": None
                    }
                )

        # Calculate scores
        try:
            # Calculate MCQ score
            mcq_score = Submission.objects.filter(
                result_trial=result_trial,
                is_correct=True
            ).aggregate(total=Sum('question__points'))['total'] or 0

            # Calculate essay score (only scored essays)
            essay_score = EssaySubmission.objects.filter(
                result_trial=result_trial,
                is_scored=True
            ).aggregate(total=Sum('score'))['total'] or 0

            total_score = mcq_score + essay_score

            # Get exam total score
            if result.exam.type == ExamType.RANDOM and result_trial.exam_model:
                exam_score = ExamModelQuestion.objects.filter(
                    exam_model=result_trial.exam_model
                ).aggregate(total=Sum('question__points'))['total'] or 0
            else:
                exam_score = Question.objects.filter(
                    exam_questions__exam=result.exam, 
                    is_active=True
                ).aggregate(total=Sum('points'))['total'] or 0

            # Update trial and result
            result_trial.score = total_score
            result_trial.exam_score = exam_score
            result_trial.student_submitted_exam_at = timezone.now()
            result_trial.submit_type = submit_type
            result_trial.save()

            result.score = total_score
            result.save()

        except Exception as e:
            return Response(
                {"error": f"Error calculating score: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            "message": "Exam submitted successfully",
            "score": total_score,
            "is_succeeded": total_score >= (exam.passing_percent / 100) * result_trial.exam_score,
            "trial": result.trial
        }, status=status.HTTP_200_OK)


from django.db.models import Case, When, BooleanField, Q
from django.utils import timezone

class StudentExamResultsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentExamResultSerializer
    filter_backends = [DjangoFilterBackend, RelatedCourseFilterBackend]
    filterset_fields = ['exam__unit', 'exam__lesson', 'exam__related_to']

    def get_queryset(self):
        student = self.request.user.student

        # Fetch results for the student with prefetch_related for ResultTrial
        results = Result.objects.filter(student=student).select_related('exam').prefetch_related(
            Prefetch('trials', queryset=ResultTrial.objects.all())
        ).annotate(
            correct_count=Count(
                'exam__submissions',
                filter=Q(exam__submissions__student=student, exam__submissions__is_correct=True)
            ),
            incorrect_count=Count(
                'exam__submissions',
                filter=Q(exam__submissions__student=student, exam__submissions__is_correct=False)
            ),
            insolved_questions_count=Count(
                'exam__submissions',
                filter=Q(exam__submissions__student=student, exam__submissions__is_solved=False)
            ),
            total_questions=Count('exam__exam_questions'),
            is_allowed_to_show_result=Case(
                When(exam__allow_show_results_at__lte=timezone.now(), then=True),
                default=False,
                output_field=BooleanField()
            ),
            # Add annotation for allowing answers to be shown
            is_allowed_to_show_answers=Case(
                When(exam__allow_show_answers_at__isnull=True, then=False),
                When(exam__allow_show_answers_at__lte=timezone.now(), then=True),
                default=False,
                output_field=BooleanField()
            )
        )
        return results


class GetMyExamResult(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exam_id):
        student = request.user.student
        exam = get_object_or_404(Exam, pk=exam_id)

        # Ensure result visibility
        if timezone.now() < exam.allow_show_results_at:
            return Response(
                {"error": "You are not allowed to see this exam result yet"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Fetch the result and active trial
        result = get_object_or_404(Result, student=student, exam=exam)
        active_trial = result.active_trial

        # Fetch MCQ submissions
        mcq_submissions = Submission.objects.filter(
            student=student, exam=exam
        ).select_related('question', 'selected_answer', 'question__category')

        # Fetch Essay submissions
        essay_submissions = EssaySubmission.objects.filter(
            student=student, exam=exam
        ).select_related('question', 'question__category')

        student_answers = []
        unsolved_questions = []
        unscored_essay_questions = []  # New list for unscored essay questions

        # Process MCQ submissions
        for submission in mcq_submissions:
            question = submission.question
            selected_answer = submission.selected_answer

            answer_data = {
                "type": "mcq",
                "question_id": question.id if question else None,
                "question_category": question.category.title if question and question.category else None,
                "question_category_id": question.category.id if question and question.category else None,
                "question_text": question.text if question else None,
                "question_image": question.image.url if question and question.image else None,
                "selected_answer": selected_answer.text if selected_answer else None,
                "is_correct": submission.is_correct if submission.is_correct is not None else False,
                "is_solved": submission.is_solved if submission.is_solved is not None else False,
            }
            student_answers.append(answer_data)

            if not submission.is_solved:
                unsolved_questions.append(answer_data)

        # Process Essay submissions
        for submission in essay_submissions:
            question = submission.question
            answer_data = {
                "type": "essay",
                "question_id": question.id if question else None,
                "question_category": question.category.title if question and question.category else None,
                "question_category_id": question.category.id if question and question.category else None,
                "question_text": question.text if question else None,
                "question_image": question.image.url if question and question.image else None,
                "answer_text": submission.answer_text,
                "answer_file": submission.answer_file.url if submission.answer_file else None,
                "score": submission.score,
                "is_scored": submission.is_scored,
                "points": question.points,
                "max_points": question.points,
            }
            student_answers.append(answer_data)

            if not submission.is_scored:
                unscored_essay_questions.append(answer_data)  # Add to unscored_essay_questions

        # Fetch correct answers
        questions = Question.objects.filter(exam_questions__exam=exam).distinct()
        correct_answers = [
            {
                "question_id": question.id,
                "question_text": question.text,
                "question_image": question.image.url if question.image else None,
                "question_type": question.question_type,  # Include question type
                "correct_answers": [
                    {"text": answer.text, "image": answer.image.url if answer.image else None}
                    for answer in question.answers.filter(is_correct=True)
                ],
            }
            for question in questions
        ]

        # Response payload
        response_data = {
            "exam_id": exam.id,
            "exam_title": exam.title,
            "exam_description": exam.description,
            "exam_score": active_trial.exam_score if active_trial else 0,
            "student_score": active_trial.score if active_trial else 0,
            "is_succeeded": result.is_succeeded,
            "student_trials": result.trial,
            "is_trials_finished": result.is_trials_finished,
            "student_answers": student_answers,
            "unsolved_questions": unsolved_questions,
            "unscored_essay_questions": unscored_essay_questions,  # Include in response
            "correct_answers": correct_answers,
            "student_started_exam_at": active_trial.student_started_exam_at if active_trial else None,
            "student_submitted_exam_at": active_trial.student_submitted_exam_at if active_trial else None,
            "submit_type": active_trial.submit_type if active_trial else None,  # Add submit_type
        }

        return Response(response_data, status=status.HTTP_200_OK)




