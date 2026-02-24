"""
Modelos da app de fornecedores.

Cada campo possui comentários para ajudar a entender o motivo de existir e
como o Django transforma isso em colunas no banco de dados.
"""

from django.db import models


class Fornecedor(models.Model):
    """
    Representa uma pessoa ou empresa que fornece produtos ou serviços.

    Optamos por um conjunto enxuto de campos. Alguns são obrigatórios
    (`nome`) e outros opcionais (`email`, `telefone` etc.) para termos
    flexibilidade no cadastro.
    """

    nome = models.CharField(
        max_length=255,
        verbose_name="Nome",
        help_text="Como o fornecedor deve aparecer nos relatórios.",
    )
    email = models.EmailField(
        max_length=254,
        verbose_name="E-mail",
        help_text="Contato principal (opcional).",
        blank=True,
    )
    telefone = models.CharField(
        max_length=32,
        verbose_name="Telefone",
        help_text="Telefone ou celular para contato rápido.",
        blank=True,
    )
    site = models.URLField(
        verbose_name="Site",
        help_text="Página oficial ou catálogo online.",
        blank=True,
    )
    documento = models.CharField(
        max_length=32,
        verbose_name="Documento",
        help_text="CNPJ, CPF ou outro identificador fiscal.",
        blank=True,
    )
    observacoes = models.TextField(
        verbose_name="Observações",
        help_text="Anote detalhes úteis como horários, contatos secundários etc.",
        blank=True,
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Use para arquivar fornecedores sem removê-los do histórico.",
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        # Representação amigável utilizada no Django Admin e em logs.
        return self.nome


class QualidadeEntrega(models.IntegerChoices):
    EXCELENTE = 1, "Excelente"
    BOA = 2, "Boa"
    REGULAR = 3, "Regular"
    RUIM = 4, "Ruim"


class EntregaFornecedor(models.Model):
    """
    Registro de itens/serviços fornecidos e avaliação rápida da qualidade.
    """

    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.CASCADE,
        related_name="entregas",
    )
    titulo = models.CharField(
        max_length=255,
        verbose_name="Título",
        help_text="Resumo curto do que foi entregue (ex.: Adesivos para evento).",
    )
    descricao = models.TextField(
        verbose_name="Descrição",
        help_text="Detalhe o pedido, quantidade, condições ou outros pontos.",
    )
    qualidade = models.IntegerField(
        choices=QualidadeEntrega.choices,
        default=QualidadeEntrega.BOA,
        verbose_name="Qualidade percebida",
        help_text="Como você classificaria o resultado desta entrega?",
    )
    data_entrega = models.DateField(
        verbose_name="Data da entrega",
        help_text="Quando o material/serviço foi recebido.",
    )
    valor_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor estimado",
        help_text="Opcional. Ajuda a comparar orçamentos e custos.",
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Notas sobre follow-up, pontos de atenção ou lições aprendidas.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_entrega", "-criado_em"]
        verbose_name = "Entrega do fornecedor"
        verbose_name_plural = "Entregas dos fornecedores"

    def __str__(self):
        return f"{self.titulo} ({self.fornecedor.nome})"
