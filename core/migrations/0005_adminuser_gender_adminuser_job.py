# Generated by Django 5.1.6 on 2025-03-03 18:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_adminuser_verified_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminuser',
            name='gender',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='adminuser',
            name='job',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
