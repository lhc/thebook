import csv
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from thebook.bookkeeping.models import BankAccount, Transaction
from thebook.fornecedores.forms import EntregaFornecedorForm, FornecedorForm
from thebook.fornecedores.models import EntregaFornecedor, Fornecedor


@login_required
def listar_fornecedores(request):
    """
    Lista todos os fornecedores cadastrados.

    - Obtém todos os objetos da tabela.
    - Renderiza o template passando a lista no contexto.
    """

    fornecedores = Fornecedor.objects.all()
    return render(
        request,
        "fornecedores/listar.html",
        {"fornecedores": fornecedores},
    )


@login_required
def detalhar_fornecedor(request, fornecedor_id):
    """
    Mostra os detalhes de um fornecedor específico.

    `get_object_or_404` tenta buscar o fornecedor e, se não existir,
    levanta um erro 404 automaticamente.
    """

    fornecedor = get_object_or_404(Fornecedor, pk=fornecedor_id)
    entregas = fornecedor.entregas.select_related("fornecedor")

    transactions = fornecedor.transactions.select_related("category").order_by("-date")

    return render(
        request,
        "fornecedores/detalhe.html",
        {
            "fornecedor": fornecedor,
            "entregas": entregas,
            "transactions": transactions,
        },
    )


@login_required
def criar_fornecedor(request):
    """
    Cria um novo fornecedor.

    - GET  -> exibe o formulário vazio.
    - POST -> valida os dados, salva e redireciona para a lista.
    """

    if request.method == "POST":
        form = FornecedorForm(request.POST)
        if form.is_valid():
            novo_fornecedor = form.save()
            messages.success(
                request,
                f"Fornecedora(o) '{novo_fornecedor.nome}' criada(o) com sucesso!",
            )
            return redirect("fornecedores:listar")
    else:
        form = FornecedorForm()

    return render(
        request,
        "fornecedores/formulario.html",
        {"form": form, "titulo": "Cadastrar fornecedor"},
    )


@login_required
def editar_fornecedor(request, fornecedor_id):
    """
    Atualiza um fornecedor existente.

    A diferença principal em relação a `criar_fornecedor` é que passamos
    o `instance` para o `FornecedorForm`, permitindo editar os dados.
    """

    fornecedor = get_object_or_404(Fornecedor, pk=fornecedor_id)

    if request.method == "POST":
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            fornecedor_atualizado = form.save()
            messages.success(
                request,
                f"Fornecedora(o) '{fornecedor_atualizado.nome}' atualizada(o) com sucesso!",
            )
            return redirect("fornecedores:listar")
    else:
        form = FornecedorForm(instance=fornecedor)

    return render(
        request,
        "fornecedores/formulario.html",
        {
            "form": form,
            "titulo": f"Editar fornecedor — {fornecedor.nome}",
        },
    )


@login_required
def excluir_fornecedor(request, fornecedor_id):
    """
    Exclui um fornecedor após confirmação.

    - GET  -> mostra uma página de confirmação.
    - POST -> realiza a exclusão e redireciona.
    """

    fornecedor = get_object_or_404(Fornecedor, pk=fornecedor_id)

    if request.method == "POST":
        nome = fornecedor.nome
        fornecedor.delete()
        messages.success(request, f"Fornecedora(o) '{nome}' removida(o) com sucesso!")
        return redirect("fornecedores:listar")

    return render(
        request,
        "fornecedores/confirmar_exclusao.html",
        {"fornecedor": fornecedor},
    )


@login_required
def criar_entrega(request, fornecedor_id):
    """
    Cria uma nova entrega associada a um fornecedor.

    - GET  -> exibe o formulário de criação.
    - POST -> valida, salva e redireciona (ou retorna formulário com erros).

    Suporta HTMX: em requisições HTMX, retorna HTML parcial ou redireciona via HX-Redirect.
    """
    fornecedor = get_object_or_404(Fornecedor, pk=fornecedor_id)
    is_htmx = request.headers.get("HX-Request") == "true"

    if request.method == "POST":
        form = EntregaFornecedorForm(request.POST)
        if form.is_valid():
            entrega = form.save(commit=False)
            entrega.fornecedor = fornecedor
            entrega.save()
            messages.success(
                request,
                "Entrega registrada com sucesso!",
            )

            # Se for requisição HTMX, retorna redirecionamento via header
            if is_htmx:
                response = HttpResponse()
                response["HX-Redirect"] = reverse(
                    "fornecedores:detalhar", args=[fornecedor.id]
                )
                return response

            # Senão, redireciona normalmente
            return redirect("fornecedores:detalhar", fornecedor.id)
    else:
        form = EntregaFornecedorForm()

    return render(
        request,
        "fornecedores/entrega_formulario.html",
        {
            "form": form,
            "fornecedor": fornecedor,
            "titulo": f"Registrar entrega — {fornecedor.nome}",
        },
    )


@login_required
def editar_entrega(request, fornecedor_id, entrega_id):
    """
    Edita uma entrega existente associada a um fornecedor.

    - GET  -> exibe o formulário pré-preenchido com os dados atuais.
    - POST -> valida, atualiza e redireciona (ou retorna formulário com erros).

    Suporta HTMX: em requisições HTMX, retorna HTML parcial ou redireciona via HX-Redirect.
    """
    fornecedor = get_object_or_404(Fornecedor, pk=fornecedor_id)
    entrega = get_object_or_404(EntregaFornecedor, pk=entrega_id, fornecedor=fornecedor)
    is_htmx = request.headers.get("HX-Request") == "true"

    if request.method == "POST":
        form = EntregaFornecedorForm(request.POST, instance=entrega)
        if form.is_valid():
            form.save()
            messages.success(request, "Entrega atualizada com sucesso!")

            # Se for requisição HTMX, retorna redirecionamento via header
            if is_htmx:
                response = HttpResponse()
                response["HX-Redirect"] = reverse(
                    "fornecedores:detalhar", args=[fornecedor.id]
                )
                return response

            # Senão, redireciona normalmente
            return redirect("fornecedores:detalhar", fornecedor.id)
    else:
        form = EntregaFornecedorForm(instance=entrega)

    return render(
        request,
        "fornecedores/entrega_formulario.html",
        {
            "form": form,
            "fornecedor": fornecedor,
            "entrega": entrega,
            "titulo": f"Editar entrega — {entrega.titulo}",
        },
    )


@login_required
def excluir_entrega(request, fornecedor_id, entrega_id):
    fornecedor = get_object_or_404(Fornecedor, pk=fornecedor_id)
    entrega = get_object_or_404(EntregaFornecedor, pk=entrega_id, fornecedor=fornecedor)

    if request.method == "POST":
        titulo = entrega.titulo
        entrega.delete()
        messages.success(
            request,
            f"Entrega '{titulo}' removida com sucesso!",
        )
        return redirect("fornecedores:detalhar", fornecedor.id)

    return render(
        request,
        "fornecedores/confirmar_exclusao_entrega.html",
        {
            "fornecedor": fornecedor,
            "entrega": entrega,
        },
    )


@login_required
def vincular_transacoes(request, fornecedor_id):
    """
    Permite vincular múltiplas transações a um fornecedor.
    Lista transações filtradas por mês/ano, similar ao livro caixa.
    """
    fornecedor = get_object_or_404(Fornecedor, pk=fornecedor_id)

    # Filtros de Data (usado tanto no POST quanto no GET)
    today = datetime.date.today()
    try:
        month = int(request.GET.get("month", today.month))
    except (ValueError, TypeError):
        month = today.month

    try:
        year = int(request.GET.get("year", today.year))
    except (ValueError, TypeError):
        year = today.year

    # Processar o formulário de vinculação/desvinculação
    if request.method == "POST":
        selected_ids = set(request.POST.getlist("transaction_ids"))

        # Buscar todas as transações do período atual que estão vinculadas a este fornecedor
        # e que estão visíveis na página atual (com os filtros aplicados)
        period_transactions = Transaction.objects.filter(
            date__year=year, date__month=month, fornecedor=fornecedor
        )

        # Aplicar filtros adicionais se existirem
        search_query = request.GET.get("q", "")
        bank_account_filter = request.GET.get("bank_account", "")

        if search_query:
            period_transactions = period_transactions.filter(
                Q(description__icontains=search_query)
                | Q(amount__icontains=search_query)
            )
        if bank_account_filter:
            period_transactions = period_transactions.filter(
                bank_account__slug=bank_account_filter
            )

        # IDs das transações que devem estar vinculadas (marcadas)
        selected_ids_int = {int(id) for id in selected_ids if id}

        # IDs das transações que estão vinculadas mas foram desmarcadas
        currently_linked_ids = set(period_transactions.values_list("id", flat=True))
        to_unlink_ids = currently_linked_ids - selected_ids_int

        # Vincular as selecionadas
        linked_count = 0
        if selected_ids_int:
            transactions_to_link = Transaction.objects.filter(id__in=selected_ids_int)
            linked_count = transactions_to_link.update(fornecedor=fornecedor)

        # Desvincular as que foram desmarcadas
        unlinked_count = 0
        if to_unlink_ids:
            transactions_to_unlink = Transaction.objects.filter(id__in=to_unlink_ids)
            unlinked_count = transactions_to_unlink.update(fornecedor=None)

        # Mensagem de sucesso
        if linked_count > 0 or unlinked_count > 0:
            msg_parts = []
            if linked_count > 0:
                msg_parts.append(f"{linked_count} transação(ões) vinculada(s)")
            if unlinked_count > 0:
                msg_parts.append(f"{unlinked_count} transação(ões) desvinculada(s)")
            messages.success(request, f"{' e '.join(msg_parts)} com sucesso!")
        else:
            messages.info(request, "Nenhuma alteração realizada.")

        # Construir URL com parâmetros preservados
        url = reverse("fornecedores:vincular-transacoes", args=[fornecedor.id])
        # Preservar todos os parâmetros GET
        query_params = request.GET.copy()
        if query_params:
            url = f"{url}?{query_params.urlencode()}"

        # Redirecionar mantendo os filtros (POST-redirect-GET pattern)
        return redirect(url)

    # Navegação de períodos
    reference_date = datetime.date(year, month, 1)

    # Mês anterior
    previous_date = reference_date - datetime.timedelta(days=1)
    previous_period = f"month={previous_date.month}&year={previous_date.year}"

    # Próximo mês
    next_date_temp = reference_date + datetime.timedelta(days=32)
    next_date = datetime.date(next_date_temp.year, next_date_temp.month, 1)
    next_period = f"month={next_date.month}&year={next_date.year}"

    # Filtros Adicionais
    search_query = request.GET.get("q", "")
    bank_account_filter = request.GET.get("bank_account", "")

    # Query Base - Todas as transações do período
    transactions = (
        Transaction.objects.filter(date__year=year, date__month=month)
        .order_by("-date")
        .select_related("bank_account", "category", "fornecedor")
    )

    if search_query:
        transactions = transactions.filter(
            Q(description__icontains=search_query) | Q(amount__icontains=search_query)
        )

    if bank_account_filter:
        transactions = transactions.filter(bank_account__slug=bank_account_filter)

    bank_accounts = BankAccount.objects.filter(active=True)

    return render(
        request,
        "fornecedores/vincular_transacoes.html",
        {
            "fornecedor": fornecedor,
            "transactions": transactions,
            "bank_accounts": bank_accounts,
            "search_query": search_query,
            "current_bank_account": bank_account_filter,
            "year": year,
            "month": month,
            "previous_period": previous_period,
            "next_period": next_period,
        },
    )
