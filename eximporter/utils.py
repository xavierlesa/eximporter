# -*- coding:utf-8 -*-
import csv
import codecs

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

class DictUnicodeWriter(object):

    def __init__(self, f, fieldnames, dialect=csv.excel, encoding="utf-8", **kwargs):
        # Redirect output to a queue
        self.queue = StringIO.StringIO()
        self.writer = csv.DictWriter(self.queue, fieldnames, dialect=dialect, **kwargs)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, D):
        self.writer.writerow(dict((k, v.encode("utf-8") if isinstance(v, unicode) else v) for k, v in D.iteritems()))

        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        try:
            data = data.decode("utf-8")
        except UnicodeDecodeError:
            data = data.decode("iso8859-1")

        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for D in rows:
            self.writerow(D)

    def writeheader(self):
        self.writer.writeheader()
