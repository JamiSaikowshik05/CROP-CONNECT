"""
Django management command to train ML models from CSV files.
Usage: python manage.py train_ml
"""
from django.core.management.base import BaseCommand
import subprocess
import os
import sys


class Command(BaseCommand):
    help = 'Train ML models from CSV files in ml_data/ folder'

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        train_script = os.path.join(base_dir, 'train_models.py')

        if not os.path.exists(train_script):
            self.stderr.write('train_models.py not found!')
            return

        self.stdout.write('Starting ML training...\n')
        result = subprocess.run(
            [sys.executable, train_script],
            capture_output=False
        )
        if result.returncode == 0:
            self.stdout.write(self.style.SUCCESS('\nML training completed!'))
        else:
            self.stderr.write('Training failed. Check CSV files in ml_data/.')
