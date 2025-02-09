from django.db import models

from accounts.models import User
from courses.models import Session

# Create your models here.
class Exam(models.Model):
    name = models.CharField(max_length=100)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    duration = models.IntegerField()

    def __str__(self):
        return f"{self.name} - {self.session}"

class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return f"Question: {self.text[:50]}..."  # Display first 50 characters of the question

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['question'],
                condition=models.Q(is_correct=True),
                name='unique_correct_answer'
            )
        ]

    def save(self, *args, **kwargs):
        if self.is_correct:
            # Set all other options for this question to incorrect
            Option.objects.filter(question=self.question).update(is_correct=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Option: {self.text} ({'Correct' if self.is_correct else 'Incorrect'})"

class ExamResult(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.exam.name} - Score: {self.score}"