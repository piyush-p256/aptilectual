# Generated by Django 5.0.7 on 2025-04-26 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aptitude', '0012_achievement_customuser_bio_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='branch',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='contact_number',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='end_year',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='enrollment_number',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='start_year',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
