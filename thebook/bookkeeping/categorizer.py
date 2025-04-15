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
        if re.match(self.pattern, transaction.description, re.IGNORECASE):
            transaction.category = self.category
            applied = True
        return transaction, applied
