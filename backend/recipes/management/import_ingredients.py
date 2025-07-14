from recipes.models import Ingredients
from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    model = Ingredients
    filename: str
