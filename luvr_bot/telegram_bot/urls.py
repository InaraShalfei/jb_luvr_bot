from django.urls import path

from . import views, parser

urlpatterns = [
    path('', views.main_func, name='main_function'),
    path('start/', views.start, name='start'),
    path('parse/', parser.parse, name='parse_excel')
 ]
