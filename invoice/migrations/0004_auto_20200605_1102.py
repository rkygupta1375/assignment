# Generated by Django 3.0.4 on 2020-06-05 05:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0003_auto_20200605_1059'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiveitem',
            name='File',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='invoice.File'),
        ),
    ]