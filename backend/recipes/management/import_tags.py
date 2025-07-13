from recipes.models import Tag
from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    model = Tag
    filename = 'data/tags.json'
    help = 'Load tags from JSON fixture'
