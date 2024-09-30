from thebook.bookkeeping.models import Category


def test_category_default_fetch_order_by_name(db):
    category_1 = Category.objects.create(name="Groceries")
    category_2 = Category.objects.create(name="Credits")
    category_3 = Category.objects.create(name="Expenses")

    categories = Category.objects.all()

    assert categories[0].name == category_2.name
    assert categories[1].name == category_3.name
    assert categories[2].name == category_1.name
