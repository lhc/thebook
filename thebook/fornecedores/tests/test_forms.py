"""
Testes para o formulário de fornecedores.
"""

from datetime import date

from django.test import TestCase

from thebook.fornecedores.forms import EntregaFornecedorForm, FornecedorForm


class FornecedorFormTest(TestCase):
    def test_form_valido_com_campos_minimos(self):
        form = FornecedorForm(data={"nome": "LHC Supplies"})
        self.assertTrue(form.is_valid())

    def test_form_invalido_quando_nome_vazio(self):
        form = FornecedorForm(data={"nome": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("nome", form.errors)


class EntregaFornecedorFormTest(TestCase):
    def test_form_valido(self):
        form = EntregaFornecedorForm(
            data={
                "titulo": "Compra de parafusos",
                "descricao": "Caixa com 500 unidades, inox.",
                "qualidade": 2,
                "data_entrega": date.today(),
                "valor_estimado": "120.00",
            }
        )
        self.assertTrue(form.is_valid())
