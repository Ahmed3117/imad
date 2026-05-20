import re

DEFAULT_COUNTRY_CODE = "+20"

COUNTRY_CODE_CHOICES = (
    ("+20", "Egypt (+20)"),
    ("+966", "Saudi Arabia (+966)"),
    ("+971", "United Arab Emirates (+971)"),
    ("+974", "Qatar (+974)"),
    ("+965", "Kuwait (+965)"),
    ("+973", "Bahrain (+973)"),
    ("+968", "Oman (+968)"),
    ("+962", "Jordan (+962)"),
    ("+1", "United States / Canada (+1)"),
    ("+44", "United Kingdom (+44)"),
    ("+61", "Australia (+61)"),
    ("+49", "Germany (+49)"),
    ("+33", "France (+33)"),
    ("+90", "Turkey (+90)"),
    ("+92", "Pakistan (+92)"),
    ("+91", "India (+91)"),
    ("+62", "Indonesia (+62)"),
    ("+60", "Malaysia (+60)"),
)


def normalize_country_code(country_code):
    digits = re.sub(r"\D", "", str(country_code or DEFAULT_COUNTRY_CODE))
    return f"+{digits}" if digits else DEFAULT_COUNTRY_CODE


def normalize_phone(phone, country_code=DEFAULT_COUNTRY_CODE):
    raw_phone = str(phone or "").strip()
    if not raw_phone:
        return ""

    normalized_country_code = normalize_country_code(country_code)
    country_digits = normalized_country_code.lstrip("+")

    raw_phone = raw_phone.replace(" ", "")
    if raw_phone.startswith("00"):
        raw_phone = f"+{raw_phone[2:]}"

    if raw_phone.startswith("+"):
        digits = re.sub(r"\D", "", raw_phone)
        return f"+{digits}" if digits else ""

    digits = re.sub(r"\D", "", raw_phone)
    if not digits:
        return ""

    if digits.startswith(country_digits) and len(digits) > len(country_digits) + 5:
        return f"+{digits}"

    national_number = digits.lstrip("0")
    if not national_number:
        return ""

    return f"{normalized_country_code}{national_number}"


def phone_digits_for_url(phone, country_code=DEFAULT_COUNTRY_CODE):
    normalized = normalize_phone(phone, country_code=country_code)
    return re.sub(r"\D", "", normalized)
