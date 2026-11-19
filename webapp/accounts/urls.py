from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.user_list, name="list"),
    path("new/", views.user_create, name="create"),
    path("<int:pk>/edit/", views.user_update, name="update"),
    path("<int:pk>/password/", views.user_set_password, name="password"),
    path("<int:pk>/delete/", views.user_delete, name="delete"),
]
