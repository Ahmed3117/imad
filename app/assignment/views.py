from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from accounts.models import User
from subscriptions.models import Lecture,StudyGroup
from .models import Assignment, StudentAnswer
from .forms import AssignmentForm, GradeAssignmentForm, StudentAnswerForm

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def assignment_create(request, lecture_pk):
    lecture = get_object_or_404(Lecture, pk=lecture_pk)
    if request.user != lecture.group.teacher:
        messages.error(request, "You don't have permission to create assignments for this lecture.")
        return redirect('lecture_detail', pk=lecture_pk)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.lecture = lecture
            assignment.save()
            messages.success(request, 'Assignment created successfully!')
            return redirect('assignment_detail', pk=assignment.pk)
    else:
        form = AssignmentForm()
    
    return render(request, 'assignments/teacher/assignment_create.html', {
        'form': form,
        'lecture': lecture
    })

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def assignment_edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if request.user != assignment.lecture.group.teacher:
        messages.error(request, "You don't have permission to edit this assignment.")
        return redirect('assignment_detail', pk=pk)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated successfully!')
            return redirect('assignment_detail', pk=assignment.pk)
    else:
        form = AssignmentForm(instance=assignment)
    
    return render(request, 'assignments/teacher/assignment_edit.html', {
        'form': form,
        'assignment': assignment
    })

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if request.user != assignment.lecture.group.teacher:
        messages.error(request, "You don't have permission to delete this assignment.")
        return redirect('assignment_detail', pk=pk)
    
    lecture_pk = assignment.lecture.pk
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Assignment deleted successfully!')
        return redirect('lecture_detail', pk=lecture_pk)
    
    return render(request, 'assignments/teacher/assignment_confirm_delete.html', {
        'assignment': assignment
    })

@login_required
def assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    is_teacher = request.user == assignment.lecture.group.teacher
    is_student = request.user in assignment.lecture.group.students.all()
    
    if not (is_teacher or is_student):
        messages.error(request, "You don't have permission to view this assignment.")
        return redirect('home')
    
    student_answers = assignment.student_answers.all()
    
    return render(request, 'assignments/teacher/assignment_detail.html', {
        'assignment': assignment,
        'student_answers': student_answers,
        'is_teacher': is_teacher
    })

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def grade_answer(request, pk):
    answer = get_object_or_404(StudentAnswer, pk=pk)
    if request.user != answer.assignment.lecture.group.teacher:
        messages.error(request, "You don't have permission to grade this answer.")
        return redirect('assignment_detail', pk=answer.assignment.pk)
    
    if request.method == 'POST':
        form = GradeAssignmentForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grade submitted successfully!')
            return redirect('assignment_detail', pk=answer.assignment.pk)
    else:
        form = GradeAssignmentForm(instance=answer)
    
    return render(request, 'assignments/teacher/grade_assignment.html', {
        'form': form,
        'answer': answer
    })

@login_required
@user_passes_test(lambda u: u.role == 'student')
def student_assignment_list(request, group_pk):
    study_group = get_object_or_404(StudyGroup, pk=group_pk)
    if request.user not in study_group.students.all():
        messages.error(request, "You are not a member of this study group.")
        return redirect('home')
    
    assignments = Assignment.objects.filter(lecture__group=study_group)
    
    # Prefetch answers for the current student
    assignments = assignments.prefetch_related(
        models.Prefetch(
            'student_answers',
            queryset=StudentAnswer.objects.filter(student=request.user),
            to_attr='student_answer'
        )
    )
    
    return render(request, 'assignments/student/assignment_list.html', {
        'assignments': assignments,
        'studygroup': study_group
    })

@login_required
@user_passes_test(lambda u: u.role == 'student')
def submit_answer(request, assignment_pk):
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    if request.user not in assignment.lecture.group.students.all():
        messages.error(request, "You are not a member of this study group.")
        return redirect('home')
    
    if assignment.is_past_due():
        messages.error(request, "This assignment is past due and can no longer be submitted.")
        return redirect('student_assignment_list', group_pk=assignment.lecture.group.pk)
    
    if StudentAnswer.objects.filter(assignment=assignment, student=request.user).exists():
        messages.error(request, "You have already submitted an answer for this assignment.")
        return redirect('student_assignment_list', group_pk=assignment.lecture.group.pk)
    
    if request.method == 'POST':
        form = StudentAnswerForm(request.POST, request.FILES)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.assignment = assignment
            answer.student = request.user
            answer.save()
            messages.success(request, 'Answer submitted successfully!')
            return redirect('student_assignment_list', group_pk=assignment.lecture.group.pk)
    else:
        form = StudentAnswerForm()
    
    return render(request, 'assignments/student/answer_form.html', {
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
        return redirect('student_assignment_list', group_pk=answer.assignment.lecture.group.pk)
    
    if answer.assignment.is_past_due():
        messages.error(request, "This assignment is past due and can no longer be edited.")
        return redirect('student_assignment_list', group_pk=answer.assignment.lecture.group.pk)
    
    if request.method == 'POST':
        form = StudentAnswerForm(request.POST, request.FILES, instance=answer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Answer updated successfully!')
            return redirect('student_assignment_list', group_pk=answer.assignment.lecture.group.pk)
    else:
        form = StudentAnswerForm(instance=answer)
    
    return render(request, 'assignments/student/answer_form.html', {
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
        return redirect('student_assignment_list', group_pk=answer.assignment.lecture.group.pk)
    
    if answer.assignment.is_past_due():
        messages.error(request, "This assignment is past due and answers can no longer be deleted.")
        return redirect('student_assignment_list', group_pk=answer.assignment.lecture.group.pk)
    
    if request.method == 'POST':
        answer.delete()
        messages.success(request, 'Answer deleted successfully!')
        return redirect('student_assignment_list', group_pk=answer.assignment.lecture.group.pk)
    
    return render(request, 'assignments/student/answer_confirm_delete.html', {
        'answer': answer
    })


@login_required
def studygroup_grades(request, pk):
    study_group = get_object_or_404(StudyGroup, pk=pk)
    is_teacher = request.user == study_group.teacher
    has_permission = is_teacher or request.user.has_perm('view_all_reports')
    
    if not has_permission:
        messages.error(request, "You don't have permission to view this report.")
        return redirect('home')
    
    assignments = Assignment.objects.filter(lecture__group=study_group)
    students = study_group.students.all()
    
    report_data = []
    for student in students:
        student_data = {
            'student': student,
            'assignments': [],
            'average_grade': None
        }
        grades = []
        
        for assignment in assignments:
            answer = StudentAnswer.objects.filter(
                assignment=assignment,
                student=student
            ).first()
            
            student_data['assignments'].append({
                'assignment': assignment,
                'answer': answer,
                'grade': answer.grade if answer else None
            })
            
            if answer and answer.grade is not None:
                grades.append(answer.grade)
        
        if grades:
            student_data['average_grade'] = sum(grades) / len(grades)
        
        report_data.append(student_data)
    
    return render(request, 'assignments/reports/studygroup_grades.html', {
        'study_group': study_group,
        'report_data': report_data,
        'is_teacher': is_teacher
    })

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
        return redirect('home')
    
    assignments = Assignment.objects.filter(lecture__group=study_group)
    student_answers = StudentAnswer.objects.filter(
        assignment__in=assignments,
        student=student
    ).select_related('assignment')
    
    grades = [answer.grade for answer in student_answers if answer.grade is not None]
    average_grade = sum(grades) / len(grades) if grades else None
    
    return render(request, 'assignments/reports/student_grades.html', {
        'study_group': study_group,
        'student': student,
        'student_answers': student_answers,
        'average_grade': average_grade,
        'is_teacher': is_teacher
    })



