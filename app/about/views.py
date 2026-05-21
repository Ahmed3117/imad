import json
import uuid

from accounts.models import TeacherInfo, TeacherInfoTranslation
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from services.email_service import (
    EmailConfigurationError,
    EmailRateLimitError,
    send_contact_email,
)
from project.phone_utils import normalize_phone

from .meta_capi import send_lead_event, send_contact_event

from about.models import (
    CompanyInfo,
    CompanyInfoTranslation,
    HomePageContent,
    HomePageContentTranslation,
    HomePageFeatureTranslation,
    HomePageVideoPointTranslation,
    LegalPage,
    LegalPageTranslation,
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

    company_info.email = getattr(settings, "CONTACT_EMAIL_TO", company_info.email)

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

    # Logo URL previously came from admin_interface Theme.
    # After UNFOLD migration, templates fall back to static logo.
    logo_url = None

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
            contact_data = form.cleaned_data.copy()
            contact_data["phone"] = normalize_phone(
                contact_data.get("phone"),
                contact_data.get("phone_country_code"),
            )
            user_email = contact_data["email"]
            from about.models import ContactMessage
            ContactMessage.objects.create(
                name=contact_data["name"],
                email=user_email,
                phone=contact_data.get("phone", "") or "",
                telegram_username=contact_data.get("telegram_username", "") or "",
                message=contact_data["message"],
            )
            try:
                send_contact_email(request, contact_data)
            except EmailRateLimitError as e:
                return JsonResponse(
                    {
                        "error": f"Too many contact requests. Try again in {e.retry_after} seconds."
                    },
                    status=429,
                )
            except EmailConfigurationError:
                return JsonResponse({"error": "Email service is not configured."}, status=500)
            except Exception:
                return JsonResponse({"error": "Could not send email."}, status=502)

            # Fire server-side Contact event via Meta Conversions API
            send_contact_event(request, email=user_email)

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

    phone = (
        normalize_phone(data.get("phone", ""), data.get("phone_country_code"))
        or normalize_phone(request.user.phone)
    )
    telegram_username = data.get("telegram_username", "") or getattr(request.user, "telegram_username", "") or ""
    message = data.get("message", "")

    FreeSession.objects.create(
        user=request.user,
        phone=phone,
        telegram_username=telegram_username,
        message=message,
    )
    if telegram_username and not getattr(request.user, "telegram_username", None):
        request.user.telegram_username = telegram_username
        request.user.save(update_fields=["telegram_username"])

    # Fire server-side Lead event via Meta Conversions API
    # (best-effort; must never break the booking flow)
    try:
        send_lead_event(
            request,
            email=getattr(request.user, "email", ""),
            phone=phone,
        )
    except Exception:
        pass

    return JsonResponse(
        {
            "success": True,
            "message": "Your free session has been booked! We will contact you soon.",
        }
    )


# ─────────────────────────────────────────────
# Legal Pages Views
# ─────────────────────────────────────────────

DEFAULT_LEGAL_CONTENT = {
    "en": {
        "privacy": """
<h2>1. Introduction</h2>
<p>Welcome to Nabbiuwny. We respect your privacy and are committed to protecting your personal data. This Privacy Policy explains how we collect, use, store, and safeguard your information when you use our website and mobile application.</p>

<h2>2. Information We Collect</h2>
<p><strong>Personal Information:</strong> When you register, we collect your name, email address, phone number, and Telegram username. This information is necessary to create your account and match you with the right teacher.</p>
<p><strong>Payment Information:</strong> We collect billing details and payment method information through our secure payment processors. We do not store full credit card numbers on our servers.</p>
<p><strong>Usage Data:</strong> We collect information about how you interact with our platform, including class attendance, lecture progress, and assignment submissions.</p>
<p><strong>Device Information:</strong> We may collect device type, operating system, and IP address to improve our services and ensure security.</p>

<h2>3. How We Use Your Information</h2>
<p>We use your personal data to:</p>
<ul>
<li>Create and manage your account</li>
<li>Match students with appropriate teachers</li>
<li>Process payments and manage subscriptions</li>
<li>Send class reminders and platform notifications</li>
<li>Improve our teaching quality and user experience</li>
<li>Comply with legal obligations</li>
</ul>

<h2>4. Data Sharing and Disclosure</h2>
<p>We do not sell your personal data to third parties. We may share your information with:</p>
<ul>
<li><strong>Teachers:</strong> To facilitate Quran classes and communication</li>
<li><strong>Payment Processors:</strong> To securely handle transactions</li>
<li><strong>Service Providers:</strong> Trusted partners who assist in operating our platform (e.g., hosting, analytics)</li>
<li><strong>Legal Authorities:</strong> When required by law or to protect our rights</li>
</ul>

<h2>5. Data Security</h2>
<p>We implement industry-standard security measures including SSL encryption, secure data storage, and regular security audits. Access to personal data is restricted to authorized personnel only.</p>

<h2>6. Data Retention</h2>
<p>We retain your personal data for as long as your account is active or as needed to provide you with our services. You may request deletion of your account and associated data at any time through your profile settings or by contacting us.</p>

<h2>7. Your Rights</h2>
<p>You have the right to:</p>
<ul>
<li>Access the personal data we hold about you</li>
<li>Correct inaccurate or incomplete data</li>
<li>Request deletion of your personal data</li>
<li>Withdraw consent for data processing</li>
<li>Receive a copy of your data in a portable format</li>
</ul>

<h2>8. Children's Privacy</h2>
<p>Nabbiuwny provides educational services to children under parental supervision. Parents or legal guardians manage student accounts and are responsible for the information provided. We do not knowingly collect data from children under 13 without verifiable parental consent.</p>

<h2>9. Cookies and Tracking</h2>
<p>We use cookies and similar technologies to enhance your browsing experience, remember your preferences, and analyze site traffic. You can manage cookie preferences through your browser settings.</p>

<h2>10. Changes to This Policy</h2>
<p>We may update this Privacy Policy periodically. We will notify you of significant changes via email or through the platform. The "Last Updated" date at the top of this page indicates when the policy was last revised.</p>

<h2>11. Contact Us</h2>
<p>If you have any questions about this Privacy Policy or our data practices, please contact us at contact@nabbiuwny.com or through our Contact page.</p>
""",
        "terms": """
<h2>1. Acceptance of Terms</h2>
<p>By accessing or using the Nabbiuwny platform, you agree to be bound by these Terms & Conditions. If you do not agree to these terms, please do not use our services. These terms apply to all users, including students, parents, teachers, and administrators.</p>

<h2>2. Service Description</h2>
<p>Nabbiuwny is an online Quran learning platform that connects students with certified teachers for one-on-one and group Quran classes. We provide scheduling, video conferencing integration, progress tracking, and educational resource management.</p>

<h2>3. Account Registration</h2>
<p>To use our services, you must create an accurate and complete account. You are responsible for maintaining the confidentiality of your login credentials and for all activities that occur under your account. You must be at least 18 years old to register a parent/teacher account, or have parental consent for a student account.</p>

<h2>4. User Conduct</h2>
<p>You agree to use the platform responsibly and respectfully. Prohibited activities include:</p>
<ul>
<li>Sharing inappropriate or offensive content during classes</li>
<li>Recording or distributing class sessions without consent</li>
<li>Harassing teachers, students, or staff</li>
<li>Attempting to access unauthorized areas of the platform</li>
<li>Using the platform for any illegal purpose</li>
</ul>

<h2>5. Class Scheduling and Attendance</h2>
<p>Classes are scheduled based on the agreed-upon times between teachers and students. We expect punctuality and advance notice for cancellations. Repeated no-shows may result in forfeiture of that session. Teachers may mark attendance and provide progress notes after each session.</p>

<h2>6. Teacher-Student Relationship</h2>
<p>Teachers on our platform are independent contractors. Nabbiuwny facilitates the connection but is not directly responsible for individual teaching methods or outcomes. We carefully vet all teachers to ensure quality and appropriate conduct.</p>

<h2>7. Intellectual Property</h2>
<p>All content provided on the platform, including curriculum materials, videos, and software, is the property of Nabbiuwny or its licensors. You may not reproduce, distribute, or create derivative works without our express permission. User-generated content remains the property of the user but grants us a license to use it for platform operation.</p>

<h2>8. Payment and Subscriptions</h2>
<p>Fees for classes and subscriptions are clearly displayed before purchase. By making a payment, you agree to the pricing and billing terms. Subscription plans auto-renew unless canceled before the renewal date. Prices are subject to change with prior notice.</p>

<h2>9. Termination</h2>
<p>We reserve the right to suspend or terminate your account for violations of these terms, fraudulent activity, or behavior that endangers our community. You may also request account deletion at any time through your profile settings.</p>

<h2>10. Limitation of Liability</h2>
<p>Nabbiuwny provides its services "as is" without warranties of any kind. We are not liable for indirect, incidental, or consequential damages arising from your use of the platform. Our total liability shall not exceed the amount you paid for services in the preceding 12 months.</p>

<h2>11. Governing Law</h2>
<p>These Terms shall be governed by the laws of the Arab Republic of Egypt. Any disputes shall be resolved through good-faith negotiation, and if necessary, through the courts of Cairo.</p>

<h2>12. Changes to Terms</h2>
<p>We may modify these Terms at any time. Continued use of the platform after changes constitutes acceptance of the updated Terms. We will notify users of material changes via email or platform notifications.</p>
""",
        "refund": """
<h2>1. Free Trial Policy</h2>
<p>Every new student is entitled to one free trial class. No payment information is required to book the trial. The trial class is designed to help you evaluate our teaching quality before committing to a paid plan.</p>

<h2>2. Money-Back Guarantee</h2>
<p>If you are not satisfied after your first week of paid classes, you may request a full refund within 7 days of your first paid session. This guarantee applies to the first subscription period only.</p>

<h2>3. Subscription Cancellations</h2>
<p>You may cancel your subscription at any time through your account settings. Cancellations take effect at the end of the current billing period. You will retain access to your classes until the end of the paid period.</p>

<h2>4. Refund Eligibility</h2>
<p>Refunds may be granted in the following circumstances:</p>
<ul>
<li>Technical failures preventing class delivery (platform-side issues)</li>
<li>Teacher unavailability after confirmed booking</li>
<li>Service interruptions lasting more than 48 hours due to our infrastructure</li>
<li>Accidental duplicate charges</li>
</ul>

<h2>5. Non-Refundable Situations</h2>
<p>Refunds will not be issued for:</p>
<ul>
<li>Classes missed due to student absence or late cancellation (less than 24 hours notice)</li>
<li>Partial completion of a subscription period (except under the 7-day guarantee)</li>
<li>Classes completed but deemed unsatisfactory after multiple sessions</li>
<li>Issues caused by the user's internet connection or device</li>
</ul>

<h2>6. Refund Process</h2>
<p>To request a refund, contact our support team at contact@nabbiuwny.com with your order details and reason for the request. We aim to process refund decisions within 5 business days. Approved refunds are processed to the original payment method within 10-14 business days.</p>

<h2>7. Family Bundle Refunds</h2>
<p>Family bundle subscriptions follow the same refund policy. If any child in the bundle is dissatisfied within the first week, the entire bundle may be refunded. Partial family bundle refunds are not available after the guarantee period.</p>
""",
        "cookie": """
<h2>1. What Are Cookies</h2>
<p>Cookies are small text files stored on your device when you visit a website. They help the site remember your preferences, login status, and improve your browsing experience.</p>

<h2>2. How We Use Cookies</h2>
<p>Nabbiuwny uses cookies for the following purposes:</p>
<ul>
<li><strong>Essential Cookies:</strong> Required for the platform to function, including authentication and session management</li>
<li><strong>Preference Cookies:</strong> Remember your language selection, display preferences, and notification settings</li>
<li><strong>Analytics Cookies:</strong> Help us understand how users interact with our platform so we can improve it</li>
<li><strong>Security Cookies:</strong> Protect your account from unauthorized access and detect suspicious activity</li>
</ul>

<h2>3. Third-Party Cookies</h2>
<p>We may allow trusted third-party services to place cookies for analytics (e.g., understanding site traffic) and payment processing. These cookies are governed by the third parties' respective privacy policies.</p>

<h2>4. Managing Cookies</h2>
<p>You can control cookies through your browser settings. Most browsers allow you to block or delete cookies. Please note that disabling essential cookies may prevent you from using certain features of our platform, such as staying logged in.</p>

<h2>5. Consent</h2>
<p>By continuing to use our website and mobile application, you consent to our use of cookies as described in this policy. You may withdraw consent at any time by adjusting your browser settings, though this may affect functionality.</p>
""",
        "payment": """
<h2>1. Accepted Payment Methods</h2>
<p>Nabbiuwny accepts payments through major credit cards, debit cards, and digital payment methods available in your region. All transactions are processed through PCI-DSS compliant payment gateways.</p>

<h2>2. Subscription Plans</h2>
<p>We offer flexible subscription plans for individual students and family bundles. Plan details, pricing, and inclusions are clearly displayed before purchase. By subscribing, you authorize us to charge your payment method on a recurring basis.</p>

<h2>3. Billing Cycle</h2>
<p>Subscriptions are billed in advance on a monthly basis. Your billing date is determined by your initial subscription date. You will receive an email receipt for each successful payment.</p>

<h2>4. Auto-Renewal</h2>
<p>All subscriptions automatically renew at the end of each billing period unless you cancel before the renewal date. You can manage or cancel your subscription at any time from your account settings.</p>

<h2>5. Failed Payments</h2>
<p>If a payment fails, we will notify you and attempt to process the payment again. If payment continues to fail, your subscription may be suspended until the outstanding balance is resolved.</p>

<h2>6. Price Changes</h2>
<p>We may adjust subscription prices with at least 30 days' advance notice. Price changes will take effect on your next billing cycle after the notice period. You may cancel before the price change takes effect if you do not agree to the new pricing.</p>

<h2>7. Taxes</h2>
<p>All prices displayed are inclusive of applicable taxes unless otherwise stated. You are responsible for any additional taxes or duties imposed by your jurisdiction.</p>

<h2>8. Secure Transactions</h2>
<p>All payment information is encrypted using industry-standard SSL/TLS technology. We do not store complete credit card details on our servers. Payment processing is handled by certified, secure third-party providers.</p>

<h2>9. Dispute Resolution</h2>
<p>If you believe you have been incorrectly charged, please contact us immediately at contact@nabbiuwny.com. We will investigate and resolve billing disputes promptly. Chargebacks should only be initiated after attempting to resolve the issue with our support team.</p>
""",
    },
    "ar": {
        "privacy": """
<h2>1. مقدمة</h2>
<p>مرحبًا بك في نبـيـونـي. نحن نحترم خصوصيتك وملتزمون بحماية بياناتك الشخصية. توضح سياسة الخصوصية هذه كيفية جمعنا واستخدامنا وتخزيننا وحماية معلوماتك عند استخدامك لموقعنا وتطبيقنا.</p>

<h2>2. المعلومات التي نجمعها</h2>
<p><strong>المعلومات الشخصية:</strong> عند التسجيل، نجمع اسمك وعنوان بريدك الإلكتروني ورقم هاتفك واسم مستخدم تيليجرام. هذه المعلومات ضرورية لإنشاء حسابك ومطابقته مع المعلم المناسب.</p>
<p><strong>معلومات الدفع:</strong> نجمع تفاصيل الفوترة ومعلومات طريقة الدفع من خلال معالجات الدفع الآمنة لدينا. لا نقوم بتخزين أرقام بطاقات الائتمان الكاملة على خوادمنا.</p>
<p><strong>بيانات الاستخدام:</strong> نجمع معلومات حول كيفية تفاعلك مع منصتنا، بما في ذلك حضور الحصص وتقدم المحاضرات وتسليم الواجبات.</p>
<p><strong>معلومات الجهاز:</strong> قد نجمع نوع الجهاز ونظام التشغيل وعنوان IP لتحسين خدماتنا وضمان الأمان.</p>

<h2>3. كيف نستخدم معلوماتك</h2>
<p>نستخدم بياناتك الشخصية من أجل:</p>
<ul>
<li>إنشاء حسابك وإدارته</li>
<li>مطابقة الطلاب مع المعلمين المناسبين</li>
<li>معالجة المدفوعات وإدارة الاشتراكات</li>
<li>إرسال تذكيرات بالحصص وإشعارات المنصة</li>
<li>تحسين جودة التدريس وتجربة المستخدم</li>
<li>الامتثال للالتزامات القانونية</li>
</ul>

<h2>4. مشاركة البيانات والإفصاح</h2>
<p>لا نقوم ببيع بياناتك الشخصية لأطراف ثالثة. قد نشارك معلوماتك مع:</p>
<ul>
<li><strong>المعلمين:</strong> لتسهيل حصص القرآن والتواصل</li>
<li><strong>معالجي الدفع:</strong> لمعالجة المعاملات بشكل آمن</li>
<li><strong>مزودي الخدمات:</strong> شركاء موثوقين يساعدون في تشغيل منصتنا (مثل الاستضافة والتحليلات)</li>
<li><strong>السلطات القانونية:</strong> عندما يقتضي القانون ذلك أو لحماية حقوقنا</li>
</ul>

<h2>5. أمان البيانات</h2>
<p>ننفذ تدابير أمان على مستوى الصناعة تشمل تشفير SSL وتخزين البيانات الآمن والتدقيق الأمني المنتظم. يقتصر الوصول إلى البيانات الشخصية على الموظفين المصرح لهم فقط.</p>

<h2>6. الاحتفاظ بالبيانات</h2>
<p>نحتفظ ببياناتك الشخصية طالما كان حسابك نشطًا أو حسب الحاجة لتزويدك بخدماتنا. يمكنك طلب حذف حسابك والبيانات المرتبطة به في أي وقت من خلال إعدادات ملفك الشخصي أو بالتواصل معنا.</p>

<h2>7. حقوقك</h2>
<p>لديك الحق في:</p>
<ul>
<li>الوصول إلى البيانات الشخصية التي نحتفظ بها عنك</li>
<li>تصحيح البيانات غير الدقيقة أو غير المكتملة</li>
<li>طلب حذف بياناتك الشخصية</li>
<li>سحب الموافقة على معالجة البيانات</li>
<li>تلقي نسخة من بياناتك بتنسيق محمول</li>
</ul>

<h2>8. خصوصية الأطفال</h2>
<p>تقدم نبـيـونـي خدمات تعليمية للأطفال تحت إشراف الوالدين. يدير الوالدون أو الأوصياء القانونيون حسابات الطلاب ويتحملون المسؤولية عن المعلومات المقدمة. لا نقوم عن قصد بجمع بيانات من أطفال دون 13 عامًا دون موافقة أبوية يمكن التحقق منها.</p>

<h2>9. ملفات تعريف الارتباط والتتبع</h2>
<p>نستخدم ملفات تعريف الارتباط والتقنيات المشابهة لتحسين تجربة التصفح وتذكر تفضيلاتك وتحليل حركة المرور على الموقع. يمكنك إدارة تفضيلات ملفات تعريف الارتباط من خلال إعدادات متصفحك.</p>

<h2>10. التغييرات على هذه السياسة</h2>
<p>قد نقوم بتحديث سياسة الخصوصية هذه دوريًا. سنقوم بإخطارك بالتغييرات المهمة عبر البريد الإلكتروني أو من خلال المنصة. يشير تاريخ "آخر تحديث" أعلى هذه الصفحة إلى متى تمت مراجعة السياسة آخر مرة.</p>

<h2>11. تواصل معنا</h2>
<p>إذا كانت لديك أي أسئلة حول سياسة الخصوصية هذه أو ممارساتنا المتعلقة بالبيانات، يرجى التواصل معنا على contact@nabbiuwny.com أو من خلال صفحة التواصل.</p>
""",
        "terms": """
<h2>1. قبول الشروط</h2>
<p>باستخدامك منصة نبـيـونـي أو الوصول إليها، فإنك توافق على الالتزام بهذه الشروط والأحكام. إذا كنت لا توافق على هذه الشروط، يرجى عدم استخدام خدماتنا. تنطبق هذه الشروط على جميع المستخدمين، بما في ذلك الطلاب والوالدين والمعلمين والمسؤولين.</p>

<h2>2. وصف الخدمة</h2>
<p>نبـيـونـي هي منصة تعليمية عبر الإنترنت لتعليم القرآن تربط بين الطلاب والمعلمين المعتمدين للحصص الفردية والجماعية. نقدم الجدولة والتكامل مع مؤتمرات الفيديو وتتبع التقدم وإدارة الموارد التعليمية.</p>

<h2>3. تسجيل الحساب</h2>
<p>لاستخدام خدماتنا، يجب عليك إنشاء حساب دقيق وكامل. أنت مسؤول عن الحفاظ على سرية بيانات تسجيل الدخول الخاصة بك وعن جميع الأنشطة التي تحدث ضمن حسابك. يجب أن يكون عمرك 18 عامًا على الأقل لتسجيل حساب ولي/معلم، أو الحصول على موافقة الوالدين لحساب الطالب.</p>

<h2>4. سلوك المستخدم</h2>
<p>توافق على استخدام المنصة بمسؤولية واحترام. تشمل الأنشطة المحظورة:</p>
<ul>
<li>مشاركة محتوى غير لائق أو مهين أثناء الحصص</li>
<li>تسجيل الحصص أو توزيعها دون موافقة</li>
<li>التحرش بالمعلمين أو الطلاب أو الموظفين</li>
<li>محاولة الوصول إلى مناطق غير مصرح بها في المنصة</li>
<li>استخدام المنصة لأي غرض غير قانوني</li>
</ul>

<h2>5. جدولة الحصص والحضور</h2>
<p>يتم جدولة الحصص بناءً على الأوقات المتفق عليها بين المعلمين والطلاب. نتوقع الانضباط في المواعيد والإشعار المسبق عند الإلغاء. قد يؤدي التخلف المتكرر عن الحضور إلى فقدان الحصة. يجوز للمعلمين تسجيل الحضور وتقديم ملاحظات التقدم بعد كل حصة.</p>

<h2>6. العلاقة بين المعلم والطالب</h2>
<p>المعلمون على منصتنا هم متعاقدون مستقلون. تسهل نبـيـونـي الربط ولكنها ليست مسؤولة مباشرة عن طرق التدريس الفردية أو النتائج. نقوم بفحص جميع المعلمين بعناية لضمان الجودة والسلوك اللائق.</p>

<h2>7. الملكية الفكرية</h2>
<p>جميع المحتويات المقدمة على المنصة، بما في ذلك مواد المنهج الدراسي ومقاطع الفيديو والبرمجيات، هي ملك لنبـيـونـي أو مرخصيها. لا يجوز لك إعادة إنتاجها أو توزيعها أو إنشاء أعمال مشتقة دون إذننا الصريح. يظل المحتوى الذي ينشئه المستخدم ملكًا للمستخدم ولكنه يمنحنا ترخيصًا لاستخدامه في تشغيل المنصة.</p>

<h2>8. الدفع والاشتراكات</h2>
<p>يتم عرض رسوم الحصص والاشتراكات بوضوح قبل الشراء. من خلال إجراء الدفع، فإنك توافق على شروط التسعير والفوترة. يتم تجديد خطط الاشتراك تلقائيًا ما لم يتم الإلغاء قبل تاريخ التجديد. تخضر الأسعار للتغيير مع إشعار مسبق.</p>

<h2>9. إنهاء الحساب</h2>
<p>نحتفظ بالحق في تعليق أو إنهاء حسابك في حالة انتهاك هذه الشروط أو النشاط الاحتيالي أو السلوك الذي يعرض مجتمعنا للخطر. يمكنك أيضًا طلب حذف حسابك في أي وقت من خلال إعدادات ملفك الشخصي.</p>

<h2>10. تحديد المسؤولية</h2>
<p>تقدم نبـيـونـي خدماتها "كما هي" دون ضمانات من أي نوع. نحن لسنا مسؤولين عن الأضرار غير المباشرة أو العرضية أو التبعية الناشئة عن استخدامك للمنصة. لا تتجاوز مسؤوليتنا الإجمالية المبلغ الذي دفعته مقابل الخدمات خلال الأشهر الـ 12 السابقة.</p>

<h2>11. القانون الحاكم</h2>
<p>تخضع هذه الشروط لقوانون جمهورية مصر العربية. يتم تسوية أي نزاعات من خلال التفاوض بحسن نية، وإذا لزم الأمر، من خلال محاكم القاهرة.</p>

<h2>12. التغييرات على الشروط</h2>
<p>يجوز لنا تعديل هذه الشروط في أي وقت. يشكل الاستخدام المستمر للمنصة بعد التغييرات قبولًا للشروط المحدثة. سنقوم بإخطار المستخدمين بالتغييرات الجوهرية عبر البريد الإلكتروني أو إشعارات المنصة.</p>
""",
        "refund": """
<h2>1. سياسة الحصص التجريبية المجانية</h2>
<p>يحق لكل طالب جديد الحصول على حصة تجريبية مجانية واحدة. لا يلزم تقديم معلومات دفع لحجز التجربة. تم تصميم الحصة التجريبية لمساعدتك في تقييم جودة تدريسنا قبل الالتزام بخطة مدفوعة.</p>

<h2>2. ضمان استرداد الأموال</h2>
<p>إذا لم تكن راضيًا بعد أول أسبوع من الحصص المدفوعة، يمكنك طلب استرداد كامل خلال 7 أيام من أول حصة مدفوعة. ينطبق هذا الضمان على فترة الاشتراك الأولى فقط.</p>

<h2>3. إلغاء الاشتراكات</h2>
<p>يمكنك إلغاء اشتراكك في أي وقت من خلال إعدادات حسابك. تسري عمليات الإلغاء في نهاية فترة الفوترة الحالية. ستبقى لديك حق الوصول إلى حصصك حتى نهاية الفترة المدفوعة.</p>

<h2>4. أهلية الاسترداد</h2>
<p>يجوز منح المبالغ المستردة في الحالات التالية:</p>
<ul>
<li>الأعطال التقنية التي تمنع تقديم الحصة (مشاكل من جانب المنصة)</li>
<li>عدم توفر المعلم بعد الحجز المؤكد</li>
<li>انقطاع الخدمة لأكثر من 48 ساعة بسبب بنيتنا التحتية</li>
<li>الرسوم المكررة بالخطأ</li>
</ul>

<h2>5. الحالات غير القابلة للاسترداد</h2>
<p>لن يتم إصدار المبالغ المستردة في الحالات التالية:</p>
<ul>
<li>الحصص التي تفوت بسبب غياب الطالب أو الإلغاء المتأخر (أقل من 24 ساعة إشعار)</li>
<li>إكمال جزء من فترة الاشتراك (باستثناء ضمان الـ 7 أيام)</li>
<li>الحصص المكتملة ولكنها تعتبر غير مرضية بعد عدة حصص</li>
<li>المشاكل الناشئة عن اتصال الإنترنت أو جهاز المستخدم</li>
</ul>

<h2>6. عملية الاسترداد</h2>
<p>لطلب استرداد، يرجى التواصل مع فريق الدعم لدينا على contact@nabbiuwny.com مع تفاصيل طلبك وسبب الطلب. نهدف إلى معالجة قرارات الاسترداد خلال 5 أيام عمل. يتم معالجة المبالغ المستردة المعتمدة إلى طريقة الدفع الأصلية خلال 10-14 يوم عمل.</p>

<h2>7. استردادات الباقة العائلية</h2>
<p>تتبع اشتراكات الباقة العائلية نفس سياسة الاسترداد. إذا كان أي طفل في الباقة غير راضٍ خلال الأسبوع الأول، يجوز استرداد تكلفة الباقة بالكامل. لا تتوفر استردادات جزئية للباقة العائلية بعد فترة الضمان.</p>
""",
        "cookie": """
<h2>1. ما هي ملفات تعريف الارتباط</h2>
<p>ملفات تعريف الارتباط هي ملفات نصية صغيرة تُخزن على جهازك عند زيارة موقع ويب. إنها تساعد الموقع على تذكر تفضيلاتك وحالة تسجيل الدخول وتحسين تجربة التصفح.</p>

<h2>2. كيف نستخدم ملفات تعريف الارتباط</h2>
<p>تستخدم نبـيـونـي ملفات تعريف الارتباط للأغراض التالية:</p>
<ul>
<li><strong>ملفات تعريف الارتباط الأساسية:</strong> مطلوبة لعمل المنصة، بما في ذلك المصادقة وإدارة الجلسات</li>
<li><strong>ملفات تفضيل الارتباط:</strong> تذكر اختيار اللغة وتفضيلات العرض وإعدادات الإشعارات</li>
<li><strong>ملفات تحليل الارتباط:</strong> تساعدنا في فهم كيفية تفاعل المستخدمين مع منصتنا حتى نتمكن من تحسينها</li>
<li><strong>ملفات أمان الارتباط:</strong> تحمي حسابك من الوصول غير المصرح به وكشف النشاط المشبوه</li>
</ul>

<h2>3. ملفات تعريف الارتباط الخاصة بالأطراف الثالثة</h2>
<p>قد نسمح لخدمات الأطراف الثالثة الموثوقة بوضع ملفات تعريف الارتباط لأغراض التحليلات (مثل فهم حركة المرور على الموقع) ومعالجة الدفع. تحكم هذه الملفات سياسات الخصوصية الخاصة بالأطراف الثالثة المعنية.</p>

<h2>4. إدارة ملفات تعريف الارتباط</h2>
<p>يمكنك التحكم في ملفات تعريف الارتباط من خلال إعدادات متصفحك. تسمح معظم المتصفحات لك بحظر أو حذف ملفات تعريف الارتباط. يرجى ملاحظة أن تعطيل ملفات تعريف الارتباط الأساسية قد يمنعك من استخدام بعض ميزات منصتنا، مثل البقاء متصلًا.</p>

<h2>5. الموافقة</h2>
<p>باستمرارك في استخدام موقعنا وتطبيقنا المحمول، فإنك توافق على استخدامنا لملفات تعريف الارتباط كما هو موضح في هذه السياسة. يمكنك سحب الموافقة في أي وقت عن طريق تعديل إعدادات متصفحك، على الرغم من أن هذا قد يؤثر على الوظائف.</p>
""",
        "payment": """
<h2>1. طرق الدفع المقبولة</h2>
<p>تقبل نبـيـونـي المدفوعات من خلال بطاقات الائتمان الرئيسية وبطاقات الخصم وطرق الدفع الرقمية المتوفرة في منطقتك. تتم معالجة جميع المعاملات من خلال بوابات دفع متوافقة مع معايير PCI-DSS.</p>

<h2>2. خطط الاشتراك</h2>
<p>نقدم خطط اشتراك مرنة للطلاب الأفراد والباقات العائلية. يتم عرض تفاصيل الخطة والتسعير والشروclusions بوضوح قبل الشراء. من خلال الاشتراك، فإنك تفوضنا بتحصيل رسوم من طريقة الدفع الخاصة بك بشكل متكرر.</p>

<h2>3. دورة الفوترة</h2>
<p>يتم تحصيل رسوم الاشتراكات مقدمًا على أساس شهري. يتم تحديد تاريخ فوترتك بناءً على تاريخ اشتراكك الأولي. ستتلقى إيصالًا عبر البريد الإلكتروني لكل عملية دفع ناجحة.</p>

<h2>4. التجديد التلقائي</h2>
<p>يتم تجديد جميع الاشتراكات تلقائيًا في نهاية كل فترة فوترة ما لم تقم بالإلغاء قبل تاريخ التجديد. يمكنك إدارة اشتراكك أو إلغائه في أي وقت من إعدادات حسابك.</p>

<h2>5. المدفوعات الفاشلة</h2>
<p>إذا فشلت عملية الدفع، فسنقوم بإخطارك ومحاولة معالجة الدفع مرة أخرى. إذا استمر فشل الدفع، فقد يتم تعليق اشتراكك حتى يتم تسوية الرصيد المستحق.</p>

<h2>6. تغييرات الأسعار</h2>
<p>يجوز لنا تعديل أسعار الاشتراك مع إشعار مسبق لمدة 30 يومًا على الأقل. تسري تغييرات الأسعار في دورة الفوترة التالية بعد فترة الإشعار. يمكنك الإلغاء قبل دخول تغيير السعر حيز التنفيذ إذا كنت لا توافق على التسعير الجديد.</p>

<h2>7. الضرائب</h2>
<p>جميع الأسعار المعروضة شاملة للضرائب المطبقة ما لم يُذكر خلاف ذلك. أنت مسؤول عن أي ضرائب أو رسوم إضافية تفرضها سلطة ولايتك.</p>

<h2>8. المعاملات الآمنة</h2>
<p>يتم تشفير جميع معلومات الدفع باستخدام تقنية SSL/TLS القياسية في الصناعة. لا نقوم بتخزين تفاصيل بطاقات الائتمان الكاملة على خوادمنا. تتم معالجة المدفوعات من قبل مزودين معتمدين وآمنين من الأطراف الثالثة.</p>

<h2>9. تسوية النزاعات</h2>
<p>إذا كنت تعتقد أنه تم تحصيل رسوم منك بشكل غير صحيح، يرجى التواصل معنا فورًا على contact@nabbiuwny.com. سنحقق في نزاعات الفوترة وحلها على الفور. يجب أن تتم عمليات الاسترجاع (chargebacks) فقط بعد محاولة حل المشكلة مع فريق الدعم لدينا.</p>
""",
    },
}


def _get_legal_page(page_type, language):
    """Fetch legal page content, falling back to default if none exists."""
    page = LegalPage.objects.filter(page_type=page_type, is_active=True).first()
    lang_defaults = DEFAULT_LEGAL_CONTENT.get(language, DEFAULT_LEGAL_CONTENT["en"])

    if not page:
        content = lang_defaults.get(page_type, "")
        title = dict(LegalPage.PAGE_TYPE_CHOICES).get(page_type, page_type.replace("-", " ").title())
        return {"title": title, "content": content, "last_updated": None}

    translation = LegalPageTranslation.objects.filter(
        legal_page=page, language=language
    ).first()

    if translation and translation.translated_content:
        content = translation.translated_content
    else:
        # Fall back to base content (usually English), then language defaults
        content = page.content or lang_defaults.get(page_type, "")

    return {
        "title": page.get_page_type_display(),
        "content": content,
        "last_updated": page.last_updated,
    }


def privacy_policy(request):
    language = _get_current_language(request)
    page_data = _get_legal_page("privacy", language)
    return render(request, "about/legal_page.html", {
        "page": page_data,
        "page_type": "privacy",
        "translation_folder": "legal",
    })


def terms_conditions(request):
    language = _get_current_language(request)
    page_data = _get_legal_page("terms", language)
    return render(request, "about/legal_page.html", {
        "page": page_data,
        "page_type": "terms",
        "translation_folder": "legal",
    })


def refund_policy(request):
    language = _get_current_language(request)
    page_data = _get_legal_page("refund", language)
    return render(request, "about/legal_page.html", {
        "page": page_data,
        "page_type": "refund",
        "translation_folder": "legal",
    })


def cookie_policy(request):
    language = _get_current_language(request)
    page_data = _get_legal_page("cookie", language)
    return render(request, "about/legal_page.html", {
        "page": page_data,
        "page_type": "cookie",
        "translation_folder": "legal",
    })


def payment_terms(request):
    language = _get_current_language(request)
    page_data = _get_legal_page("payment", language)
    return render(request, "about/legal_page.html", {
        "page": page_data,
        "page_type": "payment",
        "translation_folder": "legal",
    })
