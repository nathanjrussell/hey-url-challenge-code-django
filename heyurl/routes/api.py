from django.urls import path

from heyurl import views

urlpatterns = [
    path("urls/get_last_n/<int:num_records>/",views.get_n_urls,name="get_n_urls")
]
