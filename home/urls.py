from django.urls import path
from .views import GitHubRepoUploadView

urlpatterns = [
    path('upload-to-github/', GitHubRepoUploadView.as_view(), name='upload-to-github'),
]