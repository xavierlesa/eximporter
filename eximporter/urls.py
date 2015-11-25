# -*- coding:utf-8 -*-

from django.conf.urls import include, url
from eximporter.views import ExImportView, FileUploaderView

urlpatterns = [
        url(r'^eximporter/upload/$', 
            FileUploaderView.as_view(), name='eximport_file_uploader'),

        url(r'^eximporter/import/(?P<uuid>[^/]+)/$', 
            ExImportView.as_view(), name='eximport_import'),
        ]
