from django.urls import path

from . import views

urlpatterns = [
    # ex: /urls/
    path('', views.index, name='index'),
    path('store', views.store, name='store'),
    # ex: /urls/5/
    # path('<url_id>/', views.show, name='show'),
    # ex: /urls/5/click/
    #path('<int:question_id>/results/', views.results, name='results'),
]
