from django.core.management.base import BaseCommand
from django.conf import settings


device_id = "2e5a016d-fcb7-4966-882f-7b9502e02ee6"
network_id = "040bd8f2-cb5a-4d99-b858-103246cc731a"

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        pass
