"""
Rotas da aplicação de fornecedores.

Separar as URLs por app ajuda a manter o projeto organizado.
"""

from django.urls import path

from thebook.fornecedores import views

app_name = "fornecedores"

urlpatterns = [
    path("", views.listar_fornecedores, name="listar"),
    path("novo/", views.criar_fornecedor, name="criar"),
    path("<int:fornecedor_id>/", views.detalhar_fornecedor, name="detalhar"),
    path("<int:fornecedor_id>/editar/", views.editar_fornecedor, name="editar"),
    path("<int:fornecedor_id>/excluir/", views.excluir_fornecedor, name="excluir"),
    path(
        "<int:fornecedor_id>/entregas/novo/",
        views.criar_entrega,
        name="entrega-criar",
    ),
    path(
        "<int:fornecedor_id>/entregas/<int:entrega_id>/editar/",
        views.editar_entrega,
        name="entrega-editar",
    ),
    path(
        "<int:fornecedor_id>/entregas/<int:entrega_id>/excluir/",
        views.excluir_entrega,
        name="entrega-excluir",
    ),
    path(
        "<int:fornecedor_id>/vincular-transacoes/",
        views.vincular_transacoes,
        name="vincular-transacoes",
    ),
]
