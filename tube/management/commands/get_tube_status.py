import hashlib

import requests
from django.core.management.base import BaseCommand

from tube.models import TubeStatus

TFL_STATUS_URL = 'http://cloud.tfl.gov.uk/TrackerNet/LineStatus'


class Command(BaseCommand):

    def handle(self, *args, **options):
        response = requests.get(TFL_STATUS_URL)
        status = response.content
        _hash = hashlib.md5()
        _hash.update(status)
        md5 = _hash.hexdigest()

        try:
            latest = TubeStatus.objects.latest('fetched')
        except TubeStatus.DoesNotExist:
            latest = None

        if not latest or latest.hash_id != md5:
            TubeStatus.objects.create(raw_status=status)
