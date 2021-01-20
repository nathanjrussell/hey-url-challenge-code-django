from django.urls import path

from heyurl import views

urlpatterns = [
    path('', views.index, name='index'),
    path('store', views.store, name='store'),
    path('click_data/<short_url>',views.click_data,name="click_data")
]
