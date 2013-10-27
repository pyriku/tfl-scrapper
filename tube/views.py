from datetime import datetime

from rest_framework import generics

from .models import TubeDisruption
from .serializers import TubeDisruptionSerializer


class DisruptionsView(generics.ListAPIView):
    queryset = TubeDisruption.objects.all()
    serializer_class = TubeDisruptionSerializer
    paginate_by = 100
    filter_fields = ('line', 'description', 'start', 'end')

    def get_queryset(self):
        start = self.request.QUERY_PARAMS.get('start__gt')
        end = self.request.QUERY_PARAMS.get('end__lt')

        qs = super(DisruptionsView, self).get_queryset()
        filters = {}
        if start:
            filters['start__gt'] = datetime.strptime(start, "%Y-%m-%d")
        if end:
            filters['end__lt'] = datetime.strptime(end, "%Y-%m-%d")

        if filters:
            qs = qs.filter(**filters)
        return qs
