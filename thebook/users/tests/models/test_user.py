import pytest

from django.contrib.auth import get_user_model


@pytest.mark.parametrize(
    "first_name,last_name,email,display_name",
    [
        (None, None, "tina.crawley@test.com", "tina.crawley@test.com"),
        ("Tina", None, "tina.crawley@test.com", "Tina"),
        ("Tina", "Crawley", "tina.crawley@test.com", "Tina Crawley"),
        (None, "Crawley", "tina.crawley@test.com", "Crawley"),
        ("Glenn C Jones", None, "glenn.jones@test.com", "Glenn C Jones"),
        ("Tina   ", "     Crawley", "tina.crawley@test.com", "Tina Crawley"),
    ],
)
def test_user_display_name(first_name, last_name, email, display_name):
    User = get_user_model()
    user = User(first_name=first_name, last_name=last_name, email=email)

    assert user.display_name == display_name
