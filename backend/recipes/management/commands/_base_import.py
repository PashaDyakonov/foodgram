import json

from django.core.management.base import BaseCommand
from django.db import models


class BaseImportCommand(BaseCommand):
    """Базовый класс для импорта данных из JSON"""
    model: models.Model
    filename: str

    def handle(self, *args, **options):
        try:
            with open(self.filename, encoding='utf-8') as f:
                created_count = len(self.model.objects.bulk_create(
                    [
                        self.model(**item)
                        for item in json.load(f)
                    ],
                    ignore_conflicts=True
                ))
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Успешно загружено {created_count} '
                        f'{self.model._meta.verbose_name_plural} из '
                        f'{self.filename}'
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при загрузке {self.filename}: {e}'
            ))
