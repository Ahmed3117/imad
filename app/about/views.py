import json

from accounts.models import TeacherInfo, TeacherInfoTranslation
from admin_interface.models import Theme
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from about.models import (
    CompanyInfo,
    CompanyInfoTranslation,
    HomePageContent,
    HomePageContentTranslation,
    HomePageFeatureTranslation,
    HomePageVideoPointTranslation,
)

from .forms import ContactForm

DEFAULT_HOME_PAGE_TEXT = {
    "hero_badge": "FREE TRIAL — NO CARD REQUIRED",
    "hero_title": "Your Child Deserves to Love the Quran",
    "hero_description": "Book a free 1-on-1 class with a certified Egyptian teacher. Real instruction, real progress — from the comfort of your home.",
    "hero_primary_button_text": "Book Your Child's Free Class",
    "hero_side_title": "A Real Teacher. A Real Relationship. Real Results.",
    "hero_side_description": "Most online platforms feel transactional. We focus on matching each learner with a dedicated teacher who understands their pace, personality, and goals — so progress feels personal, steady, and meaningful.",
    "hero_trust_badge_1": "Al-Azhar Certified teachers",
    "hero_trust_badge_2": "⭐ 4.9/5 parent rating",
    "hero_trust_badge_3": "🕐 24/7 scheduling — your timezone",
    "hero_trust_badge_4": "👨‍👩‍👧‍👦 Family bundles available",
    "hero_pricing_note": "💰 From $45/mo after trial",
    "primary_features_title": "Why Families Choose Us",
    "primary_features_description": "We combine authentic Quran teaching, personal teacher matching, flexible scheduling, and family-friendly support to create a learning experience children enjoy and parents trust.",
    "primary_features_empty_text": "New highlights will appear here soon.",
    "who_we_are_title": "Why Nabbiuwny",
    "who_we_are_lead": "A real teacher, a real relationship, and real results — built around your child's long-term Quran journey.",
    "who_we_are_description": "Most online platforms operate like institutions with rotating staff and generic lesson flow. Nabbiuwny takes a more personal approach. We match each student with one dedicated teacher who learns their level, supports their confidence, and grows with them over time. That consistency helps children not only improve in recitation and understanding, but also build a lasting love for Quran learning.",
    "who_we_are_button_text": "Explore Learning Options",
    "video_section_title": "See How the Journey Works",
    "video_section_description": "From the first class to steady weekly progress, our learning experience is designed to be clear, supportive, and measurable for both children and parents.",
    "video_point_fallback": "Live, one-on-one Quran learning with a teacher who truly knows your child.",
    "chat_section_title": "Talk to Us Before You Decide",
    "chat_section_description_1": "If you have questions about age, level, scheduling, or the right program, our team is here to help you make the best choice with confidence.",
    "chat_section_description_2": "Reach out anytime to discuss your child's needs, compare options, and get guidance before booking or enrolling.",
    "chat_button_text": "Chat With Us",
    "secondary_features_title": "What Makes the Experience Different",
    "secondary_features_description": "Beyond strong teaching, we focus on the details that help families stay consistent, informed, and confident throughout the learning journey.",
    "secondary_features_empty_text": "More program details will be added soon.",
    "teachers_section_title": "Our Teachers",
    "teachers_section_subtitle": "Al-Azhar certified, carefully vetted, and experienced in teaching children, teens, and adults with patience, clarity, and care.",
    "testimonials_section_title": "What Parents Are Saying",
    "testimonials_section_subtitle": "Real feedback from families who saw confidence, consistency, and love for Quran learning grow at home.",
    "process_section_title": "From Sign-Up to First Class in 24 Hours",
    "process_section_description": "A simple, guided process that helps your family get started quickly and confidently.",
    "free_session_section_badge": "100% FREE • NO CARD REQUIRED",
    "free_session_section_title": "Book Your Child's Free Trial Class",
    "free_session_section_description": "Takes 60 seconds. We'll match your child with the right teacher and help you experience the quality before you commit.",
    "free_session_privacy_note": "Your info is private. We never sell data. If you enroll and the first week is not the right fit, you're covered by our money-back guarantee.",
    "family_bundle_section_badge": "FAMILY BUNDLE — EXCLUSIVE OFFER",
    "family_bundle_section_title": "One Platform. Every Child. One Price.",
    "family_bundle_section_description": "Give all your children the Islamic education they deserve. Our Family Bundle is designed for Muslim families who want dedicated teachers, transparent pricing, and a simpler way to support every child at once.",
    "family_bundle_section_pricing_note_1": "$45 per child / month",
    "family_bundle_section_pricing_note_2": "3 children for $95/mo",
    "family_bundle_section_pricing_note_3": "$40+ average monthly savings vs. competitors",
    "family_bundle_section_pricing_note_4": "Free first class, no card needed",
    "family_bundle_plans_title": "Transparent Pricing. No Surprises.",
    "family_bundle_plans_description": "Every plan includes dedicated certified teaching, weekly parent updates, progress tracking, and a clear first-week money-back guarantee.",
    "family_bundle_comparison_title": "How We Compare",
    "family_bundle_comparison_description": "Families choose us for transparent pricing, dedicated teachers, personal communication, and a trial-first experience that reduces risk.",
    "family_bundle_faq_title": "Questions Answered",
    "family_bundle_faq_description": "Clear answers for the most common family bundle questions before you book.",
    "family_bundle_cta_title": "Start Your Family's Quran Journey Today",
    "family_bundle_cta_description": "Free trial for every child. No cards. No commitment. Just the Islamic education your family deserves.",
    "family_bundle_cta_button_text": "Get the Family Bundle",
    "contact_section_title": "Get in Touch",
    "contact_section_description": "Need help choosing the right starting point, understanding pricing, or planning for multiple children? Send us a message and we'll guide you.",
    "contact_info_title": "Contact Information",
    "contact_info_description": "Reach out directly by phone, email, or Facebook and our team will help you take the next step with clarity.",
    "facebook_label": "Follow us on Facebook",
    "footer_description": "Nabbiuwny helps families build a meaningful Quran journey through certified teachers, personal guidance, flexible scheduling, and a learning experience children can truly enjoy.",
    "footer_cta_text": "Book the Free Class Now",
    "footer_created_by_text": "Built to support meaningful Quran learning for families everywhere",
    "footer_copyright_text": "© Nabbiuwny",
}


def _get_current_language(request):
    return request.GET.get("lang", "en")


def _get_company_info(language):
    company_info = CompanyInfo.objects.last()
    if not company_info:
        return None

    translation = CompanyInfoTranslation.objects.filter(
        company_info=company_info,
        language=language,
    ).first()

    if translation:
        company_info.name = translation.translated_name or company_info.name
        company_info.description = (
            translation.translated_description or company_info.description
        )

    return company_info


def _get_home_page_content():
    home_page = HomePageContent.get_solo()
    if home_page:
        return home_page

    return HomePageContent.objects.create()


def _apply_home_translation(home_page, language):
    english_translation = HomePageContentTranslation.objects.filter(
        home_page=home_page,
        language="en",
    ).first()
    translation = HomePageContentTranslation.objects.filter(
        home_page=home_page,
        language=language,
    ).first()

    source_translation = translation or english_translation
    translated_content = DEFAULT_HOME_PAGE_TEXT.copy()

    if not source_translation:
        return translated_content

    translated_content.update(
        {
            "hero_badge": source_translation.hero_badge
            or translated_content["hero_badge"],
            "hero_title": source_translation.hero_title
            or translated_content["hero_title"],
            "hero_description": source_translation.hero_description
            or translated_content["hero_description"],
            "hero_primary_button_text": source_translation.hero_primary_button_text
            or translated_content["hero_primary_button_text"],
            "hero_side_title": source_translation.hero_side_title
            or translated_content["hero_side_title"],
            "hero_side_description": source_translation.hero_side_description
            or translated_content["hero_side_description"],
            "hero_trust_badge_1": source_translation.hero_trust_badge_1
            or translated_content["hero_trust_badge_1"],
            "hero_trust_badge_2": source_translation.hero_trust_badge_2
            or translated_content["hero_trust_badge_2"],
            "hero_trust_badge_3": source_translation.hero_trust_badge_3
            or translated_content["hero_trust_badge_3"],
            "hero_trust_badge_4": source_translation.hero_trust_badge_4
            or translated_content["hero_trust_badge_4"],
            "hero_pricing_note": source_translation.hero_pricing_note
            or translated_content["hero_pricing_note"],
            "primary_features_title": source_translation.primary_features_title
            or translated_content["primary_features_title"],
            "primary_features_description": source_translation.primary_features_description
            or translated_content["primary_features_description"],
            "primary_features_empty_text": source_translation.primary_features_empty_text
            or translated_content["primary_features_empty_text"],
            "who_we_are_title": source_translation.who_we_are_title
            or translated_content["who_we_are_title"],
            "who_we_are_lead": source_translation.who_we_are_lead
            or translated_content["who_we_are_lead"],
            "who_we_are_description": source_translation.who_we_are_description
            or translated_content["who_we_are_description"],
            "who_we_are_button_text": source_translation.who_we_are_button_text
            or translated_content["who_we_are_button_text"],
            "video_section_title": source_translation.video_section_title
            or translated_content["video_section_title"],
            "video_section_description": source_translation.video_section_description
            or translated_content["video_section_description"],
            "video_point_fallback": source_translation.video_point_fallback
            or translated_content["video_point_fallback"],
            "chat_section_title": source_translation.chat_section_title
            or translated_content["chat_section_title"],
            "chat_section_description_1": source_translation.chat_section_description_1
            or translated_content["chat_section_description_1"],
            "chat_section_description_2": source_translation.chat_section_description_2
            or translated_content["chat_section_description_2"],
            "chat_button_text": source_translation.chat_button_text
            or translated_content["chat_button_text"],
            "secondary_features_title": source_translation.secondary_features_title
            or translated_content["secondary_features_title"],
            "secondary_features_description": source_translation.secondary_features_description
            or translated_content["secondary_features_description"],
            "secondary_features_empty_text": source_translation.secondary_features_empty_text
            or translated_content["secondary_features_empty_text"],
            "teachers_section_title": source_translation.teachers_section_title
            or translated_content["teachers_section_title"],
            "teachers_section_subtitle": source_translation.teachers_section_subtitle
            or translated_content["teachers_section_subtitle"],
            "testimonials_section_title": source_translation.testimonials_section_title
            or translated_content["testimonials_section_title"],
            "testimonials_section_subtitle": source_translation.testimonials_section_subtitle
            or translated_content["testimonials_section_subtitle"],
            "process_section_title": source_translation.process_section_title
            or translated_content["process_section_title"],
            "process_section_description": source_translation.process_section_description
            or translated_content["process_section_description"],
            "free_session_section_badge": source_translation.free_session_section_badge
            or translated_content["free_session_section_badge"],
            "free_session_section_title": source_translation.free_session_section_title
            or translated_content["free_session_section_title"],
            "free_session_section_description": source_translation.free_session_section_description
            or translated_content["free_session_section_description"],
            "free_session_privacy_note": source_translation.free_session_privacy_note
            or translated_content["free_session_privacy_note"],
            "family_bundle_section_badge": source_translation.family_bundle_section_badge
            or translated_content["family_bundle_section_badge"],
            "family_bundle_section_title": source_translation.family_bundle_section_title
            or translated_content["family_bundle_section_title"],
            "family_bundle_section_description": source_translation.family_bundle_section_description
            or translated_content["family_bundle_section_description"],
            "family_bundle_section_pricing_note_1": source_translation.family_bundle_section_pricing_note_1
            or translated_content["family_bundle_section_pricing_note_1"],
            "family_bundle_section_pricing_note_2": source_translation.family_bundle_section_pricing_note_2
            or translated_content["family_bundle_section_pricing_note_2"],
            "family_bundle_section_pricing_note_3": source_translation.family_bundle_section_pricing_note_3
            or translated_content["family_bundle_section_pricing_note_3"],
            "family_bundle_section_pricing_note_4": source_translation.family_bundle_section_pricing_note_4
            or translated_content["family_bundle_section_pricing_note_4"],
            "family_bundle_plans_title": source_translation.family_bundle_plans_title
            or translated_content["family_bundle_plans_title"],
            "family_bundle_plans_description": source_translation.family_bundle_plans_description
            or translated_content["family_bundle_plans_description"],
            "family_bundle_comparison_title": source_translation.family_bundle_comparison_title
            or translated_content["family_bundle_comparison_title"],
            "family_bundle_comparison_description": source_translation.family_bundle_comparison_description
            or translated_content["family_bundle_comparison_description"],
            "family_bundle_faq_title": source_translation.family_bundle_faq_title
            or translated_content["family_bundle_faq_title"],
            "family_bundle_faq_description": source_translation.family_bundle_faq_description
            or translated_content["family_bundle_faq_description"],
            "family_bundle_cta_title": source_translation.family_bundle_cta_title
            or translated_content["family_bundle_cta_title"],
            "family_bundle_cta_description": source_translation.family_bundle_cta_description
            or translated_content["family_bundle_cta_description"],
            "family_bundle_cta_button_text": source_translation.family_bundle_cta_button_text
            or translated_content["family_bundle_cta_button_text"],
            "contact_section_title": source_translation.contact_section_title
            or translated_content["contact_section_title"],
            "contact_section_description": source_translation.contact_section_description
            or translated_content["contact_section_description"],
            "contact_info_title": source_translation.contact_info_title
            or translated_content["contact_info_title"],
            "contact_info_description": source_translation.contact_info_description
            or translated_content["contact_info_description"],
            "facebook_label": source_translation.facebook_label
            or translated_content["facebook_label"],
            "footer_description": source_translation.footer_description
            or translated_content["footer_description"],
            "footer_cta_text": source_translation.footer_cta_text
            or translated_content["footer_cta_text"],
            "footer_created_by_text": source_translation.footer_created_by_text
            or translated_content["footer_created_by_text"],
            "footer_copyright_text": source_translation.footer_copyright_text
            or translated_content["footer_copyright_text"],
        }
    )

    return translated_content


def _build_feature_item(feature, language):
    translation = HomePageFeatureTranslation.objects.filter(
        feature=feature,
        language=language,
    ).first()
    english_translation = HomePageFeatureTranslation.objects.filter(
        feature=feature,
        language="en",
    ).first()
    source_translation = translation or english_translation

    return {
        "id": feature.id,
        "section": feature.section,
        "icon_class": feature.icon_class,
        "image_url": feature.image.url if feature.image else "",
        "title": (
            source_translation.title
            if source_translation and source_translation.title
            else ""
        ),
        "description": (
            source_translation.description
            if source_translation and source_translation.description
            else ""
        ),
        "subtitle": (
            source_translation.subtitle
            if source_translation and source_translation.subtitle
            else ""
        ),
        "meta": (
            source_translation.meta
            if source_translation and source_translation.meta
            else ""
        ),
    }


def _get_features(home_page, language, section):
    features = home_page.features.filter(
        section=section,
        is_active=True,
    ).order_by("order", "id")

    return [_build_feature_item(feature, language) for feature in features]


def _build_video_point_item(video_point, language):
    translation = HomePageVideoPointTranslation.objects.filter(
        video_point=video_point,
        language=language,
    ).first()
    english_translation = HomePageVideoPointTranslation.objects.filter(
        video_point=video_point,
        language="en",
    ).first()
    source_translation = translation or english_translation

    return {
        "id": video_point.id,
        "icon_class": video_point.icon_class,
        "text": source_translation.text
        if source_translation and source_translation.text
        else "",
    }


def _get_video_points(home_page, language):
    video_points = home_page.video_points.filter(is_active=True).order_by("order", "id")
    return [
        _build_video_point_item(video_point, language) for video_point in video_points
    ]


def _get_home_page_translations(home_page):
    payload = {
        "en": _apply_home_translation(home_page, "en"),
        "ar": _apply_home_translation(home_page, "ar"),
        "primary_features": {"en": [], "ar": []},
        "secondary_features": {"en": [], "ar": []},
        "testimonials": {"en": [], "ar": []},
        "process": {"en": [], "ar": []},
        "family_bundle_plans": {"en": [], "ar": []},
        "family_bundle_comparison": {"en": [], "ar": []},
        "family_bundle_testimonials": {"en": [], "ar": []},
        "family_bundle_faq": {"en": [], "ar": []},
        "video_points": {"en": [], "ar": []},
    }

    for lang in ("en", "ar"):
        payload["primary_features"][lang] = _get_features(home_page, lang, "primary")
        payload["secondary_features"][lang] = _get_features(
            home_page, lang, "secondary"
        )
        payload["testimonials"][lang] = _get_features(home_page, lang, "testimonials")
        payload["process"][lang] = _get_features(home_page, lang, "process")
        payload["family_bundle_plans"][lang] = _get_features(
            home_page, lang, "family_bundle_plans"
        )
        payload["family_bundle_comparison"][lang] = _get_features(
            home_page, lang, "family_bundle_comparison"
        )
        payload["family_bundle_testimonials"][lang] = _get_features(
            home_page, lang, "family_bundle_testimonials"
        )
        payload["family_bundle_faq"][lang] = _get_features(
            home_page, lang, "family_bundle_faq"
        )
        payload["video_points"][lang] = _get_video_points(home_page, lang)

    return payload


def _get_teachers(language):
    teachers = TeacherInfo.objects.filter(is_active_to_be_shown_in_home=True)
    translated_teachers = []

    for teacher in teachers:
        translation = TeacherInfoTranslation.objects.filter(
            teacher_info=teacher,
            language=language,
        ).first()

        teacher_user = teacher.teacher

        translated_teachers.append(
            {
                "teacher": teacher_user,
                "name": teacher_user.name,
                "image": teacher_user.image,
                "bio": (
                    translation.translated_bio
                    if translation and translation.translated_bio
                    else teacher.bio
                ),
                "specialization": (
                    translation.translated_specialization
                    if translation and translation.translated_specialization
                    else teacher.specialization
                ),
                "profile_link": teacher.profile_link,
            }
        )

    return translated_teachers


def home(request):
    language = _get_current_language(request)
    current_year = timezone.now().year

    company_info = _get_company_info(language)
    home_page = _get_home_page_content()
    home_page_text = _apply_home_translation(home_page, language)
    home_page_translations = _get_home_page_translations(home_page)

    teachers = _get_teachers(language)

    theme = Theme.objects.filter(active=True).first()
    logo_url = theme.logo.url if theme and theme.logo else None

    context = {
        "logo_url": logo_url,
        "teachers": teachers,
        "company_info": company_info,
        "current_year": current_year,
        "home_page": home_page,
        "home_page_text": home_page_text,
        "home_page_primary_features": _get_features(home_page, language, "primary"),
        "home_page_secondary_features": _get_features(home_page, language, "secondary"),
        "home_page_testimonials": _get_features(home_page, language, "testimonials"),
        "home_page_process_steps": _get_features(home_page, language, "process"),
        "home_page_family_bundle_plans": _get_features(
            home_page, language, "family_bundle_plans"
        ),
        "home_page_family_bundle_comparison": _get_features(
            home_page, language, "family_bundle_comparison"
        ),
        "home_page_family_bundle_testimonials": _get_features(
            home_page, language, "family_bundle_testimonials"
        ),
        "home_page_family_bundle_faq": _get_features(
            home_page, language, "family_bundle_faq"
        ),
        "home_page_video_points": _get_video_points(home_page, language),
        "home_page_translations": home_page_translations,
    }
    return render(request, "about/home.html", context)


def about_us(request):
    return render(request, "about/about_us.html")


def send_email(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data["email"]
            message = form.cleaned_data["message"]
            company_info = CompanyInfo.objects.last()

            if not company_info:
                return JsonResponse(
                    {"error": "Company information is not configured."},
                    status=400,
                )

            email = EmailMessage(
                subject="HiCode Contact",
                body=message,
                from_email="platraincloud@gmail.com",
                to=[company_info.email],
                headers={"Reply-To": user_email},
            )

            email.send(fail_silently=False)
            return JsonResponse({"message": "Email sent successfully!"})

        return JsonResponse({"errors": form.errors}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)


def book_free_session(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    from about.models import FreeSession

    if hasattr(request.user, "free_session"):
        session = request.user.free_session
        if session.status == "done":
            return JsonResponse(
                {
                    "error": "already_done",
                    "message": "You have already completed your free session.",
                },
                status=400,
            )
        else:
            return JsonResponse(
                {
                    "error": "already_booked",
                    "message": "You have already booked a free session. We will contact you soon!",
                },
                status=400,
            )

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = {}

    phone = data.get("phone", "") or request.user.phone or ""
    message = data.get("message", "")

    FreeSession.objects.create(
        user=request.user,
        phone=phone,
        message=message,
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Your free session has been booked! We will contact you soon.",
        }
    )
