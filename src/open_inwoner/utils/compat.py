"""
Compatibility utilities for Django version differences.

Import this module early in test files that use zgw-consumers-oas or other
libraries that depend on timezone.utc.
"""

import datetime

from django.utils import timezone

# Django 5.x removed timezone.utc - add it back for zgw-consumers-oas compatibility
# This module should be imported before any code that uses timezone.utc
if not hasattr(timezone, "utc"):
    timezone.utc = datetime.timezone.utc
