import json
from django.core.management.base import BaseCommand
from django.db import models


class BaseImportCommand(BaseCommand):
    """Базовый класс для импорта данных из JSON"""
    model: models.Model
    filename: str
    help: str

    def handle(self, *args, **options):
        try:
            with open(self.filename, encoding='utf-8') as f:
                items = [
                    self.model(**item)
                    for item in json.load(f)
                    if self.is_valid_item(item)
                ]

                created_count = len(self.model.objects.bulk_create(
                    items,
                    ignore_conflicts=True
                ))
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Успешно загружено {created_count} '
                        '{self.model._meta.verbose_name_plural} из '
                        '{self.filename}'
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при загрузке {self.filename}: {e}'
            ))
