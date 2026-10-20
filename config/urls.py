from django.contrib import admin
from django.urls import include, path

from config.views import home


urlpatterns = [

    path(
        'admin/',
        admin.site.urls
    ),

    path(
        '',
        home,
        name='home'
    ),

    path(
        'accounts/',
        include('accounts.urls')
    ),

    path(
        'classrooms/',
        include('classrooms.urls')
    ),

    path(
        'problems/',
        include('problems.urls')
    ),

    path(
    'submissions/',
    include('submissions.urls')
),

]