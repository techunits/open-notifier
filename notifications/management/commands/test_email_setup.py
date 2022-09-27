from django.core.management.base import BaseCommand
from django.conf import settings


device_id = "2e5a016d-fcb7-4966-882f-7b9502e02ee6"
network_id = "040bd8f2-cb5a-4d99-b858-103246cc731a"

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        device_obj = Device.objects.get(pk=str(device_id))

        storage =  storage = ZODB.FileStorage.FileStorage(os.path.join("qwerx.dummy.fs"))
        db = ZODB.DB(storage)
        connection = db.open()
        device_config = connection.root
        device_config.id = str(device_obj.pk)
        device_config.lookup_token_index = device_obj.lookup_token_index
        device_config.agent_token = device_obj.agent_token
        device_config.network_id = network_id
        transaction.commit()
        connection.close()
