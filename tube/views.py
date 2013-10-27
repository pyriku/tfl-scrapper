from datetime import datetime

from rest_framework import generics

from .models import TubeDisruption
from .serializers import TubeDisruptionSerializer


class DisruptionsView(generics.ListAPIView):
    queryset = TubeDisruption.objects.all()
    serializer_class = TubeDisruptionSerializer
    paginate_by = 100

    def get_pagination_serializer(self, page):
        serializer = super(DisruptionsView, self).get_pagination_serializer(page)

        if 'next' in serializer.data and serializer.data['next']:
            serializer.data['next'] = serializer.data['next'].replace(
                'localhost:8600', 'tfl.recio.me')
        if 'previous' in serializer.data and serializer.data['previous']:
            serializer.data['previous'] = serializer.data['previous'].replace(
                'localhost:8600', 'tfl.recio.me')

        return serializer

    def get_queryset(self):
        qs = super(DisruptionsView, self).get_queryset()
        filters = {}

        start = self.request.QUERY_PARAMS.get('start__gt')
        end = self.request.QUERY_PARAMS.get('end__lt')
        line = self.request.QUERY_PARAMS.getlist('line')
        description = self.request.QUERY_PARAMS.getlist('description')

        if start:
            filters['start__gt'] = datetime.strptime(start, "%Y-%m-%d")
        if end:
            filters['end__lt'] = datetime.strptime(end, "%Y-%m-%d")
        if line:
            filters['line__in'] = line
        if description:
            filters['description__in'] = description

        if filters:
            qs = qs.filter(**filters)
        return qs
