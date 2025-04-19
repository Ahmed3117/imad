
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from subscriptions.models import StudyGroup, StudyGroupResource
from .models import CourseLibrary, Course
from django.db.models import Q

def course_library_view(request):
    # Get all CourseLibrary entries initially
    libraries = CourseLibrary.objects.all()
    
    # Handle search query
    search_query = request.GET.get('search', '').strip()
    if search_query:
        libraries = libraries.filter(
            Q(course__name__icontains=search_query) |
            Q(file__icontains=search_query)
        )
    
    # Handle course filter
    course_id = request.GET.get('course', '')
    if course_id:
        libraries = libraries.filter(course__id=course_id)
    
    # Get all courses for the filter dropdown
    courses = Course.objects.all()
    
    context = {
        'libraries': libraries,
        'courses': courses,
        'search_query': search_query,
        'selected_course': course_id,
    }
    
    return render(request, 'library/course_library_list.html', context)



def get_study_groups(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.user.role != 'teacher':
        return JsonResponse({'error': 'Only teachers can access this endpoint'}, status=403)

    try:
        teacher = request.user
        course_id = request.GET.get('course_id', '')
        
        # Filter study groups where the current user is the teacher
        study_groups = StudyGroup.objects.filter(teacher=teacher)
        
        # Apply course filter if provided
        if course_id:
            study_groups = study_groups.filter(course_id=course_id)
        
        # Prepare the response data
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

def share_resources(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return JsonResponse({'error': 'Teacher authentication required'}, status=403)

    try:
        resource_ids = request.POST.getlist('resource_ids')
        studygroup_ids = request.POST.getlist('studygroup_ids')
        
        if not resource_ids or not studygroup_ids:
            return JsonResponse({'error': 'No resources or study groups selected'}, status=400)
        
        # Verify all study groups belong to this teacher
        teacher_groups = StudyGroup.objects.filter(
            id__in=studygroup_ids,
            teacher=request.user
        ).values_list('id', flat=True)
        
        if len(teacher_groups) != len(studygroup_ids):
            return JsonResponse({'error': 'Invalid study group selection'}, status=400)
        
        # Create the shared resources
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






