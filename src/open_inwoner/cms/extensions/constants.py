from django.db import models
from django.utils.translation import gettext_lazy as _


class IndicatorChoices(models.TextChoices):
    plan_new_contacts = "plan_new_contacts", _("Plans > new contacts")
    inbox_new_messages = "inbox_new_messages", _("Inbox > new messages")


class Icons(models.TextChoices):
    # Note: help_outline from Material Icons requires _outline suffix for this icon's variant;
    # Whereas person/inbox/euro etc. use the standard name without a suffix
    person = "person", _("User")
    description = "description", _("Products")
    inbox = "inbox", _("Inbox")
    inventory_2 = "inventory_2", _("Cases")
    group = "group", _("Collaborate")
    help_outline = "help_outline", _("Help")
    euro = "euro", _("Benefits")
    trash = "delete", _("Afval")

    # Places & housing
    home = "home", _("Home")
    apartment = "apartment", _("Housing")
    home_work = "home_work", _("Housing (work)")
    place = "place", _("Location")

    # Work & government
    business = "business", _("Business")
    work = "work", _("Work")
    account_balance = "account_balance", _("Government")
    gavel = "gavel", _("Permits")
    assignment = "assignment", _("Forms")

    # Health & care
    medical_services = "medical_services", _("Healthcare")
    local_hospital = "local_hospital", _("Care")
    child_care = "child_care", _("Youth")
    elderly = "elderly", _("Elderly")
    accessible = "accessible", _("Accessibility")

    # Education
    school = "school", _("Education")

    # Environment & animals
    park = "park", _("Environment")
    recycling = "recycling", _("Recycling")
    pets = "pets", _("Pets")

    # Traffic
    directions_car = "directions_car", _("Traffic")
    local_parking = "local_parking", _("Parking")

    # Safety
    security = "security", _("Safety")
    warning = "warning", _("Warning")

    # Finance
    payments = "payments", _("Payments")
    credit_card = "credit_card", _("Finance")
    savings = "savings", _("Savings")
    receipt = "receipt", _("Invoices")

    # Community & contact
    groups = "groups", _("Community")
    forum = "forum", _("Forum")
    chat = "chat", _("Chat")
    mail = "mail", _("Mail")
    phone = "phone", _("Contact")
    support_agent = "support_agent", _("Support")

    # Content & information
    campaign = "campaign", _("News")
    event = "event", _("Events")
    calendar_today = "calendar_today", _("Calendar")
    article = "article", _("Documents")
    folder = "folder", _("Files")
    quiz = "quiz", _("FAQ")
    info = "info", _("Information")
    language = "language", _("Language")

    # Interface
    notifications = "notifications", _("Notifications")
    search = "search", _("Search")
    settings = "settings", _("Settings")
    favorite = "favorite", _("Favorites")
    build = "build", _("Maintenance")
