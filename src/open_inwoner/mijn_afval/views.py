from django.shortcuts import render

from .clients import AfvalApiClient


def afval_view(request):
    client = AfvalApiClient(base_url="")

    data = client.fetch_bag_objects_for_bsn(bsn="42")

    return render(request, "pages/mijn_afval/index.html", {"data": data})
