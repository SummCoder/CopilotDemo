# urls.py
# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^chat/$', views.chat, name='chat_api'),  # 👈 这一行是新增的
]