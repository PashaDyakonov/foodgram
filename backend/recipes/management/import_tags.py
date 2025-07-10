from core.management.commands._base_import import BaseImportCommand

from recipes.models import Tags


class Command(BaseImportCommand):
    model = Tags
    filename = 'data/tags.json'
    help = 'Load tags from JSON fixture'
