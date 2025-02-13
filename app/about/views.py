from django.shortcuts import get_object_or_404, render
from about.models import CompanyInfo, CompanyInfoTranslation, Policy, PolicyTranslation, SocialAccount
from accounts.models import TeacherInfo, TeacherInfoTranslation
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

    context = {
        'logo_url': logo_url,
        'teachers': translated_teachers,
        'social_accounts': social_accounts,
        'company_info': company_info
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











