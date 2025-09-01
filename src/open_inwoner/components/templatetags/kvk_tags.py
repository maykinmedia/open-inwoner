import json
from typing import Any, Dict

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


def format_address(address_data: Dict[str, Any]) -> str:
    """
    Format address data into a human-readable string.

    Handles both combined straatHuisnummer field and separate
    straatnaam/huisnummer/huisnummerToevoeging fields.

    Args:
        address_data: Dictionary containing address fields from KVK API

    Returns:
        Formatted address string, or empty string if no address data
    """
    if not address_data:
        return ""

    # Check for combined street+house number field first
    if address_data.get("straatHuisnummer"):
        return address_data["straatHuisnummer"]

    # Build address from separate components
    address_parts = []
    if address_data.get("straatnaam"):
        address_parts.append(address_data["straatnaam"])
    if address_data.get("huisnummer"):
        address_parts.append(str(address_data["huisnummer"]))
    if address_data.get("huisnummerToevoeging"):
        address_parts.append(address_data["huisnummerToevoeging"])

    return " ".join(address_parts)


@register.simple_tag
def vestigingen_combox_data(branches, selected_id=None):
    """
    Convert Django branch data to React-compatible JSON format for the KVKBranchSelector component.
    This includes only the branch data - translations are handled by react-intl.

    IMPORTANT: The data flow works as follows:
    1. Django creates this JSON data with branch info
    2. HTML template embeds this JSON in a <script> tag
    3. React KVKBranchSelectorModule reads this JSON and renders the dropdown
    4. User selects a branch in React UI
    5. React creates hidden <input name="branch_number"> with selected branch ID
    6. Form submission sends branch_number back to Django
    7. Django view reads request.POST['branch_number'] to get user's choice

    Args:
        branches: List of branch dictionaries from KVK API
        selected_id: Currently selected vestigingsnummer (or "rechtspersoon")

    Returns:
        Safe JSON string ready to embed in HTML template
    """

    # Validate input to prevent errors with invalid data
    if not branches or not isinstance(branches, (list, tuple)):
        return mark_safe(json.dumps({"items": [], "selected_id": ""}))  # noqa: S308

    items = []
    for branch in branches:
        # Handle the "entire company" case (empty vestigingsnummer)
        # CRITICAL: This branch_id becomes the value sent back to Django as 'branch_number'
        # Use "rechtspersoon" as default for clarity (Dutch legal entity term)
        # Note: Using 'or' to handle both missing AND empty string values
        branch_id = branch.get("vestigingsnummer") or "rechtspersoon"

        # Build structured additional info for multi-line display in React dropdown
        vestiging_info = ""
        rechtspersoon_info = ""

        # Check branch type once and build appropriate info
        if branch_id == "rechtspersoon":
            # Show "(Rechtspersoon)" as separate line for entire company option
            rechtspersoon_info = "Selecteer de rechtspersoon (geen vestiging)"
        else:
            vestiging_info = f"Vestiging: {branch['vestigingsnummer']}"
            if branch.get("type") == "hoofdvestiging":
                vestiging_info += " (Hoofdvestiging)"

        # Add address information to help users identify the correct branch
        adres = branch.get("adres", {}).get("binnenlandsAdres", {})
        address_info = format_address(adres)

        # Get city information
        city_info = adres.get("plaats", "")

        # Properly escape all string values to prevent Cross-Site Scripting attacks
        # React will display these values in the interactive dropdown
        items.append(
            {
                "id": escape(
                    str(branch_id)
                ),  # Used as form value for branch_number field
                "label": escape(str(branch.get("naam", ""))),
                "vestigingInfo": escape(vestiging_info),
                "rechtspersoonInfo": escape(rechtspersoon_info),
                "addressInfo": escape(address_info),
                "cityInfo": escape(city_info),
                "vestigingsnummer": escape(str(branch.get("vestigingsnummer", ""))),
                "type": escape(str(branch.get("type", ""))),
            }
        )

    data = {
        "items": items,
        "selected_id": escape(
            str(selected_id or "")
        ),  # Pre-selected branch for React component
        # No translations here - handled by react-intl in the React component
    }

    # We need mark_safe here because JSON needs to be output as-is in the template
    # All individual data values are already escaped above for security
    return mark_safe(json.dumps(data, ensure_ascii=False))  # noqa: S308
