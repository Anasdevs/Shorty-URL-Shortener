# Generated by Django 4.1.7 on 2023-08-31 05:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shortyapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shorturl',
            name='click_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
