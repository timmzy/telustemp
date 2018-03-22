import csv
from django.db import transaction
from django.contrib.redirects.models import Redirect
from django.contrib.sites.models import Site
from django.conf import settings


site = Site.objects.get(pk=settings.SITE_ID)

def redirectIt(csvObj, which):
    try:
        text = [line.decode('latin-1') for line in csvObj.readlines()]
        try:
            readCsv = csv.reader(text, delimiter=";")
        except:
            readCsv = csv.reader(text, delimiter=",")
        if which == 2:
            get = Redirect.objects.all()
            get.delete()
        for ind, row in enumerate(readCsv):
            if ind == 0:
                continue
            url1 = row[1]
            url2 = row[2]
            try:
                with transaction.atomic():
                    Redirect.objects.create(site=site, old_path=url1, new_path=url2)
            except:pass
        return 1
    except:
        return 0
