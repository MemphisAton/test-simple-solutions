# Generated by Django 5.0 on 2023-12-30 13:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('simple_app', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='discount',
            old_name='amount',
            new_name='rate',
        ),
    ]
