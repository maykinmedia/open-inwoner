from django.urls import path

from .views import CategoryDetailView, CategoryListView, HomeView, SearchView

urlpatterns = [
    path("search/", SearchView.as_view(), name="search"),
    path("themas/", CategoryListView.as_view(), name="themas"),
    path("themas/<str:slug>/", CategoryDetailView.as_view(), name="thema-detail"),
    path("", HomeView.as_view(), name="root"),
]
