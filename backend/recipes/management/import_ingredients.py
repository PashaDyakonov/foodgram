from core.management.commands._base_import import BaseImportCommand

from recipes.models import Ingredients


class Command(BaseImportCommand):
    model = Ingredients
    filename = 'data/ingredients.json'
    help = 'Load ingredients from JSON fixture'
