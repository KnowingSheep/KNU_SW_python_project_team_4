from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    path('danger/', views.danger_map_view, name='danger_map'),
    path('cluster/', views.cluster_map_view, name='cluster_map'),

    path('run/danger_map/', views.run_danger_map, name='run_danger_map'),
    path('run/cluster_map/', views.run_cluster_map, name='run_cluster_map'),
]
