# -*- coding:utf-8 -*-

import uuid
import os
from django import forms
from django.forms import modelform_factory
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.views import generic
from django.views.generic.edit import FormView
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from .forms import FileUploaderForm
from .eximporter import ExImporter

import logging
log = logging.getLogger(__name__)

class ExImporterException(Exception):
    pass


class FileUploaderView(FormView):
    template_name = 'eximporter/file_uploader_form.html'
    form_class = FileUploaderForm

    def get_success_url(self, *args, **kwargs):
        if self.fname:
            return reverse_lazy('eximport_import', kwargs=dict(uuid=self.fname))
        return reverse_lazy('eximport_file_uploader')

    def form_valid(self, form):
        log.debug(u"Se cargaron los datos de forma correcta, intenta importar")
        log.debug(form.cleaned_data.get('file_source'))
        data = form.cleaned_data.get('file_source')
        
        if data:
            fname = str(uuid.uuid1())
            path = default_storage.save(u'tmp/' + fname, ContentFile(data.read()))
            tmp_file = os.path.join(settings.MEDIA_ROOT, path)
            self.fname = fname

        return super(FileUploaderView, self).form_valid(form)


class FileUploaderAdminView(FileUploaderView):
    def get_success_url(self, *args, **kwargs):
        if self.fname:
            return reverse_lazy('admin:eximport_import', kwargs=dict(uuid=self.fname))
        return reverse_lazy('admin:eximport_file_uploader')


class ExImportView(generic.View):
    template_name = 'eximporter/import_form.html'
    model = None
    fields = []
    exclude = []
    result = []

    def get_object(self, *args, **kwargs):
        return None

    def get_queryset(self, *args, **kwargs):
        return None

    def get_model(self, *args, **kwargs):
        return self.model or self.get_object() or self.get_queryset().model

    def create_form_class(self, *args, **kwargs):
        if not self.fields and not self.exclude:
            raise ExImporterException(u"Error field o exclude son necesarios")

        return modelform_factory(self.get_model(), fields=self.fields, exclude=self.exclude)

    def get_form_importer(self, request, *args, **kwargs):
        initial = self.get_initial(request, *args, **kwargs)
        form = self.create_form_class()

        #for fields in form.fields:
        for field_name, field_instance in form.base_fields.iteritems():
            # No es un iterable/choice entonces le pone el choices con los 
            # campos del excel/csv
            if not hasattr(field_instance, 'choices'):
                form.base_fields[field_name] = forms.ChoiceField(choices=initial[field_name])

        return form

    def get_initial(self, request, *args, **kwargs):
        uuid = self.kwargs['uuid']
        path = os.path.join(settings.MEDIA_ROOT, 'tmp/', uuid)
        initial_fields = {}

        if os.path.isfile(path):
            log.debug('Lee el archivo %s', path)
            exi = ExImporter()
            exi.load_file(path)
            columns = exi.get_columns().items()
            log.info(columns)

            form = self.create_form_class()

            #for fields in form.fields:
            for field_name, field_instance in form.base_fields.iteritems():
                # No es un iterable/choice entonces le pone el choices con los 
                # campos del excel/csv
                if not hasattr(field_instance, 'choices'):
                    initial_fields.update({field_name:columns})

        return initial_fields

    def get_form_class(self, request, *args, **kwargs):
        return self.get_form_importer(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class(request, *args, **kwargs)
        form = form_class(initial=self.get_initial(request, *args, **kwargs))
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class(request, *args, **kwargs)
        form = form_class(request.POST, initial=self.get_initial(request, *args, **kwargs))

        uuid = self.kwargs['uuid']
        fname = os.path.join(settings.MEDIA_ROOT, 'tmp/', uuid)

        if form.is_valid() and os.path.isfile(fname):
            log.info('cargando el archivo %s', fname)
            dcolumns = dict((str(val), key) for key, val in form.cleaned_data.iteritems())
            log.debug(dcolumns)

            exi = ExImporter()
            exi.load_file(fname)
            
            for data in exi.data:
                self.import_item(**exi.migrate_columns(data, dcolumns))

        return render(request, self.template_name, {
            'form': form, 
            'result': self.result
            })

    def import_item(self, *args, **kwargs):
        log.debug(kwargs)
