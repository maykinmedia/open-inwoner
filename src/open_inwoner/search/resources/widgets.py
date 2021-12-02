from import_export.widgets import SimpleArrayWidget


class CustomSimpleArrayWidget(SimpleArrayWidget):
    def render(self, value, obj=None):
        return ", ".join(str(v) for v in value)
