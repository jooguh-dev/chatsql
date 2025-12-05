from django.core.management.base import BaseCommand
from django.db import connection, transaction
from exercises.models import DatabaseSchema


class Command(BaseCommand):
    help = 'Apply schema_sql and seed_sql from DatabaseSchema into the default database'

    def handle(self, *args, **options):
        schemas = DatabaseSchema.objects.all()
        if not schemas:
            self.stdout.write(self.style.WARNING('No DatabaseSchema records found'))
            return

        with connection.cursor() as cursor:
            for s in schemas:
                self.stdout.write(f'Applying schema for {s.name}...')
                try:
                    with transaction.atomic():
                        if s.schema_sql:
                            cursor.executescript(s.schema_sql)
                        if s.seed_sql:
                            cursor.executescript(s.seed_sql)
                    self.stdout.write(self.style.SUCCESS(f'Applied schema and seed for {s.name}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to apply {s.name}: {e}'))