import hashlib
import re
from xml.etree import ElementTree

from django.db import models

TAG_PREFIX = '{http://webservices.lul.co.uk/}'

slugify = lambda x: re.sub(r'\W+', '-', x.lower())
tag = lambda x: '%s%s' % (TAG_PREFIX, x)
to_bool = lambda x: x == 'true'


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

    def __str__(self):
        return self.fetched.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        ordering = ['fetched']
