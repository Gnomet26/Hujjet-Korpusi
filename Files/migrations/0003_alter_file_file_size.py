# Generated by Django 5.2.3 on 2025-07-02 05:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Files', '0002_file_is_verified'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='file_size',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
