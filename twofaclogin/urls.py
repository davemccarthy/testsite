from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("auth_first", views.auth_first, name="auth_first"),
    path("auth_second", views.auth_second, name="auth_second"),
    path("authorize/<str:token>", views.authorize, name="authorize")
]