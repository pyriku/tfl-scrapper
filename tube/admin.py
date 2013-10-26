from django.contrib import admin
from .models import TubeStatus, TubeDisruption

admin.site.register(TubeStatus)
admin.site.register(TubeDisruption)
