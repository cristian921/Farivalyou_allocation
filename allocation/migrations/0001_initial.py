# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-02-12 09:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('codec', models.CharField(max_length=8, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Series',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.FloatField()),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='allocation.Asset')),
            ],
        ),
    ]
