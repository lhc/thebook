# Generated by Django 5.2 on 2025-04-07 20:47

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reimbursements", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="reimbursementrequest",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="reimbursementrequest",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
