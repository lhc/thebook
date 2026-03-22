"""
Formulários relacionados a fornecedores.

Ao invés de reescrevermos toda a lógica de persistência manualmente, usamos
`ModelForm`, que já sabe criar/atualizar objetos do modelo `Fornecedor`.
"""

from django import forms

from thebook.fornecedores.models import EntregaFornecedor, Fornecedor, QualidadeEntrega


class FornecedorForm(forms.ModelForm):
    """
    Formulário com labels e mensagens em português.

    O Django vai gerar os campos automaticamente a partir do modelo, mas aqui
    conseguimos ajustar textos para tornar o formulário mais amigável.
    """

    class Meta:
        model = Fornecedor
        fields = [
            "nome",
            "documento",
            "email",
            "telefone",
            "site",
            "observacoes",
            "ativo",
        ]
        labels = {
            "nome": "Nome do fornecedor",
            "documento": "Documento (CNPJ/CPF)",
            "email": "E-mail",
            "telefone": "Telefone",
            "site": "Site",
            "observacoes": "Observações",
            "ativo": "Fornecedor ativo?",
        }


class EntregaFornecedorForm(forms.ModelForm):
    class Meta:
        model = EntregaFornecedor
        fields = [
            "titulo",
            "descricao",
            "qualidade",
            "data_entrega",
            "valor_estimado",
            "observacoes",
        ]
        labels = {
            "titulo": "O que foi entregue?",
            "descricao": "Detalhes",
            "qualidade": "Qualidade percebida",
            "data_entrega": "Data da entrega",
            "valor_estimado": "Valor (opcional)",
            "observacoes": "Observações adicionais",
        }
        help_texts = {
            "qualidade": "Escolha a opção que melhor resume a experiência.",
            "valor_estimado": "Use ponto para separar decimais: 1234.56",
        }
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control",
                    "placeholder": "Ex.: Pedido de 200 adesivos, impressão vinílica, entrega expressa.",
                }
            ),
            "qualidade": forms.Select(
                attrs={"class": "form-control"},
                choices=QualidadeEntrega.choices,
            ),
            "data_entrega": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "valor_estimado": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "observacoes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control",
                    "placeholder": "Use para registrar feedback, próximos passos, responsáveis etc.",
                }
            ),
        }
        help_texts = {
            "documento": "Opcional. Use para facilitar buscas ou gerar relatórios.",
            "observacoes": "Guarde informações importantes: prazos, pessoa de contato etc.",
            "ativo": "Desmarque para arquivar o fornecedor sem remover seus dados.",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "documento": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "site": forms.URLInput(attrs={"class": "form-control"}),
            "observacoes": forms.Textarea(
                attrs={
                    "rows": 5,
                    "class": "form-control",
                    "placeholder": "Ex.: horários de atendimento, políticas de pagamento, contatos adicionais…",
                }
            ),
            "ativo": forms.CheckboxInput(
                attrs={
                    "class": "custom-control-input",
                }
            ),
        }
