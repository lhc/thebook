# Generated by Django 5.0 on 2024-08-23 19:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bookkeeping", "0003_document_notes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="reference",
            field=models.CharField(max_length=36, unique=True),
        ),
    ]
