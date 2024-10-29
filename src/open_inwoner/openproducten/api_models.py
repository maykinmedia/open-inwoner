from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from zgw_consumers.api_models.base import Model


@dataclass
class TagType(Model):
    id: str
    name: str


@dataclass
class Tag(Model):
    id: str
    name: str
    icon: Optional[str]
    type: TagType


@dataclass
class Link(Model):
    id: str
    name: str
    url: str


@dataclass
class File(Model):
    id: str
    file: str


@dataclass
class Question(Model):
    id: str
    question: str
    answer: str


@dataclass
class Condition(Model):
    id: str
    name: str
    question: str
    positive_text: str
    negative_text: str


@dataclass
class BaseCategory(Model):
    id: str


@dataclass
class Category(BaseCategory):
    name: str
    description: str
    icon: Optional[str]
    image: Optional[str]
    published: bool
    parent_category: Optional[str]
    questions: list[Question]


@dataclass
class PriceOption(Model):
    id: str
    amount: str
    description: str


@dataclass
class Price(Model):
    id: str
    valid_from: date
    options: list[PriceOption]


@dataclass
class Location(Model):
    id: str
    coordinates: list[float]
    name: str
    email: str
    phone_number: str
    street: str
    house_number: str
    postcode: str
    city: str


@dataclass
class Neighbourhood(Model):
    id: str
    name: str


@dataclass
class OrganisationType(Model):
    id: str
    name: str


@dataclass
class Organisation(Location):
    neighbourhood: Neighbourhood
    type: OrganisationType
    logo: Optional[str]


@dataclass
class Contact(Model):
    id: str
    organisation_id: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    role: str


@dataclass
class ProductType(Model):
    id: str
    published: bool
    name: str
    summary: str
    icon: Optional[str]
    image: Optional[str]
    form_link: str
    open_forms_slug: str
    content: str
    keywords: list[str]
    uniform_product_name: str
    conditions: list[Condition]
    tags: list[Tag]
    categories: list[BaseCategory]
    links: list[Link]
    files: list[File]
    prices: list[Price]
    questions: list[Question]
    locations: list[Location]
    organisations: list[Organisation]
    contacts: list[Contact]
    related_product_types: list[str]

    related_product_types: list = field(default_factory=list)
