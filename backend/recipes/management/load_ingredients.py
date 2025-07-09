import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredients


class Command(BaseCommand):
    help = 'Load ingredients from JSON fixture using bulk_create()'

    def handle(self, *args, **options):
        try:
            with open('data/ingredients.json', encoding='utf-8') as f:
                data = json.load(f)
                ingredients = []
                existing_names = set(
                    Ingredients.objects.values_list('name', flat=True))

                for item in data:
                    fields = item.get('fields', {})
                    name = fields.get('name', '').strip()
                    measurement_unit = fields.get('measurement_unit', 'г')
                    if name and name not in existing_names:
                        ingredients.append(
                            Ingredients(
                                name=name,
                                measurement_unit=measurement_unit
                            )
                        )
                if ingredients:
                    Ingredients.objects.bulk_create(ingredients)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Загружено {len(ingredients)} ингредиентов')
                    )
                else:
                    self.stdout.write(self.style.WARNING(
                        'Все ингредиенты уже есть в базе'
                    ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                'Файл data/ingredients.json не найден'
            ))

        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(
                'Ошибка парсинга JSON. Проверьте формат файла'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Неизвестная ошибка: {str(e)}'
            ))
