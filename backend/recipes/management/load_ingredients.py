import csv
from django.core.management.base import BaseCommand
from recipes.models import Ingredients


class Command(BaseCommand):
    help = 'Load ingredients from CSV file'

    def handle(self, *args, **options):
        with open('data/ingredients.csv', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                name = row[0].strip()
                Ingredients.objects.get_or_create(
                    name=name,
                    measurement_unit='г'
                )
        self.stdout.write(self.style.SUCCESS('Ингредиенты успешно загружены'))
