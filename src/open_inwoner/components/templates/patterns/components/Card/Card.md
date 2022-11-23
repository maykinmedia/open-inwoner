    Render in a card. Only using variables.

    Variables:
        + href: url | where the card links to.
        + title: string | this will be the card title.
        - alt: string | the alt of the header image.
        - direction: string | can be set to "horizontal" to show contents horizontally.
        - inline: bool | Whether the card should be rendered inline.
        - src: string | the src of the header image.
        - tinted: bool | whether to use gray as background color.
        - type: string (info) | Set to info for an info card.
        - image: FilerImageField | an image that should be used.
        - image_object_fit: string | Can be set to either "cover" (default) or "contain".
        - grid: boolean | if the card should be a grid.
