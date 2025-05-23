


from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from subscriptions.models import StudyGroup, StudyGroupResource
from .models import CourseLibrary, LibraryCategory, Course
from django.contrib import messages


def course_library_view(request):
    libraries = CourseLibrary.objects.all()
    search_query = request.GET.get('search', '').strip()
    course_id = request.GET.get('course', '')
    category_id = request.GET.get('category', '')

    if search_query:
        libraries = libraries.filter(
            Q(course__name__icontains=search_query) |
            Q(file__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    if course_id:
        libraries = libraries.filter(course__id=course_id)
    
    if category_id:
        libraries = libraries.filter(category__id=category_id)

    courses = Course.objects.all()
    categories = LibraryCategory.objects.all()

    context = {
        'libraries': libraries,
        'courses': courses,
        'categories': categories,
        'search_query': search_query,
        'selected_course': course_id,
        'selected_category': category_id,
    }
    
    return render(request, 'library/course_library_list.html', context)

# Updated add_course_library view with AJAX support
@login_required
def add_course_library(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Admin authentication required'}, status=403)

    if request.method == 'POST':
        course_id = request.POST.get('course')
        category_id = request.POST.get('category')
        files = request.FILES.getlist('files')

        if not files or not course_id:
            return JsonResponse({'error': 'Please select a course and at least one file.'}, status=400)

        try:
            course = get_object_or_404(Course, id=course_id)
            category = get_object_or_404(LibraryCategory, id=category_id) if category_id else None

            for file in files:
                CourseLibrary.objects.create(
                    course=course,
                    file=file,
                    category=category
                )

            return JsonResponse({'status': 'success', 'message': 'Files uploaded successfully.'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    courses = Course.objects.all()
    categories = LibraryCategory.objects.all()
    return render(request, 'library/add_course_library.html', {
        'courses': courses,
        'categories': categories,
    })

@login_required
def create_library_category(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Admin authentication required'}, status=403)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            return JsonResponse({'error': 'Category name is required'}, status=400)

        try:
            category, created = LibraryCategory.objects.get_or_create(
                name=name,
                defaults={'description': description if description else None}
            )
            if not created:
                return JsonResponse({'error': 'Category with this name already exists'}, status=400)

            return JsonResponse({
                'status': 'success',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description or ''
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST method required'}, status=405)

# New view to edit CourseLibrary entry
@login_required
def edit_course_library(request, library_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Admin authentication required'}, status=403)

    library = get_object_or_404(CourseLibrary, id=library_id)

    if request.method == 'POST':
        course_id = request.POST.get('course')
        category_id = request.POST.get('category')
        file = request.FILES.get('file')

        library.course = get_object_or_404(Course, id=course_id)
        library.category = get_object_or_404(LibraryCategory, id=category_id) if category_id else None
        if file:
            library.file = file
        library.save()

        messages.success(request, 'Library entry updated successfully.')
        return redirect('library:course_library')

    courses = Course.objects.all()
    categories = LibraryCategory.objects.all()
    return render(request, 'library/edit_course_library.html', {
        'library': library,
        'courses': courses,
        'categories': categories,
    })


# New view to delete CourseLibrary entry
@login_required
def delete_course_library(request, library_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Admin authentication required'}, status=403)

    library = get_object_or_404(CourseLibrary, id=library_id)
    library.delete()
    return JsonResponse({'status': 'success', 'message': 'Resource deleted successfully'})

def get_study_groups(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.user.role != 'teacher' and not request.user.is_superuser:
        return JsonResponse({'error': 'Only teachers or superusers can access this endpoint'}, status=403)

    try:
        course_id = request.GET.get('course_id', '')
        
        # Superusers get all study groups; teachers get only their own
        if request.user.is_superuser:
            study_groups = StudyGroup.objects.all()
        else:
            study_groups = StudyGroup.objects.filter(teacher=request.user)
        
        if course_id:
            study_groups = study_groups.filter(course_id=course_id)
        
        data = [{
            'id': group.id,
            'name': f"{group.course.name} - {group.course.level.name}",
            'course': group.course.name,
            'level': group.course.level.name,
            'capacity': group.capacity
        } for group in study_groups.select_related('course', 'course__level')]
        
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# share_resources view 
def share_resources(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    if not request.user.is_authenticated or (request.user.role != 'teacher' and not request.user.is_superuser):
        return JsonResponse({'error': 'Teacher or superuser authentication required'}, status=403)

    try:
        resource_ids = request.POST.getlist('resource_ids')
        studygroup_ids = request.POST.getlist('studygroup_ids')
        
        if not resource_ids or not studygroup_ids:
            return JsonResponse({'error': 'No resources or study groups selected'}, status=400)
        
        # Superusers can share to any study group; teachers only to their own
        if request.user.is_superuser:
            valid_groups = StudyGroup.objects.filter(id__in=studygroup_ids).values_list('id', flat=True)
        else:
            valid_groups = StudyGroup.objects.filter(
                id__in=studygroup_ids,
                teacher=request.user
            ).values_list('id', flat=True)
        
        if len(valid_groups) != len(studygroup_ids):
            return JsonResponse({'error': 'Invalid study group selection'}, status=400)
        
        created_count = 0
        for resource_id in resource_ids:
            resource = get_object_or_404(CourseLibrary, id=resource_id)
            for group_id in studygroup_ids:
                _, created = StudyGroupResource.objects.get_or_create(
                    studygroup_id=group_id,
                    resource=resource,
                    shared_by=request.user
                )
                if created:
                    created_count += 1
        
        return JsonResponse({
            'status': 'success',
            'shared_count': created_count
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

