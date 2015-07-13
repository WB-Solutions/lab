# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lab', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='forcevisit',
            name='f_contact',
            field=models.CharField(default=b'Presencial', max_length=30, choices=[(b'Presencial', b'Presencial'), (b'Telefonica', b'Telefonica'), (b'Web', b'Web')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='forcevisit',
            name='f_goal',
            field=models.CharField(default=b'Presentacion Inicial', max_length=30, choices=[(b'Presentacion Inicial', b'Presentacion Inicial'), (b'Promocion', b'Promocion'), (b'Pedido', b'Pedido'), (b'Negociar', b'Negociar')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='forcevisit',
            name='f_option',
            field=models.CharField(default=b'Planeada', max_length=30, choices=[(b'Planeada', b'Planeada'), (b'Re-agendada', b'Re-agendada'), (b'Asignada', b'Asignada')]),
            preserve_default=True,
        ),
    ]
