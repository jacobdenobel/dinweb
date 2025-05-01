from django.core.management.base import BaseCommand
from din.models import Questionary



class Command(BaseCommand):
    def handle(self, *args, **options):
        Questionary.objects.create(
            age = 31,
            normal_hearing = True,
            approve = True,
            first_time = True,
            first_language = True,
        )