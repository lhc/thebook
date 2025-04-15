import re
from dataclasses import dataclass
from decimal import Decimal


@dataclass()
class CategoryRule:
    pattern: str
    category: "Category"
    value: Decimal = None
    comparison_function: str = None
    tags: list[str] = None

    def apply_rule(self, transaction):
        applied = False
        if self.tags and not transaction.id:
            raise ValueError(
                "You need to save the transaction before adding tags to it."
            )

        string_pattern_matched = bool(
            re.match(self.pattern, transaction.description, re.IGNORECASE)
        )

        if self.value:
            value_matched = False
            if self.comparison_function == "EQ" and transaction.amount == self.value:
                value_matched = True
            elif self.comparison_function == "LTE" and transaction.amount <= self.value:
                value_matched = True
            elif self.comparison_function == "GTE" and transaction.amount >= self.value:
                value_matched = True
        else:
            value_matched = True

        applied = all(
            [
                string_pattern_matched,
                value_matched,
            ]
        )
        if applied:
            transaction.category = self.category
            if self.tags:
                transaction.tags.add(*self.tags)
            transaction.save()

        return transaction, applied
