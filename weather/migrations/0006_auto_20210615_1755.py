# Generated by Django 3.1.7 on 2021-06-15 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0005_auto_20210614_1223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='district',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]
