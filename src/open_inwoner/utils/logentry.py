from django.contrib.admin import models

LOG_ACTIONS = {
    models.ADDITION: (models.ADDITION, "Addition"),
    models.CHANGE: (models.CHANGE, "Change"),
    models.DELETION: (models.DELETION, "Deletion"),
    4: (4, "User action"),
}
