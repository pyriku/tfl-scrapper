from rest_framework import generics

from .models import TubeDisruption
from .serializers import TubeDisruptionSerializer


class DisruptionsView(generics.ListAPIView):
    queryset = TubeDisruption.objects.all()
    serializer_class = TubeDisruptionSerializer
    paginate_by = 100
    filter_fields = ('line', 'description', 'start', 'end')
