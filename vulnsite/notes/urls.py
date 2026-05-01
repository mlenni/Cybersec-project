from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("notes/", views.notes_view, name="notes"),
    path("notes/new/", views.note_create_view, name="note_create"),
    path("notes/<int:note_id>/", views.note_detail_view, name="note_detail"),
    path("notes/<int:note_id>/edit/", views.note_edit_view, name="note_edit"),

    path("search/", views.search_view, name="search"),
    path("fetch-url/", views.fetch_url_view, name="fetch_url"),
]