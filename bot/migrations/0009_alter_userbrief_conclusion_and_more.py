# Generated by Django 5.0.1 on 2024-02-13 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0008_alter_userbrief_attorneys_alter_userbrief_court_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userbrief',
            name='conclusion',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='userbrief',
            name='statement_of_case',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='userbrief',
            name='summary_of_arguments',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='userbrief',
            name='table_of_authorities',
            field=models.JSONField(null=True),
        ),
    ]
