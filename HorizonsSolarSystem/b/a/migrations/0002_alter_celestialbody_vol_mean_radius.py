# Generated by Django 5.1.1 on 2024-09-18 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='celestialbody',
            name='vol_mean_radius',
            field=models.FloatField(blank=True, help_text='Volume mean radius in km', null=True),
        ),
    ]
