import json
from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.safestring import mark_safe
from accounts.models import User
from subscriptions.models import Lecture,StudyGroup
from .models import Assignment, StudentAnswer
from .forms import AssignmentForm, GradeAssignmentForm, StudentAnswerForm
from django.views.decorators.csrf import csrf_exempt

@login_required
def lecture_assignments(request, lecture_pk):
    lecture = get_object_or_404(Lecture, pk=lecture_pk)
    is_teacher = request.user == lecture.group.teacher
    is_student = request.user in lecture.group.students.all()
    
    if not (is_teacher or is_student):
        messages.error(request, "You don't have permission to view these assignments.")
        return redirect('/')
    
    assignments = lecture.assignments.all().order_by('-created_at')
    
    return render(request, 'assignment/lecture_assignments.html', {
        'lecture': lecture,
        'assignments': assignments,
        'is_teacher': is_teacher
    })


@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def assignment_create(request, lecture_pk):
    lecture = get_object_or_404(Lecture, pk=lecture_pk)
    if request.user != lecture.group.teacher:
        messages.error(request, "You don't have permission to create assignments for this lecture.")
        return redirect('assignment:lecture_detail', pk=lecture_pk)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.lecture = lecture
            assignment.save()
            messages.success(request, 'Assignment created successfully!')
            return redirect('assignment:assignment_detail', pk=assignment.pk)
    else:
        form = AssignmentForm()
    
    return render(request, 'assignment/assignment_create.html', {
        'form': form,
        'lecture': lecture
    })

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def assignment_edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if request.user != assignment.lecture.group.teacher:
        messages.error(request, "You don't have permission to edit this assignment.")
        return redirect('assignment:assignment_detail', pk=pk)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated successfully!')
            return redirect('assignment:assignment_detail', pk=assignment.pk)
    else:
        form = AssignmentForm(instance=assignment)
    
    return render(request, 'assignment/assignment_edit.html', {
        'form': form,
        'assignment': assignment
    })

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if request.user != assignment.lecture.group.teacher:
        messages.error(request, "You don't have permission to delete this assignment.")
        return redirect('assignment:lecture_assignments', assignment.lecture.pk)
    
    lecture_pk = assignment.lecture.pk
    assignment.delete()
    messages.success(request, 'Assignment deleted successfully!')
    return redirect('assignment:lecture_assignments', assignment.lecture.pk)
    
    


@login_required
def assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    is_teacher = request.user == assignment.lecture.group.teacher
    is_student = request.user in assignment.lecture.group.students.all()
    
    if not (is_teacher or is_student):
        messages.error(request, "You don't have permission to view this assignment.")
        return redirect('/')
    
    student_answers = assignment.student_answers.all()
    student_answer = None
    
    if is_student:
        student_answer = StudentAnswer.objects.filter(
            assignment=assignment,
            student=request.user
        ).first()
    
    return render(request, 'assignment/assignment_detail.html', {
        'assignment': assignment,
        'student_answers': student_answers,
        'student_answer': student_answer,
        'is_teacher': is_teacher,
        'is_student': is_student,
        'can_submit': is_student and not assignment.is_past_due(),
        'can_edit': is_student and student_answer and not assignment.is_past_due()
    })


@login_required
@user_passes_test(lambda u: u.role == 'teacher')
@csrf_exempt  # Ensure CSRF is handled correctly
def grade_answer(request, pk):
    answer = get_object_or_404(StudentAnswer, pk=pk)
    if request.user != answer.assignment.lecture.group.teacher:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            grade = data.get('grade')
            feedback = data.get('feedback', '')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if grade is None:
            return JsonResponse({'error': 'Grade is required'}, status=400)

        try:
            grade = int(grade)
            if grade < 0 or grade > answer.assignment.max_grade:
                return JsonResponse({
                    'error': f'Grade must be between 0 and {answer.assignment.max_grade}'
                }, status=400)

            answer.grade = grade
            answer.teacher_feedback = feedback
            answer.save()

            return JsonResponse({
                'success': True,
                'grade': grade,
                'max_grade': answer.assignment.max_grade,
                'feedback': feedback
            })
        except ValueError:
            return JsonResponse({'error': 'Invalid grade value'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
@user_passes_test(lambda u: u.role == 'student')
def student_assignment_list(request, lecture_pk):
    lecture = get_object_or_404(StudyGroup, pk=lecture_pk)
    if request.user not in lecture.group.students.all():
        messages.error(request, "You are not a member of this study group.")
        return redirect('/')
    
    assignments = Assignment.objects.filter(lecture=lecture)
    
    # Prefetch answers for the current student
    assignments = assignments.prefetch_related(
        models.Prefetch(
            'student_answers',
            queryset=StudentAnswer.objects.filter(student=request.user),
            to_attr='student_answer'
        )
    )
    
    return render(request, 'assignment/assignment_list.html', {
        'assignments': assignments,
        'lecture': lecture
    })

@login_required
@user_passes_test(lambda u: u.role == 'student')
def submit_answer(request, assignment_pk):
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    if request.user not in assignment.lecture.group.students.all():
        messages.error(request, "You are not a member of this study group.")
        return redirect('/')
    
    if assignment.is_past_due():
        messages.error(request, "This assignment is past due and can no longer be submitted.")
        return redirect('assignment:student_assignment_list', lecture_pk=assignment.lecture.pk)
    
    if StudentAnswer.objects.filter(assignment=assignment, student=request.user).exists():
        messages.error(request, "You have already submitted an answer for this assignment.")
        return redirect('assignment:student_assignment_list', lecture_pk=assignment.lecture.pk)
    
    if request.method == 'POST':
        form = StudentAnswerForm(request.POST, request.FILES)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.assignment = assignment
            answer.student = request.user
            answer.save()
            messages.success(request, 'Answer submitted successfully!')
            return redirect('assignment:student_assignment_list', lecture_pk=assignment.lecture.pk)
    else:
        form = StudentAnswerForm()
    
    return render(request, 'assignment/answer_form.html', {
        'form': form,
        'assignment': assignment,
        'action': 'Submit'
    })

@login_required
@user_passes_test(lambda u: u.role == 'student')
def edit_answer(request, pk):
    answer = get_object_or_404(StudentAnswer, pk=pk)
    if request.user != answer.student:
        messages.error(request, "You can only edit your own answers.")
        return redirect('assignment:student_assignment_list', lecture_pk=answer.assignment.lecture.pk)
    
    if answer.assignment.is_past_due():
        messages.error(request, "This assignment is past due and can no longer be edited.")
        return redirect('assignment:student_assignment_list', lecture_pk=answer.assignment.lecture.pk)
    
    if request.method == 'POST':
        form = StudentAnswerForm(request.POST, request.FILES, instance=answer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Answer updated successfully!')
            return redirect('assignment:student_assignment_list', lecture_pk=answer.assignment.lecture.pk)
    else:
        form = StudentAnswerForm(instance=answer)
    
    return render(request, 'assignment/answer_form.html', {
        'form': form,
        'assignment': answer.assignment,
        'action': 'Edit'
    })

@login_required
@user_passes_test(lambda u: u.role == 'student')
def delete_answer(request, pk):
    answer = get_object_or_404(StudentAnswer, pk=pk)
    if request.user != answer.student:
        messages.error(request, "You can only delete your own answers.")
        return redirect('assignment:student_assignment_list', lecture_pk=answer.assignment.lecture.pk)
    
    if answer.assignment.is_past_due():
        messages.error(request, "This assignment is past due and answers can no longer be deleted.")
        return redirect('assignment:student_assignment_list', lecture_pk=answer.assignment.lecture.pk)
    
    answer.delete()
    messages.success(request, 'Answer deleted successfully!')
    return redirect('assignment:student_assignment_list', lecture_pk=answer.assignment.lecture.pk)



@login_required
def studygroup_grades(request, pk):
    study_group = get_object_or_404(StudyGroup, pk=pk)
    is_teacher = request.user == study_group.teacher
    has_permission = is_teacher or request.user.has_perm('view_all_reports')

    if not has_permission:
        messages.error(request, "You don't have permission to view this report.")
        return redirect('/')

    assignments = Assignment.objects.filter(lecture__group=study_group)
    students = study_group.students.all()

    report_data = []
    total_grades = []
    assignment_grades_map = {assignment.id: [] for assignment in assignments}

    completion_counts = {
        'completed': 0,
        'partial': 0,
        'not_started': 0
    }

    for student in students:
        student_data = {
            'student': student,
            'assignments': [],
            'average_grade': None
        }
        grades = []
        total_answered = 0

        for assignment in assignments:
            answer = StudentAnswer.objects.filter(
                assignment=assignment,
                student=student
            ).first()

            grade = answer.grade if answer else None

            student_data['assignments'].append({
                'assignment': assignment,
                'answer': answer,
                'grade': grade
            })

            if answer and grade is not None:
                grades.append(grade)
                assignment_grades_map[assignment.id].append(grade)
                total_answered += 1

        if grades:
            avg = sum(grades) / len(grades)
            student_data['average_grade'] = avg
            total_grades.append(avg)

            if total_answered == assignments.count():
                completion_counts['completed'] += 1
            elif total_answered > 0:
                completion_counts['partial'] += 1
            else:
                completion_counts['not_started'] += 1

        report_data.append(student_data)

    # Calculate average grade for each assignment
    for assignment in assignments:
        assignment_grades = assignment_grades_map[assignment.id]
        if assignment_grades:
            assignment.average_grade = sum(assignment_grades) / len(assignment_grades)
        else:
            assignment.average_grade = None

    # Grade distribution for chart (example buckets: 90-100, 80-89, ..., <50)
    grade_distribution = [0] * 6
    for avg in total_grades:
        if avg >= 90:
            grade_distribution[0] += 1
        elif avg >= 80:
            grade_distribution[1] += 1
        elif avg >= 70:
            grade_distribution[2] += 1
        elif avg >= 60:
            grade_distribution[3] += 1
        elif avg >= 50:
            grade_distribution[4] += 1
        else:
            grade_distribution[5] += 1

    # Completion chart data
    completion_status = [
        completion_counts['completed'],
        completion_counts['partial'],
        completion_counts['not_started']
    ]

    # Overall average
    overall_average = sum(total_grades) / len(total_grades) if total_grades else None

    context = {
        'study_group': study_group,
        'assignments': assignments,
        'report_data': report_data,
        'is_teacher': is_teacher,
        'overall_average': overall_average,
        'grade_distribution': mark_safe(json.dumps(grade_distribution)),
        'completion_status': mark_safe(json.dumps(completion_status)),
    }

    return render(request, 'assignment/studygroup_grades.html', context)




@login_required
def student_grades(request, pk, student_pk):
    study_group = get_object_or_404(StudyGroup, pk=pk)
    student = get_object_or_404(User, pk=student_pk)

    # Check permissions
    is_teacher = request.user == study_group.teacher
    is_student = request.user == student
    has_permission = is_teacher or is_student or request.user.has_perm('view_all_reports')

    if not has_permission:
        messages.error(request, "You don't have permission to view this report.")
        return redirect('/')

    assignments = Assignment.objects.filter(lecture__group=study_group)
    student_answers = StudentAnswer.objects.filter(
        assignment__in=assignments,
        student=student
    ).select_related('assignment')

    grades = [answer.grade for answer in student_answers if answer.grade is not None]
    average_grade = sum(grades) / len(grades) if grades else None

    # Calculate the percentage for each assignment
    assignment_data = []
    completion_counts = {
        'completed': 0,
        'not_completed': 0
    }

    for assignment in assignments:
        answer = student_answers.filter(assignment=assignment).first()
        grade = answer.grade if answer and answer.grade is not None else None
        percentage = (grade / assignment.max_grade * 100) if grade is not None else None
        assignment_data.append({
            'assignment': assignment,
            'answer': answer,
            'grade': grade,
            'percentage': percentage,
            'feedback': answer.teacher_feedback if answer else "No feedback"
        })
        if answer:
            completion_counts['completed'] += 1
        else:
            completion_counts['not_completed'] += 1

    # Grade distribution for chart (example buckets: 90-100, 80-89, ..., <50)
    grade_distribution = [0] * 6
    for grade in grades:
        percentage = (grade / assignment.max_grade * 100)
        if percentage >= 90:
            grade_distribution[0] += 1
        elif percentage >= 80:
            grade_distribution[1] += 1
        elif percentage >= 70:
            grade_distribution[2] += 1
        elif percentage >= 60:
            grade_distribution[3] += 1
        elif percentage >= 50:
            grade_distribution[4] += 1
        else:
            grade_distribution[5] += 1

    # Completion chart data
    completion_status = [
        completion_counts['completed'],
        completion_counts['not_completed']
    ]

    context = {
        'study_group': study_group,
        'student': student,
        'assignment_data': assignment_data,
        'average_grade': average_grade,
        'is_teacher': is_teacher,
        'grade_distribution': json.dumps(grade_distribution),
        'completion_status': json.dumps(completion_status),
    }

    return render(request, 'assignment/student_grades.html', context)

