from cms.extensions import PageExtensionAdmin
from django.contrib import admin

from .models import CommonExtension


class CommonExtensionAdmin(PageExtensionAdmin):
    pass


admin.site.register(CommonExtension, CommonExtensionAdmin)
