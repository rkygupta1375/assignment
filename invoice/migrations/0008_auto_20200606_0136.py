# Generated by Django 3.0.4 on 2020-06-05 20:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0007_auto_20200606_0114'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiceitem',
            name='File',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='iteminfo', to='invoice.File'),
        ),
    ]
