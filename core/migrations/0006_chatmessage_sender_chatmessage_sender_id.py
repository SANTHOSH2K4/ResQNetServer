# Generated by Django 5.1.6 on 2025-03-12 23:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_chatmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='sender',
            field=models.CharField(choices=[('admin', 'Admin'), ('general', 'General User')], default='general', help_text='Indicates if the sender is an admin or a general user', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='sender_id',
            field=models.PositiveIntegerField(default='1', help_text='Stores the ID of either an AdminUser or a GeneralUser'),
            preserve_default=False,
        ),
    ]
