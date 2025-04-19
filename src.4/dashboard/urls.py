from django.urls import path
from . import views

urlpatterns = [
    #^ < ==============================[ <- Admins -> ]============================== > ^#
    path("admin/create-admin", views.CreateAdminView.as_view(), name="CreateAdminView"),
    path("admin/list", views.AdminListView.as_view(), name="AdminListView"),
    #^ < ==============================[ <- Student -> ]============================== > ^#
    path("student/list", views.StudentsListView.as_view(), name="StudentsListView"),
    path("student/update/<int:id>", views.StudentUpdateView.as_view(), name="StudentUpdateView"),
    path("student/details/<int:id>", views.StudentDetailView.as_view(), name="StudentDetailView"),
    path("student/rest-password/<str:username>", views.UserRestPasswordView.as_view(), name="UserRestPasswordView"),
    path("student/delete/<str:username>", views.UserDeleteView.as_view(), name="UserDeleteView"),
    path("student/change-center-status/", views.ChangeStudentByCode.as_view(), name="ChangeStudentByCode"),
    path("student/sign-code/", views.StudentSignCodeView.as_view(), name="ChangeStudentByCode"),
    #^ < ==============================[ <- Analysis -> ]============================== > ^#
    path("analysis/student-points", views.StudentPointListView.as_view(), name="StudentPointListCreateView"),
    path("analysis/lessons", views.AllLessonListView.as_view(), name="AllLessonListView"),
    path("analysis/chart-data-invoice", views.ChartDataInvoiceAPIView.as_view(), name="ChartDataInvoiceAPIView"),
    path("analysis/students-per-government", views.StudentsPerGovernmentView.as_view(), name="students-per-government"),
    path("analysis/students-over-time", views.StudentsOverTimeView.as_view(), name="students-over-time"),
    path("analysis/course-progress/<int:course_id>/", views.CourseProgressView.as_view(), name="course-progress"),
    #^ < ==============================[ <- CourseCategory -> ]============================== > ^#
    path('course-category/list', views.CourseCategoryListView.as_view(), name='course-category-list'),
    path('course-category/create', views.CourseCategoryCreateView.as_view(), name='course-category-create'),
    path('course-category/update/<int:id>', views.CourseCategoryUpdateView.as_view(), name='course-category-update'),
    path('course-category/delete/<int:id>', views.CourseCategoryDeleteView.as_view(), name='course-category-delete'),
    #^ < ==============================[ <- Course Collection -> ]============================== > ^#
    path('course-collections/list', views.CourseCollectionListView.as_view(), name='course-collection-list'),
    path('course-collections/create', views.CourseCollectionCreateView.as_view(), name='course-collection-create'),
    path('course-collections/update/<int:pk>', views.CourseCollectionUpdateView.as_view(), name='course-collection-update'),
    path('course-collections/delete/<int:pk>', views.CourseCollectionDeleteView.as_view(), name='course-collection-delete'),
    #^ < ==============================[ <- Course -> ]============================== > ^#
    path('course/list', views.CourseListView.as_view(), name='course-list'),
    path('course/create', views.CourseCreateView.as_view(), name='course-create'),
    path('course/details/<int:id>', views.CourseDetailView.as_view(), name='course-details'),
    path('courses/update/<int:id>', views.CourseUpdateView.as_view(), name='update-course'),
    path('courses/delete/<int:id>', views.CourseDeleteView.as_view(), name='delete-course'),
    
    #^ < ==============================[ <- Unit -> ]============================== > ^#
    path('unit/list/<int:course_id>', views.UnitListView.as_view(), name='unit-list'),
    path('unit/create/<int:course_id>', views.UnitCreateView.as_view(), name='unit-create'),
    path('unit/content/<int:unit_id>', views.UnitContentView.as_view(), name='unit-create'),
    path('unit/update/<int:unit_id>', views.UnitUpdateView.as_view(), name='unit-update'),
    path('unit/delete/<int:unit_id>', views.UnitDeleteView.as_view(), name='unit-delete'),
    
    #^ < ==============================[ <- Lesson -> ]============================== > ^#
    path('lesson/list/<int:unit_id>', views.LessonListView.as_view(), name='lesson-list'),
    path('lesson/create/<int:unit_id>', views.LessonCreateView.as_view(), name='lesson-create'),
    path('lesson/update/<int:lesson_id>', views.LessonUpdateView.as_view(), name='lesson-update'),
    path('lesson/delete/<int:lesson_id>', views.LessonDeleteView.as_view(), name='lesson-delete'),
    #^ < ==============================[ <- Lesson File -> ]============================== > ^#
    path('lesson-file/list/<int:lesson_id>', views.LessonFileListView.as_view(), name='lesson-file-list'),
    path('lesson-file/create/<int:lesson_id>', views.LessonFileCreateView.as_view(), name='lesson-file-create'),
    path('lesson-file/update/<int:file_id>', views.LessonFileUpdateView.as_view(), name='lesson-file-update'),
    path('lesson-file/delete/<int:file_id>', views.LessonFileDeleteView.as_view(), name='lesson-file-delete'),
    
    #^ < ==============================[ <- Files -> ]============================== > ^#
    path('file/list/<int:unit_id>', views.FileListView.as_view(), name='file-list'),
    path('file/create/<int:unit_id>', views.FileCreateView.as_view(), name='file-create'),
    path('file/update/<int:file_id>', views.FileUpdateView.as_view(), name='file-update'),
    path('file/delete/<int:file_id>', views.FileDeleteView.as_view(), name='file-delete'),
    
    #^ < ==============================[ <- Content -> ]============================== > ^#
    path('content-details/<int:course_id>/<str:content_type>/<int:content_id>', views.ContentDetails.as_view(), name='content-details'),
    
    #^ < ==============================[ <- Invoice -> ]============================== > ^#
    path('invoice/list', views.InvoiceListView.as_view(), name='invoice-list'),
    path('invoice/update/<int:id>', views.UpdateInvoicePayStatusView.as_view(), name='invoice-update'),
    path('invoice/create', views.CreateInvoiceManually.as_view(), name='create-invoice-manually'),
    
    #^ < ==============================[ <- Subscription -> ]============================== > ^#
    path('subscription/list', views.CourseSubscriptionList.as_view(), name='course_subscription_list'),
    path('subscription/cancel', views.CancelSubscription.as_view(), name='cancel-subscription'),
    path('subscription/cancel-bulk', views.CancelSubscriptionBulk.as_view(), name='cancel-subscription-bulk'),
    path('subscription/subscription-many-student', views.SubscriptionManyStudent.as_view(), name='SubscriptionManyStudent'),
    
    #^ < ==============================[ <- Exam -> ]============================== > ^#
    #^ QuestionCategory
    path('question-categories/', views.QuestionCategoryListCreateView.as_view(), name='question-category-list-create'),
    path('question-categories/<int:pk>/', views.QuestionCategoryRetrieveUpdateDestroyView.as_view(), name='question-category-detail'),
    #^ Question
    path('questions/', views.QuestionListCreateView.as_view(), name='question-list-create'),
    path('questions/<int:pk>/', views.QuestionRetrieveUpdateDestroyView.as_view(), name='question-detail'),
    path('questions/bulk/', views.BulkQuestionCreateView.as_view(), name='question-bulk-create'),
    #^ Answres
    path('answers/', views.AnswerListCreateView.as_view(), name='answer-list-create'),
    path('answers/<int:pk>/', views.AnswerRetrieveUpdateDestroyView.as_view(), name='answer-detail'),
    #^ Available Questions counts with different types and filters
    path('questions/count/', views.QuestionCountView.as_view(), name='question-count'),
    #^ Exams
    path('exams/', views.ExamListCreateView.as_view(), name='exam-list-create'),
    path('exams/<int:pk>/', views.ExamDetailView.as_view(), name='exam-detail'),
    #^ Exam Questions
    path('exams/<int:exam_id>/questions/', views.GetExamQuestions.as_view(), name='get_exam_questions'),
    path('exams/<int:exam_id>/questions/<int:question_id>/', views.RemoveExamQuestion.as_view(), name='remove_exam_question'),
    path('exams/<int:exam_id>/add-bank-questions/', views.AddBankExamQuestionsView.as_view()),
    path('exams/<int:exam_id>/add-manual-questions/', views.AddManualExamQuestionsView.as_view()),
    # Random Bank (small bank for Random Exams)
    path('exams/<int:exam_id>/random-bank/', views.GetRandomExamBank.as_view(), name='get-random-exam-bank'),
    path('exams/<int:exam_id>/random-bank/add/', views.AddToRandomExamBank.as_view(), name='add-to-random-exam-bank'),
    #^ Exam Models
    path('exams/models/<int:exam_model_id>/questions/', views.GetExamModelQuestions.as_view(), name='get-exam-model-questions'),
    path('exams/models/<int:exam_model_id>/questions/<int:question_id>/', views.RemoveQuestionFromExamModel.as_view(), name='remove-question-from-exam-model'),
    #^ ExamModels
    path('exammodels/', views.ExamModelListCreateView.as_view(), name='exammodel-list-create'),
    path('exammodels/<int:pk>/', views.ExamModelRetrieveUpdateDestroyView.as_view(), name='exammodel-retrieve-update-destroy'),
    #^ Suggest questions for an exam model
    path('exams/<int:exam_id>/suggest-questions/', views.SuggestQuestionsForModel.as_view(), name='suggest-questions'),
    #^ Add questions to an existing exam model
    path('exams/<int:exam_id>/exam-model/<int:exam_model_id>/add-questions/', views.AddQuestionsToModel.as_view(), name='add-questions-to-model'),
    #^ Essay Submissions
    path('exams/essay-submissions/', views.EssaySubmissionListView.as_view(), name='essay-submissions-list'),
    path('exams/essay-submissions/<int:submission_id>/score/', views.ScoreEssayQuestion.as_view(), name='score-essay-question'),
    #^ Results
    path('exams/exam-results/', views.ResultListView.as_view(), name='exams-results'),
    path('exams/exam-results/<int:result_id>/', views.ExamResultDetailView.as_view(), name='get-result-details'),
    path('exams/reduce_trial/<int:result_id>/', views.ReduceResultTrialView.as_view(), name='update-result'),
    #^ Trial Results
    path('exams/result-trials/<int:result_id>/', views.ResultTrialsView.as_view(), name='result-trials-list'),

    path('exams/<int:exam_id>/took_exam/', views.StudentsTookExamAPIView.as_view(), name='students-took-exam'),
    path('exams/<int:exam_id>/did_not_take_exam/', views.StudentsDidNotTakeExamAPIView.as_view(), name='students-did-not-take-exam'),
    path('exams/<int:student_id>/exams_taken/', views.ExamsTakenByStudentAPIView.as_view(), name='exams-taken-by-student'),
    path('exams/<int:student_id>/exams_not_taken/', views.ExamsNotTakenByStudentAPIView.as_view(), name='exams-not-taken-by-student'),
    
    path('exams/<int:exam_id>/copy/', views.CopyExamView.as_view(), name='copy-exam'),
    #^ < ==============================[ <- View -> ]============================== > ^#
    path('lesson-view/list', views.LessonViewList.as_view(), name='ViewList'),
    path('lesson-view/update-counter/<int:view_id>', views.UpdateStudentView.as_view(), name='UpdateStudentView'),
    path('lesson-view/not-viewed-lesson/<int:lesson_id>', views.StudentsNotViewedLesson.as_view(), name='StudentsNotViewedLesson'),
    
    #^ < ==============================[ <- Mobile App -> ]============================== > ^#
    path('app/app-validation-data', views.AppValidationData.as_view(), name='app-validation-data'),
    #^ < ==============================[ <- Codes -> ]============================== > ^#
    path('codes/generate-student-codes', views.GenerateStudentCodes.as_view(), name='generate-student-codes'),
    path('codes/generate-course-codes', views.GenerateCourseCodes.as_view(), name='generate-course-codes'),
    path('codes/generate-lesson-codes', views.GenerateLessonCodes.as_view(), name='GenerateLessonCodes'),
    path('codes/list-promo-code', views.ListPromoCode.as_view(), name='promo-code-list'),
    path('codes/create-promo-codes/', views.CreatePromoCode.as_view(), name='create-promo-code'),
    path('codes/update-promo-codes/<int:id>', views.UpdatePromoCode.as_view(), name='update-promo-code'),
    path('codes/course-code-list', views.CourseCodeListView.as_view(), name='course-code-list'),
    path('codes/lesson-code-list', views.LessonCodeListView.as_view(), name='LessonCodeListView'),
    path('codes/student-code-list', views.StudentCodeListView.as_view(), name='StudentCodeListView'),
    #^ < ==============================[ <- Permissions -> ]============================== > ^#
    path('permissions/list', views.PermissionListView.as_view(), name='permission-list'),
    path('permissions/add-permissions', views.AddPermissionsToUserView.as_view(), name='add-permissions'),
    #^ < ==============================[ <- ExtraApp -> ]============================== > ^#
    path('news/list', views.NewsListView.as_view(), name='news-list'),
    path('news/create', views.NewsCreateView.as_view(), name='news-create'),
    path('news/update/<int:id>', views.NewsUpdateView.as_view(), name='news-update'),
    path('news/delete/<int:id>', views.NewsDeleteView.as_view(), name='news-delete'),
    path('updates/list', views.UpdateListView.as_view(), name='update-list'),
    #^ < ==============================[ <- Extra -> ]============================== > ^#
    path('extra/course-list', views.ExtraCourseList.as_view(), name='extra-course-list'),
    path('extra/unit-list/<int:course_id>', views.ExtraUnitList.as_view(), name='extra-unit-list'),
    path('extra/lesson-list/<int:unit_id>', views.ExtraLessonList.as_view(), name='extra-lesson-list'),
    #^ < ==============================[ <- Logs -> ]============================== > ^#
    path('logs/', views.RequestLogListView.as_view(), name='request-logs-list'),
    path('logs/delete/', views.RequestLogDeleteView.as_view(), name='request-logs-delete'),


]
