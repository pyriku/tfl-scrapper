import hashlib
import re
from xml.etree import ElementTree

from django.db import models

TAG_PREFIX = '{http://webservices.lul.co.uk/}'

slugify = lambda x: re.sub(r'\W+', '-', x.lower())
tag = lambda x: '%s%s' % (TAG_PREFIX, x)
to_bool = lambda x: x == 'true'


def status_difference(status1, status2):

    first = lambda x, y: x if x.fetched < y.fetched else y
    last = lambda x, y: x if x.fetched > y.fetched else y
    summary_s1 = first(status1, status2).status_summary()
    summary_s2 = last(status1, status2).status_summary()

    return {line: summary_s2[line] for line in summary_s1 if summary_s1[line] != summary_s2[line]}


TUBE_LINES = [
    ('bakerloo', 'Bakerloo'),
    ('central', 'Central'),
    ('circle', 'Circle'),
    ('district', 'District'),
    ('dlr', 'DLR'),
    ('hammersmith-and-city', 'Hammersmith and City'),
    ('jubilee', 'Jubilee'),
    ('metropolitan', 'Metropolitan'),
    ('northern', 'Northern'),
    ('overground', 'Overground'),
    ('piccadilly', 'Picadilly'),
    ('victoria', 'Victoria'),
    ('waterloo-and-city', 'Waterloo and City'),
]


class TubeDisruption(models.Model):
    line = models.CharField(max_length=200, choices=TUBE_LINES)
    description = models.CharField(max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)
    duration = models.PositiveIntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.duration and self.end:
            self.duration = int((self.end - self.start).total_seconds() / 60)
        return super(TubeDisruption, self).save(*args, **kwargs)

    def __str__(self):
        return '%s - %s' % (self.line, self.description)


def create_tube_disruptions():
    statuses = TubeStatus.objects.all()
    for index in range(1, TubeStatus.objects.count()):
        differences = status_difference(statuses[index], statuses[index - 1])
        for line, description in differences.items():
            try:
                disruption = TubeDisruption.objects.get(line=line, end__isnull=True)
            except TubeDisruption.DoesNotExist:
                disruption = None

            if disruption:
                disruption.end = statuses[index].fetched
                disruption.save()

            TubeDisruption.objects.create(
                line=line, description=description, start=statuses[index].fetched)


class TubeStatus(models.Model):
    raw_status = models.TextField()
    fetched = models.DateTimeField(auto_now_add=True)
    hash_id = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        _hash = hashlib.md5()
        _hash.update(self.raw_status)
        self.hash_id = _hash.hexdigest()
        return super(TubeStatus, self).save(*args, **kwargs)

    def to_json(self):
        root = ElementTree.fromstring(self.raw_status)

        response = {}

        for line in root:  # iterate over the Tube lines
            _line = line.find(tag('Line')).attrib
            line_name = _line['Name']
            line_id = _line['ID']

            _status = line.find(tag('Status')).attrib

            status = {
                'name': line_name,
                'id': line_id,
                'status': {
                    'details': line.attrib['StatusDetails'],
                    'id': _status['ID'],
                    'description': _status['Description'],
                    'isActive': to_bool(_status['IsActive']),
                    'global': _status['CssClass']
                },
                'disruptions': []
            }

            _disruptions = line.find(tag('BranchDisruptions')) or []
            for disruption in _disruptions:
                _to = disruption.find(tag('StationTo')).attrib
                _from = disruption.find(tag('StationFrom')).attrib
                status['disruptions'].append({
                    'to': {'id': _to['ID'], 'name': _to['Name']},
                    'from': {'id': _from['ID'], 'name': _from['Name']}
                })

            response[slugify(line_name)] = status

        return response

    def status_summary(self):
        return {x: y['status']['description'] for (x, y) in self.to_json().items()}

    def __str__(self):
        return self.fetched.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        ordering = ['fetched']
