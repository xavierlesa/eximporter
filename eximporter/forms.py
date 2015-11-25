# -*- coding:utf-8 -*-

from django import forms
from django.utils.translation import ugettext_lazy as _
import logging
log = logging.getLogger(__name__)


class FileUploaderForm(forms.Form):
    file_source = forms.FileField(label=_("Archivo"), widget=forms.FileInput)
