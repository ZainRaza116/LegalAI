# Generated by Django 5.0.1 on 2024-01-23 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0004_remove_source_source_type_source_search_target'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='score',
            field=models.TextField(null=True),
        ),
    ]
