from __future__ import unicode_literals

import hashlib

from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic import View

from filer.models import Folder, Image


@require_POST
def upload_to_filer(request):
    if request.is_ajax():
        if request.user.is_authenticated:
            if request.user.is_staff:
                folder, created = Folder.objects.get_or_create(name="ckeditor")
                if created:
                    folder.owner = (
                        User.objects.filter(is_superuser=True).order_by("id").first()
                    )
                    folder.save()
                if request.FILES["image"].content_type:
                    if request.FILES["image"].content_type.split("/")[0] != "image":
                        return JsonResponse(
                            {
                                "status": "error",
                                "message": _("The uploaded file must be an image!"),
                            }
                        )
                data = request.FILES["image"].read()
                sha1 = hashlib.sha1(data).hexdigest()  # nosec
                img = Image.objects.filter(sha1=sha1).first()
                if img is None:
                    img = Image.objects.create(
                        owner=request.user,
                        folder=folder,
                        original_filename=request.FILES["image"].name,
                        file=request.FILES["image"],
                    )
                return JsonResponse({"status": "ok", "url": img.url})
            else:
                return HttpResponseForbidden("")
        else:
            return HttpResponseForbidden("")
    else:
        return HttpResponseBadRequest("")


class ImageUploadView(View):
    http_method_names = ["post"]

    def post(self, request, **kwargs):
        """
        Uploads a file and send back its URL to CKEditor.
        """
        uploaded_file = request.FILES["upload"]
        print("uploaded file=", uploaded_file)
        # todo if not image - 400 error
        folder, created = Folder.objects.get_or_create(name="ckeditor")
        sha1 = hashlib.sha1(uploaded_file.read()).hexdigest()

        img, created = Image.objects.get_or_create(
            defaults={
                "owner": request.user,
                "folder": folder,
                "original_filename": uploaded_file.name,
                "file": uploaded_file,
            },
            sha1=sha1,
        )
        return JsonResponse({"status": "ok", "url": img.url}, status=201)
