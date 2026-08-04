from enum import Enum


class AfvalType(str, Enum):
    RESTAFVAL = "Restafval"
    GFT = "GFT"
    MED = "Med"
