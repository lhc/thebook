"""
Testes de integração das views de fornecedores.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from thebook.fornecedores.models import EntregaFornecedor, Fornecedor, QualidadeEntrega


class FornecedorViewsTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="senha-segura",
        )
        self.client.force_login(self.user)

    def test_listar_fornecedores(self):
        Fornecedor.objects.create(nome="Fornecedor X")

        resposta = self.client.get(reverse("fornecedores:listar"))

        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "fornecedores/listar.html")
        self.assertContains(resposta, "Fornecedor X")

    def test_criar_fornecedor(self):
        resposta = self.client.post(
            reverse("fornecedores:criar"),
            data={"nome": "Novo fornecedor"},
            follow=True,
        )

        self.assertRedirects(resposta, reverse("fornecedores:listar"))
        self.assertTrue(
            Fornecedor.objects.filter(nome="Novo fornecedor").exists(),
        )

    def test_editar_fornecedor(self):
        fornecedor = Fornecedor.objects.create(nome="Fornecedor Original")

        resposta = self.client.post(
            reverse("fornecedores:editar", args=[fornecedor.id]),
            data={"nome": "Fornecedor Atualizado"},
            follow=True,
        )

        self.assertRedirects(resposta, reverse("fornecedores:listar"))
        fornecedor.refresh_from_db()
        self.assertEqual(fornecedor.nome, "Fornecedor Atualizado")

    def test_excluir_fornecedor(self):
        fornecedor = Fornecedor.objects.create(nome="Fornecedor Apagar")

        resposta = self.client.post(
            reverse("fornecedores:excluir", args=[fornecedor.id]),
            follow=True,
        )

        self.assertRedirects(resposta, reverse("fornecedores:listar"))
        self.assertFalse(Fornecedor.objects.filter(id=fornecedor.id).exists())

    def test_detalhar_fornecedor(self):
        fornecedor = Fornecedor.objects.create(nome="Fornecedor Detalhe")

        resposta = self.client.get(
            reverse("fornecedores:detalhar", args=[fornecedor.id])
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "fornecedores/detalhe.html")
        self.assertContains(resposta, "Fornecedor Detalhe")

    def test_criar_entrega(self):
        fornecedor = Fornecedor.objects.create(nome="Fornecedor Entrega")

        resposta = self.client.post(
            reverse("fornecedores:entrega-criar", args=[fornecedor.id]),
            data={
                "titulo": "Compra de adesivos",
                "descricao": "200 unidades",
                "qualidade": QualidadeEntrega.BOA,
                "data_entrega": date.today(),
            },
            follow=True,
        )

        self.assertRedirects(
            resposta, reverse("fornecedores:detalhar", args=[fornecedor.id])
        )
        self.assertTrue(
            fornecedor.entregas.filter(titulo="Compra de adesivos").exists()
        )

    def test_editar_entrega(self):
        fornecedor = Fornecedor.objects.create(nome="Fornecedor Edição")
        entrega = EntregaFornecedor.objects.create(
            fornecedor=fornecedor,
            titulo="Entrega antiga",
            descricao="Teste",
            qualidade=QualidadeEntrega.REGULAR,
            data_entrega=date.today(),
        )

        resposta = self.client.post(
            reverse(
                "fornecedores:entrega-editar",
                args=[fornecedor.id, entrega.id],
            ),
            data={
                "titulo": "Entrega atualizada",
                "descricao": "Atualizado",
                "qualidade": QualidadeEntrega.EXCELENTE,
                "data_entrega": date.today(),
            },
            follow=True,
        )

        self.assertRedirects(
            resposta, reverse("fornecedores:detalhar", args=[fornecedor.id])
        )
        entrega.refresh_from_db()
        self.assertEqual(entrega.titulo, "Entrega atualizada")

    def test_excluir_entrega(self):
        fornecedor = Fornecedor.objects.create(nome="Fornecedor Excluir")
        entrega = EntregaFornecedor.objects.create(
            fornecedor=fornecedor,
            titulo="Entrega será apagada",
            descricao="Teste",
            qualidade=QualidadeEntrega.BOA,
            data_entrega=date.today(),
        )

        resposta = self.client.post(
            reverse(
                "fornecedores:entrega-excluir",
                args=[fornecedor.id, entrega.id],
            ),
            follow=True,
        )

        self.assertRedirects(
            resposta, reverse("fornecedores:detalhar", args=[fornecedor.id])
        )
        self.assertFalse(fornecedor.entregas.exists())
