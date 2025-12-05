from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from exercises.models import DatabaseSchema, Exercise
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Create demo superuser and sample DatabaseSchema + Exercise'

    def handle(self, *args, **options):
        User = get_user_model()

        # Choose credentials (fixed for demo)
        username = os.environ.get('DEMO_SUPERUSER_USERNAME', 'demo_admin')
        email = os.environ.get('DEMO_SUPERUSER_EMAIL', 'demo_admin@example.com')
        password = os.environ.get('DEMO_SUPERUSER_PASSWORD', 'DemoPass123!')

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Created superuser: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser {username} already exists'))

        # Create a sample DatabaseSchema
        schema, created = DatabaseSchema.objects.get_or_create(
            name='demo_hr',
            defaults={
                'display_name': 'Demo HR Schema',
                'description': 'A small HR schema for demo',
                'db_name': 'practice_hr',
                'schema_sql': 'CREATE TABLE employees (id INT PRIMARY KEY, name VARCHAR(100), dept VARCHAR(50));',
                'seed_sql': "INSERT INTO employees (id, name, dept) VALUES (1, 'Alice', 'Sales'), (2, 'Bob', 'Engineering');"
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created demo DatabaseSchema'))
        else:
            self.stdout.write(self.style.WARNING('Demo DatabaseSchema already present'))

        # Create a sample exercise
        ex, ecreated = Exercise.objects.get_or_create(
            schema=schema,
            title='List employees',
            defaults={
                'description': 'Select all employees',
                'difficulty': 'easy',
                'order': 1,
                'expected_sql': 'SELECT id, name, dept FROM employees ORDER BY id',
                'initial_query': 'SELECT id, name, dept FROM employees',
                'hints': [{'level': 1, 'text': 'Use SELECT to choose columns.'}],
                'tags': ['SELECT', 'ORDER BY']
            }
        )

        if ecreated:
            self.stdout.write(self.style.SUCCESS('Created demo Exercise'))
        else:
            self.stdout.write(self.style.WARNING('Demo Exercise already present'))

        # Persist superuser credentials to docs file for your convenience
        docs_dir = os.path.join(settings.BASE_DIR, 'docs')
        os.makedirs(docs_dir, exist_ok=True)
        creds_path = os.path.join(docs_dir, 'superuser.txt')
        with open(creds_path, 'w') as f:
            f.write(f'username={username}\n')
            f.write(f'email={email}\n')
            f.write(f'password={password}\n')

        self.stdout.write(self.style.SUCCESS(f'Wrote superuser creds to {creds_path}'))
