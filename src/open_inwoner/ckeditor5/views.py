from __future__ import unicode_literals

import hashlib

from filer.models import Folder, Image
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class ImageUploadView(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    authentication_classes = (SessionAuthentication,)
    schema = None

    def post(self, request, **kwargs):
        """
        Uploads a file and send back its URL to CKEditor.
        """
        uploaded_file = request.FILES["upload"]
        folder, created = Folder.objects.get_or_create(
            defaults={"owner": request.user},
            name="ckeditor",
        )
        sha1 = hashlib.sha1(uploaded_file.read(), usedforsecurity=False).hexdigest()

        img, created = Image.objects.get_or_create(
            defaults={
                "owner": request.user,
                "folder": folder,
                "original_filename": uploaded_file.name,
                "file": uploaded_file,
            },
            sha1=sha1,
        )
        return Response(data={"url": img.url}, status=201)
