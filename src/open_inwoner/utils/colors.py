import re

ACCESSIBLE_CONTRAST_RATIO = 4.5


def hex_to_hsl(color):
    # Convert hex to RGB first
    r = 0
    g = 0
    b = 0
    if len(color) == 4:
        r = "0x" + color[1] + color[1]
        g = "0x" + color[2] + color[2]
        b = "0x" + color[3] + color[3]
    elif len(color) == 7:
        r = "0x" + color[1] + color[2]
        g = "0x" + color[3] + color[4]
        b = "0x" + color[5] + color[6]

    # Then to HSL
    r = int(r, 16) / 255
    g = int(g, 16) / 255
    b = int(b, 16) / 255
    cmin = min(r, g, b)
    cmax = max(r, g, b)
    delta = cmax - cmin
    h = 0
    s = 0
    l = 0

    if delta == 0:
        h = 0
    elif cmax == r:
        h = ((g - b) / delta) % 6
    elif cmax == g:
        h = (b - r) / delta + 2
    else:
        h = (r - g) / delta + 4

    h = round(h * 60)

    if h < 0:
        h += 360

    l = (cmax + cmin) / 2
    s = 0 if delta == 0 else delta / (1 - abs(2 * l - 1))
    s = int((s * 100))
    l = int((l * 100))

    return h, s, l


def hex_to_luminance(hex_color):
    """
    https://www.w3.org/TR/WCAG20-TECHS/G17.html#G17-procedure
    """
    color = re.sub(r"^0x|^#", "", hex_color)
    assert len(color) == 6

    def calc(c):
        if c <= 0.03928:
            return c / 12.92
        else:
            return pow((c + 0.055) / 1.055, 2.4)

    hex_red = int(color[0:2], base=16) / 255
    hex_green = int(color[2:4], base=16) / 255
    hex_blue = int(color[4:6], base=16) / 255

    return 0.2126 * calc(hex_red) + 0.7152 * calc(hex_green) + 0.0722 * calc(hex_blue)


def get_contrast_ratio(hex_1, hex_2):
    """
    https://www.w3.org/TR/WCAG20-TECHS/G17.html#G17-procedure
    """
    L1 = hex_to_luminance(hex_1)
    L2 = hex_to_luminance(hex_2)

    # L1 should be the more luminant
    if L1 < L2:
        L1, L2 = L2, L1

    return (L1 + 0.05) / (L2 + 0.05)
