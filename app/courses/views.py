from django.shortcuts import render

from subscriptions.models import JoinRequest


from .models import CourseTranslation, Level,LevelTranslation,Track, Course, TrackTranslation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from decimal import Decimal
from django.views.decorators.http import require_POST
from .models import  Course


def levels(request):
    language = request.GET.get('lang', 'en')  # Default to 'en' if no language is specified

    # Get all levels with their related data
    levels = Level.objects.prefetch_related(
        'courses',
        'tracks',
        'tracks__courses',
    ).all()

    # Process each level's data
    levels_data = []
    for level in levels:
        # Translate level name
        level_translation = LevelTranslation.objects.filter(level=level, language=language).first()
        level_name = level_translation.translated_name if level_translation else level.name

        # Translate individual courses
        individual_courses = []
        for course in level.courses.filter(track__isnull=True):
            course_translation = CourseTranslation.objects.filter(course=course, language=language).first()
            course_name = course_translation.translated_name if course_translation else course.name
            course_description = course_translation.translated_description if course_translation else course.description
            join_request_exists = None
            if request.user.is_authenticated:
                join_request_exists = JoinRequest.objects.filter(student=request.user, course=course).exists()
            individual_courses.append({
                'id': course.id,
                'name': course_name,
                'description': course_description,
                'image': course.image,
                'preview_video': course.preview_video,
                'join_request_exists': join_request_exists,
            })

        # Translate tracks and their courses
        tracks = []
        for track in level.tracks.all():
            track_translation = TrackTranslation.objects.filter(track=track, language=language).first()
            track_name = track_translation.translated_name if track_translation else track.name

            # Translate courses within the track
            courses = []
            for course in track.courses.all():
                course_translation = CourseTranslation.objects.filter(course=course, language=language).first()
                course_name = course_translation.translated_name if course_translation else course.name
                course_description = course_translation.translated_description if course_translation else course.description
                join_request_exists = None
                if request.user.is_authenticated:
                    join_request_exists = JoinRequest.objects.filter(student=request.user, course=course).exists()
                courses.append({
                    'id': course.id,
                    'name': course_name,
                    'description': course_description,
                    'image': course.image,
                    'preview_video': course.preview_video,
                    'join_request_exists': join_request_exists,
                })

            tracks.append({
                'id': track.id,
                'name': track_name,
                'courses': courses,
            })

        level_data = {
            'name': level_name,
            'id': level.id,
            'individual_courses': individual_courses,
            'tracks': tracks,
        }
        levels_data.append(level_data)

    context = {
        'levels': levels_data,
    }
    return render(request, 'courses/levels.html', context)


@csrf_exempt
def send_join_request(request, course_id):
    if request.method == 'POST' and request.user.is_authenticated:
        course = Course.objects.get(id=course_id)
        if not JoinRequest.objects.filter(student=request.user, course=course).exists():
            JoinRequest.objects.create(student=request.user, course=course)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Request already sent.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})