"""
Utility for performing find/replace operations on URL fields in ZGW models.
"""

from .models import (
    CatalogusConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeResultaatTypeConfig,
    ZaakTypeStatusTypeConfig,
)


def replace_urls_in_zgw_models(old_url: str, new_url: str) -> int:
    count = 0
    # CatalogusConfig
    for config in CatalogusConfig.objects.all():
        if old_url in config.url:
            config.url = config.url.replace(old_url, new_url)
            config.save()
            count += 1
    # ZaakTypeConfig
    for config in ZaakTypeConfig.objects.all():
        updated = False
        new_urls = []
        for url in config.urls:
            if old_url in url:
                new_urls.append(url.replace(old_url, new_url))
                updated = True
            else:
                new_urls.append(url)
        if updated:
            config.urls = new_urls
            config.save()
            count += 1
    # ZaakTypeInformatieObjectTypeConfig
    for config in ZaakTypeInformatieObjectTypeConfig.objects.all():
        if old_url in config.informatieobjecttype_url:
            config.informatieobjecttype_url = config.informatieobjecttype_url.replace(
                old_url, new_url
            )
            config.save()
            count += 1
    # ZaakTypeStatusTypeConfig
    for config in ZaakTypeStatusTypeConfig.objects.all():
        if old_url in config.statustype_url:
            config.statustype_url = config.statustype_url.replace(old_url, new_url)
            config.save()
            count += 1
    # ZaakTypeResultaatTypeConfig
    for config in ZaakTypeResultaatTypeConfig.objects.all():
        if old_url in config.resultaattype_url:
            config.resultaattype_url = config.resultaattype_url.replace(
                old_url, new_url
            )
            config.save()
            count += 1
    return count
