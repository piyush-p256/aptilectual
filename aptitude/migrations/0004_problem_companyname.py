# Generated by Django 5.0.7 on 2025-01-30 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aptitude', '0003_problem_answerurl'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='companyname',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
