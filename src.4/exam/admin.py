from django.contrib import admin

from exam.models import Answer, EssaySubmission, Exam, ExamQuestion, Question, QuestionCategory, Result, ResultTrial, Submission

# Register your models here.

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id','text', 'points', 'difficulty', 'category', 'lesson', 'unit', 'is_active', 'created')
    list_editable = ('is_active',)

admin.site.register(Exam)
admin.site.register(ExamQuestion)
admin.site.register(QuestionCategory)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)
admin.site.register(Submission)
admin.site.register(EssaySubmission)
admin.site.register(Result)
admin.site.register(ResultTrial)