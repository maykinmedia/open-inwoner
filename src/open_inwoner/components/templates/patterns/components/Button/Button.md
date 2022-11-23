    Creating a button. This can be a HTML button or an anchor element.

    Variables:
        + text: string | this will be the button text.
        - class: str | Additional classes.
        - hide_text: bool | whether to hide the text and use aria attribute instead.
        - href: url or string | where the link links to (can be url name).
        - uuid: string | if href is an url name, pk for reverse can be passed.
        - size: enum[big] | If the button should be bigger.
        - open: bool | If the open style button should be used.
        - bordered: bool | If the border should be colored.
        - primary: bool | If the primary colors should be used.
        - secondary: bool | If the secondary colors should be used.
        - transparent: bool | If the button does not have a background or border.
        - pill: bool | Display the button as a pill.
        - disabled: bool: If the button is disabled.
        - icon: string | the icon that you want to display.
        - icon_position: enum[before, after] | where the icon should be positioned to the text.
        - icon_outlined: bool | if the outlined icons should be used.
        - type: string | the type of button that should be used.
        - title: string | The HTML title attribute if different than the text.
        - extra_classes: string | Extra classes that need to be added to the button

    Extra context:
        - classes: string | all the classes that the button should have.
