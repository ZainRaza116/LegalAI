# Generated by Django 5.0.1 on 2024-02-27 09:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0011_alter_briefarguments_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userbrief',
            name='statement_of_case',
            field=models.JSONField(null=True),
        ),
    ]
