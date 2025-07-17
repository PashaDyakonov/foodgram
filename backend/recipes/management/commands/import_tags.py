from recipes.models import Tag
from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    model = Tag
    default_filename = 'data/tags.json'
