from django.core.exceptions import ObjectDoesNotExist

from cms.models import Page
from menus.base import Modifier
from menus.menu_pool import menu_pool

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.cms.extensions.models import CommonExtension


class MenuModifier(Modifier):
    default_common = CommonExtension()

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        if post_cut:
            page_nodes = {n.id: n for n in nodes if n.attr["is_page"]}
            pages = (
                Page.objects.filter(id__in=page_nodes.keys())
                # optimise and only retrieve id and related object
                .only("id").select_related("commonextension")
            )
            for page in pages:
                node = page_nodes[page.id]
                try:
                    ext = page.commonextension
                except ObjectDoesNotExist:
                    ext = self.default_common

                # keep this if we need it for templates
                node.common = ext

                # modify menu check for page visibility
                if ext.requires_auth and not request.user.is_authenticated:
                    nodes.remove(node)
                elif (
                    ext.requires_auth_bsn
                    and not request.user.login_type == LoginTypeChoices.digid
                ):
                    nodes.remove(node)

        return nodes


menu_pool.register_modifier(MenuModifier)
