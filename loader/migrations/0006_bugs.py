# Generated by Django 3.0.3 on 2020-04-02 11:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('loader', '0005_testjobs_custom_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bugs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bug', models.CharField(blank=True, max_length=128, null=True)),
                ('type', models.SmallIntegerField(blank=True, null=True)),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bugs', to='loader.TestsStorage')),
            ],
        ),
    ]