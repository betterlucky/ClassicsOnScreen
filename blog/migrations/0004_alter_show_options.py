# Generated by Django 4.2.4 on 2025-01-07 21:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_remove_show_title'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='show',
            options={'ordering': ['eventtime']},
        ),
    ]
