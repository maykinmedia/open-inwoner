from django.utils.translation import gettext_lazy as _

# mail-editor
MAIL_EDITOR_CONF = {
    "invite": {
        "name": _("Invitation Email"),
        "description": _(
            "This email is used to invite people to sing up to the website"
        ),
        "subject_default": "Uitnodiging voor {{ site_name }}",
        "body_default": """
            <p>Beste</p>

            <p>Je bent door {{ inviter_name}} uitgenodigd om in te loggen op {{ site_name }}.
            Gebruik onderstaande link om je aan te melden </p>

            <p><a href="{{ invite_link }}">aanmelden</a> </p>

            <p>Mocht je geen behoefte hieraan hebben dan staat het je vrij om dit bericht te negeren </p>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
        """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
            {"name": "inviter_name", "description": _("Full name of the inviter")},
        ],
        "body": [
            {
                "name": "inviter_name",
                "description": _("Full name of the inviter"),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
            {
                "name": "invite_link",
                "description": _("Link to activate their account."),
            },
            {"name": "email", "description": _("Email of the invited user")},
        ],
    },
    "contact_approval": {
        "name": _("Contact Approval Email"),
        "description": _(
            "This email is used to notify people for pending approvals of new contacts"
        ),
        "subject_default": "Goedkeuring geven op {{ site_name }}: {{ sender_name }} wilt u toevoegen als contactpersoon",
        "body_default": """
            <p>Beste</p>

            <p>Gebruiker {{ sender_name }} wilt u toevoegen als contactpersoon op {{ site_name }}.
            Volg onderstaande link waarop u uw goedkeuring kan geven of kan aangeven {{ sender_name }} niet als contactpersoon te willen. </p>

            <p><a href="{{ contacts_link }}">Mijn Contacten</a> </p>

            <p>U kunt ook op een later moment toestemming geven, het verzoek van {{ sender_name }} blijft open staat totdat u een keuze heeft gemaakt.</p>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
        """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
            {
                "name": "sender_name",
                "description": _("Full name of the inviter-sender"),
            },
        ],
        "body": [
            {
                "name": "sender_name",
                "description": _("Full name of the inviter-sender"),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
            {
                "name": "contacts_link",
                "description": _("Link to contact list page."),
            },
            {"name": "email", "description": _("Email of the receiver user")},
        ],
    },
    "new_messages": {
        "name": _("New Message Email"),
        "description": _(
            "This email is used to inform users about the new messages in their inbox"
        ),
        "subject_default": "New messages at {{ site_name }}",
        "body_default": """
           <p>Beste</p>

           <p>You've received {{ total_messages }} new messages from {{ total_senders }} users</p>

           <p><a href="{{ inbox_link }}">Go to the inbox</a> </p>

           <p>Met vriendelijke groet,
           {{ site_name }} </p>
       """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
        ],
        "body": [
            {
                "name": "total_messages",
                "description": _("Number of the new messages"),
            },
            {
                "name": "total_senders",
                "description": _("Number of the senders"),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
            {
                "name": "inbox_link",
                "description": _("Link to see the conversation."),
            },
        ],
    },
    "expiring_action": {
        "name": _("Action end date today"),
        "description": _(
            "This email is used to remind users that there are actions that are ending today"
        ),
        "subject_default": "Actions about to end today at {{ site_name }}",
        "body_default": """
            <p>Beste</p>

            <p>You are receiving this email because you have some actions that are expiring.</p>

            <table>
                <tr>
                    <td>Action name</td>
                    <td>End date</td>
                </tr>
            {% for action in actions %}
                <tr>
                    <td>{{ action.name }}</td>
                    <td>{{ action.end_date|date:"j F Y" }}</td>
                </tr>
            {% endfor %}
            </table>

            <p><a href="{{ actions_link }}">Go to your actions</a> </p>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
       """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
        ],
        "body": [
            {
                "name": "actions",
                "description": _("A list of actions that will expire today"),
            },
            {
                "name": "actions_link",
                "description": _("The link to your actions page."),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
        ],
    },
    "expiring_plan": {
        "name": _("Plan end date today"),
        "description": _(
            "This email is used to remind users that there are plans that are ending today"
        ),
        "subject_default": "Plans about to end today at {{ site_name }}",
        "body_default": """
            <p>Beste</p>

            <p>You are receiving this email because you have some plans that are expiring.</p>

            <table>
                <tr>
                    <td>Plan name</td>
                    <td>Goal</td>
                    <td>End date</td>
                </tr>
            {% for plan in plans %}
                <tr>
                    <td>{{ plan.title }}</td>
                    <td>{{ plan.goal }}</td>
                    <td>{{ plan.end_date|date:"j F Y" }}</td>
                </tr>
            {% endfor %}
            </table>

            <p><a href="{{ plan_list_link }}">Go to your plans</a> </p>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
       """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
        ],
        "body": [
            {
                "name": "plans",
                "description": _("A list of plans that will expire today"),
            },
            {
                "name": "plan_list_link",
                "description": _("The link to your plans page."),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
        ],
    },
    "plan_action_update": {
        "name": _("Plan action update"),
        "description": _(
            "This email is used to notify plan participants about the change in the plan action"
        ),
        "subject_default": "Plan action has been updated at {{ site_name }}",
        "body_default": """
            <p>Beste</p>

            <p>You are receiving this email because the action in your <a href="{{ plan_url }}">plan</a> was updated.</p>

            <table>
                <tr>
                    <th>Action name</th>
                    <td>{{ action.name }}</td>
                </tr>
                <tr>
                    <th>Plan</th>
                    <td><a href="{{ plan_url }}">{{ plan.title }}</a></td>
                </tr>
                <tr>
                    <th>Updated at</th>
                    <td>{{ action.updated_on }}</td>
                </tr>
                <tr>
                    <th>Details</th>
                    <td>{{ message }}</td>
                </tr>
            </table>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
       """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
        ],
        "body": [
            {
                "name": "action",
                "description": _("Action that was updated"),
            },
            {
                "name": "plan",
                "description": _("Plan the updated action belongs to"),
            },
            {
                "name": "plan_url",
                "description": _("The link to the plan."),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
        ],
    },
    "case_notification": {
        "name": _("Case update notification"),
        "description": _(
            "This email is used to notify people an update happened to their case"
        ),
        "subject_default": "Update to your case at {{ site_name }}",
        "body_default": """
            <p>Beste</p>

            <p>You are receiving this email because one of your cases received a new status update or document attachment.</p>

            <table>
                <tr>
                    <th>Case identification</th>
                    <td>{{ identification }}</td>
                </tr>
                <tr>
                    <th>Case type</th>
                    <td>{{ type_description }}</td>
                </tr>
                <tr>
                    <th>Start date</th>
                    <td>{{ start_date }}</td>
                </tr>
            </table>

            <p><a href="{{ case_link }}">Go to your case</a> </p>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
       """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
        ],
        "body": [
            {
                "name": "identification",
                "description": _("The identification of the case"),
            },
            {
                "name": "type_description",
                "description": _("The description of the type of the case"),
            },
            {
                "name": "start_date",
                "description": _("The start date of the case"),
            },
            {
                "name": "case_link",
                "description": _("The link to the case details."),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
        ],
    },
    "contactform_registration": {
        "name": _("Contact form registration notification"),
        "description": _("This email is used to register a contact form submission"),
        "subject_default": "Contact formulier inzending vanaf {{ site_name }}",
        "body_default": """
            <p>Beste</p>

            <table>
                <tr>
                    <th>Onderwerp:</th>
                    <td>{{ subject }}</td>
                </tr>
                <tr>
                    <th>Naam:</th>
                    <td>{{ name }}</td>
                </tr>
                <tr>
                    <th>Email:</th>
                    <td>{{ email }}</td>
                </tr>
                <tr>
                    <th>Telefoonnummer:</th>
                    <td>{{ phonenumber }}</td>
                </tr>
                <tr>
                    <th colspan="2">Vraag:</th>
                </tr>
                <tr>
                    <td colspan="2">{{ question }}</th>
                </tr>
            </table>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
       """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
        ],
        "body": [
            {
                "name": "subject",
                "description": _("Onderwerp"),
            },
            {
                "name": "name",
                "description": _("Naam"),
            },
            {
                "name": "email",
                "description": _("E-mailadres"),
            },
            {
                "name": "phonenumber",
                "description": _("Telefoonnummer"),
            },
            {
                "name": "question",
                "description": _("Vraag"),
            },
        ],
    },
}
MAIL_EDITOR_BASE_CONTEXT = {"site_name": "Open Inwoner Platform"}
