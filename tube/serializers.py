from rest_framework import serializers

from .models import TubeDisruption


class TubeDisruptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TubeDisruption
        fields = (
            'id',
            'line',
            'description',
            'start',
            'end',
            'duration'
        )
