# Generated by Django 5.1.4 on 2024-12-23 17:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bookkeeping", "0007_alter_transaction_tags"),
    ]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="notes",
            field=models.CharField(max_length=64),
        ),
    ]