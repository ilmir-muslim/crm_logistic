# logistic/migrations/0010_rename_address_fields.py
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("logistic", "0009_remove_deliveryorder_delivery_address_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="deliveryorder",
            old_name="sender_address",
            new_name="pickup_address",
        ),
        migrations.RenameField(
            model_name="deliveryorder",
            old_name="recipient_address",
            new_name="delivery_address",
        ),
    ]
