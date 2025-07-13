from ._base_import import BaseImportCommand

from recipes.models import Ingredients


class Command(BaseImportCommand):
    model = Ingredients
