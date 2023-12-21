import uuid

from django.db import migrations, models


def set_reference_value_to_transaction(apps, schema_editor):
    # Ensure that existing Transaction has a unique reference ID
    Transaction = apps.get_model("bookkeeping", "Transaction")
    transactions = Transaction.objects.all()
    for transaction in transactions:
        transaction.reference = uuid.uuid4().hex
        transaction.save()


class Migration(migrations.Migration):
    dependencies = [
        ("bookkeeping", "0002_order_transaction_retrieval_default_ordering_by_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="reference",
            field=models.CharField(default="", max_length=32),
            preserve_default=False,
        ),
        migrations.RunPython(set_reference_value_to_transaction, atomic=True),
        migrations.AlterField(
            model_name="transaction",
            name="reference",
            field=models.CharField(max_length=32, unique=True),
        ),
    ]
