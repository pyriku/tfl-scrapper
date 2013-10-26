import hashlib

import requests
from django.core.management.base import BaseCommand

from tube.models import TubeStatus, TubeDisruption, status_difference

TFL_STATUS_URL = 'http://cloud.tfl.gov.uk/TrackerNet/LineStatus'


class Command(BaseCommand):

    def handle(self, *args, **options):
        response = requests.get(TFL_STATUS_URL)
        status = response.content
        if status:
            _hash = hashlib.md5()
            _hash.update(status)
            md5 = _hash.hexdigest()

            try:
                latest = TubeStatus.objects.latest('fetched')
            except TubeStatus.DoesNotExist:
                latest = None

            if not latest or latest.hash_id != md5:
                status = TubeStatus.objects.create(raw_status=status)

                if TubeStatus.objects.count() > 1:
                    previous = TubeStatus.objects.all()[TubeStatus.objects.count() - 2]
                    differences = status_difference(previous, status)
                    for line, description in differences.items():
                        try:
                            disruption = TubeDisruption.objects.get(line=line, end__isnull=True)
                        except TubeDisruption.DoesNotExist:
                            disruption = None

                        if disruption:
                            disruption.end = status.fetched
                            disruption.save()

                        TubeDisruption.objects.create(
                            line=line, description=description, start=status.fetched)
