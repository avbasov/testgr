# Generated by Django 3.0.3 on 2020-04-02 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loader', '0006_bugs'),
    ]

    operations = [
        migrations.AddField(
            model_name='testsstorage',
            name='suppress',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
    ]