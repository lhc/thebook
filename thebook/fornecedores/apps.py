from django.apps import AppConfig


class FornecedoresConfig(AppConfig):
    """
    Configuração da aplicação de fornecedores.

    O atributo `name` precisa apontar para o caminho completo da app para que
    o Django consiga encontrá-la corretamente quando adicionarmos em
    `INSTALLED_APPS`.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "thebook.fornecedores"
    verbose_name = "Fornecedores"
