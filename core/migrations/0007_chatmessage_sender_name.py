# Generated by Django 5.1.6 on 2025-03-12 23:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_chatmessage_sender_chatmessage_sender_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='sender_name',
            field=models.CharField(default='santhosh', help_text='Name of the sender', max_length=255),
            preserve_default=False,
        ),
    ]
