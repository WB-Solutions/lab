# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lab', '0002_auto_20150713_1011'),
    ]

    operations = [
        migrations.AddField(
            model_name='forcevisit',
            name='name',
            field=models.CharField(default='', max_length=200, blank=True),
            preserve_default=False,
        ),
    ]
