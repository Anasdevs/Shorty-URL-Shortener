# Generated by Django 4.1.7 on 2023-09-07 12:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shortyapp', '0003_shorturl_created_at_alter_clickanalytics_timestamp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clickanalytics',
            name='ip_address',
        ),
    ]
