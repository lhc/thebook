"""
Testes para o modelo Fornecedor.
"""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from thebook.fornecedores.models import (
    EntregaFornecedor,
    Fornecedor,
    QualidadeEntrega,
)


class FornecedorModelTest(TestCase):
    def setUp(self):
        self.fornecedor = Fornecedor.objects.create(nome="Loja do Tio Zé")

    def test_str_retorna_nome(self):
        self.assertEqual(str(self.fornecedor), "Loja do Tio Zé")

    def test_ordering_por_nome(self):
        Fornecedor.objects.create(nome="Alpha")
        Fornecedor.objects.create(nome="Beta")

        nomes = list(Fornecedor.objects.values_list("nome", flat=True))
        self.assertEqual(nomes, ["Alpha", "Beta", "Loja do Tio Zé"])


class EntregaFornecedorModelTest(TestCase):
    def setUp(self):
        self.fornecedor = Fornecedor.objects.create(nome="Print Lab")

    def test_cria_entrega_e_str(self):
        entrega = EntregaFornecedor.objects.create(
            fornecedor=self.fornecedor,
            titulo="Lotes de adesivos",
            descricao="200 unidades, acabamento fosco",
            qualidade=QualidadeEntrega.EXCELENTE,
            data_entrega=timezone.now().date(),
            valor_estimado=Decimal("320.50"),
        )

        self.assertEqual(str(entrega), "Lotes de adesivos (Print Lab)")
        self.assertEqual(entrega.fornecedor, self.fornecedor)
