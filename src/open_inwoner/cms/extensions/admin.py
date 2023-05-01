from django.contrib import admin

from cms.extensions import PageExtensionAdmin

from .models import CommonExtension


class CommonExtensionAdmin(PageExtensionAdmin):
    pass


admin.site.register(CommonExtension, CommonExtensionAdmin)
