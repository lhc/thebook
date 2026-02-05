"""
Configurações do Django Admin para fornecedores.
"""

from django.contrib import admin

from thebook.fornecedores.models import EntregaFornecedor, Fornecedor


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    """
    Exibe informações úteis para encontrar fornecedores rapidamente no admin.
    """

    list_display = ("nome", "documento", "email", "telefone", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "documento", "email")
    ordering = ("nome",)


@admin.register(EntregaFornecedor)
class EntregaFornecedorAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "fornecedor",
        "data_entrega",
        "qualidade",
        "valor_estimado",
    )
    list_filter = ("qualidade", "fornecedor")
    search_fields = ("titulo", "fornecedor__nome", "descricao")
    autocomplete_fields = ("fornecedor",)
