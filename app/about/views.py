from django.shortcuts import get_object_or_404, render
from about.models import CompanyDescription, CompanyDescriptionTranslation, CompanyInfo, CompanyInfoTranslation, FinalProject, FinalProjectTranslation, Policy, PolicyTranslation, SocialAccount, Tech, TechTranslation
from accounts.models import TeacherInfo, TeacherInfoTranslation
from carts.models import CartCourse, CartLevel, CartTrack
from courses.models import  CourseTranslation, Level, LevelContentTranslation, LevelTranslation, Track, Course, TrackTranslation
from admin_interface.models import Theme
from django.shortcuts import render
from django.http import JsonResponse
from .forms import ContactForm
from django.core.mail import EmailMessage

def home(request):
    language = request.GET.get('lang', 'en')  # Default to 'en' if no language is specified

    # Fetch and translate company info
    company_info = CompanyInfo.objects.last()
    company_info_translation = CompanyInfoTranslation.objects.filter(company_info=company_info, language=language).first()
    if company_info_translation:
        company_info.name = company_info_translation.translated_name
        company_info.description = company_info_translation.translated_description

    # Fetch and translate company descriptions
    descriptions = list(CompanyDescription.objects.all())
    translated_descriptions = []
    for description in descriptions:
        translation = CompanyDescriptionTranslation.objects.filter(company_description=description, language=language).first()
        if translation:
            translated_descriptions.append({
                'title': translation.translated_title,
                'description': translation.translated_description,
                'order': description.order,
            })
        else:
            translated_descriptions.append({
                'title': description.title,
                'description': description.description,
                'order': description.order,
            })

    mid_index = len(translated_descriptions) // 2
    left_descriptions = translated_descriptions[:mid_index]
    right_descriptions = translated_descriptions[mid_index:]

    # Fetch and translate techs
    techs = Tech.objects.all()
    translated_techs = []
    for tech in techs:
        translation = TechTranslation.objects.filter(tech=tech, language=language).first()
        if translation:
            translated_techs.append({
                'name': translation.translated_name,
                'image': tech.image,
                'color': tech.color,
            })
        else:
            translated_techs.append({
                'name': tech.name,
                'image': tech.image,
                'color': tech.color,
            })

    # Fetch and translate FinalProjects
    final_projects = FinalProject.objects.all()
    translated_final_projects = []
    for project in final_projects:
        translation = FinalProjectTranslation.objects.filter(final_project=project, language=language).first()
        if translation:
            translated_final_projects.append({
                'title': translation.translated_title,
                'description': translation.translated_description,
                'file': project.file,
                'code_url': project.code_url,
                'preview_url': project.preview_url,
                'is_active': project.is_active,
            })
        else:
            translated_final_projects.append({
                'title': project.title,
                'description': project.description,
                'file': project.file,
                'code_url': project.code_url,
                'preview_url': project.preview_url,
                'is_active': project.is_active,
            })
    
    # Fetch and translate teachers
    teachers = TeacherInfo.objects.filter(is_active_to_be_shown_in_home=True)
    translated_teachers = []
    for teacher in teachers:
        translation = TeacherInfoTranslation.objects.filter(teacher_info=teacher, language=language).first()
        if translation:
            translated_teachers.append({
                'teacher': teacher.teacher,
                'bio': translation.translated_bio,
                'specialization': translation.translated_specialization,
                'profile_link': teacher.profile_link,
                'courses': teacher.courses.all(),
            })
        else:
            translated_teachers.append({
                'teacher': teacher.teacher,
                'bio': teacher.bio,
                'specialization': teacher.specialization,
                'profile_link': teacher.profile_link,
                'courses': teacher.courses.all(),
            })

    # Fetch social accounts and theme
    social_accounts = SocialAccount.objects.all()
    theme = Theme.objects.filter(active=True).first()
    logo_url = theme.logo.url if theme and theme.logo else None

    # Initialize empty sets in case the user is not authenticated
    cart_courses = set()
    cart_tracks = set()
    cart_levels = set()

    if request.user.is_authenticated:
        cart_courses = set(CartCourse.objects.filter(student=request.user).values_list('course_id', flat=True))
        cart_tracks = set(CartTrack.objects.filter(student=request.user).values_list('track_id', flat=True))
        cart_levels = set(CartLevel.objects.filter(student=request.user).values_list('level_id', flat=True))

    cart_item_ids = cart_courses | cart_tracks | cart_levels

    # Fetch and translate discounted items
    discounted_courses = Course.objects.filter(discountcourse__isnull=False)
    discounted_tracks = Track.objects.filter(discounttrack__isnull=False)
    discounted_levels = Level.objects.filter(discountlevel__isnull=False)

    discounted_items = []
    for course in discounted_courses:
        course_translation = CourseTranslation.objects.filter(course=course, language=language).first()
        discounted_items.append({
            'type': 'Course',
            'id': course.id,
            'name': course_translation.translated_name if course_translation else course.name,
            'description': course_translation.translated_description if course_translation else course.description,
            'image': course.image,
            'price_without_any_discount': course.price_without_any_discount,
            'discount_percent': course.discount_percent,
            'has_discount': course.has_discount,
            'final_price_after_discound': course.final_price_after_discound,
        })

    for track in discounted_tracks:
        track_translation = TrackTranslation.objects.filter(track=track, language=language).first()
        discounted_items.append({
            'type': 'Track',
            'id': track.id,
            'name': track_translation.translated_name if track_translation else track.name,
            'description': track_translation.translated_description if track_translation else track.description,
            'image': track.image,
            'price_without_any_discount': track.price_without_any_discount,
            'discount_percent': track.discount_percent,
            'has_discount': track.has_discount,
            'final_price_after_discound': track.final_price_after_discound,
        })

    for level in discounted_levels:
        level_translation = LevelTranslation.objects.filter(level=level, language=language).first()
        discounted_items.append({
            'type': 'Level',
            'id': level.id,
            'name': level_translation.translated_name if level_translation else level.name,
            'description': level_translation.translated_description if level_translation else level.description,
            'image': level.image,
            'price_without_any_discount': level.price_without_any_discount,
            'discount_percent': level.discount_percent,
            'has_discount': level.has_discount,
            'final_price_after_discound': level.final_price_after_discound,
        })

    # Fetch all levels with their related tracks and courses
    levels = Level.objects.prefetch_related('tracks__courses', 'courses')

    # Structure the data for the template
    levels_data = []
    for level in levels:
        # Translate level name and description
        level_translation = LevelTranslation.objects.filter(level=level, language=language).first()
        level_name = level_translation.translated_name if level_translation else level.name
        level_description = level_translation.translated_description if level_translation else level.description

        # Translate level content
        level_content_data = []
        for content in level.contents.all():
            content_translation = LevelContentTranslation.objects.filter(level_content=content, language=language).first()
            content_name = content_translation.translated_name if content_translation else content.name
            level_content_data.append({"name": content_name})

        # Translate tracks and their courses
        tracks = []
        for track in level.tracks.all():
            track_translation = TrackTranslation.objects.filter(track=track, language=language).first()
            track_name = track_translation.translated_name if track_translation else track.name
            courses = []
            for course in track.courses.all():
                course_translation = CourseTranslation.objects.filter(course=course, language=language).first()
                course_name = course_translation.translated_name if course_translation else course.name
                courses.append({"name": course_name})
            tracks.append({
                "name": track_name,
                "courses": courses
            })

        # Translate individual courses
        individual_courses_data = []
        for course in level.courses.filter(track__isnull=True):
            course_translation = CourseTranslation.objects.filter(course=course, language=language).first()
            course_name = course_translation.translated_name if course_translation else course.name
            individual_courses_data.append({"name": course_name})

        # Append translated level data
        levels_data.append({
            "id": level.id,
            "name": level_name,
            "description": level_description,
            "image": level.image,
            "year_limit": level.year_limit,
            "individual_courses": individual_courses_data,
            "tracks": tracks,
            "levelcontent": level_content_data,
        })

    context = {
        'logo_url': logo_url,
        'techs': translated_techs,
        'final_projects': translated_final_projects,
        'teachers': translated_teachers,
        'social_accounts': social_accounts,
        'company_info': company_info,
        'left_descriptions': left_descriptions,
        'right_descriptions': right_descriptions,
        'discounted_items': discounted_items,
        'cart_item_ids': cart_item_ids,
        'levels_data': levels_data,
    }
    return render(request, 'about/home.html', context)


def about_us(request):
    return render(request, 'about/about_us.html')

def send_email(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            company_info = CompanyInfo.objects.last()
            # Create the email message
            email = EmailMessage(
                subject='HiCode Contact',
                body=message,
                from_email='platraincloud@gmail.com',  # Must match authenticated email
                to=[company_info.email],  # Your receiving end
                headers={'Reply-To': user_email}  # Include the user's email as Reply-To
            )
            
            email.send(fail_silently=False)

            return JsonResponse({'message': 'Email sent successfully!'})
        return JsonResponse({'errors': form.errors}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def policy_detail(request, policy_type):
    language = request.GET.get('lang', 'en')  # Default to 'en' if no language is specified

    # Fetch the policy
    policy = get_object_or_404(Policy, policy_type=policy_type)
    print(policy)

    # Fetch the translation for the selected language
    policy_translation = PolicyTranslation.objects.filter(policy=policy, language=language).first()
    print(policy_translation)
    # Use translated content if available, otherwise use the default content
    content = policy_translation.translated_content if policy_translation else policy.content
    print(content)
    context = {
        'policy': policy,
        'content': content,
    }
    return render(request, 'about/policy_detail.html', context)











