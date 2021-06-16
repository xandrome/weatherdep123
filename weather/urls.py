from django.urls import path
from . import views

urlpatterns = [
	path('temperature/current/<latitude>,<longtitude>/', views.index),
	path('logs/', views.display_log_table),
	path('average/<voivo>', views.average_temperature_voivo),
]
