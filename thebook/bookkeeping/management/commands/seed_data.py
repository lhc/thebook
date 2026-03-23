import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import models, transaction

from thebook.bookkeeping.models import (
    BankAccount,
    Category,
    CategoryMatchRule,
    Transaction,
)
from thebook.members.models import (
    FeeIntervals,
    FeePaymentStatus,
    Member,
    Membership,
    PaymentMethod,
    ReceivableFee,
)

User = get_user_model()

# Livros de Caixa
CASH_BOOKS_DATA = [
    {
        "name": "Conta Corrente Principal",
        "description": "Conta principal do hackerspace - Nubank",
        "slug": "conta-principal",
        "active": True,
    },
    {
        "name": "Poupança LHC",
        "description": "Reserva para emergências",
        "slug": "poupanca",
        "active": True,
    },
]

# Membros
MEMBERS_DATA = [
    {
        "name": "Ana Carolina Silva",
        "email": "ana.silva@lhc.net.br",
        "phone": "(19) 99911-2233",
        "has_key": True,
        "start_date": "2023-06-01",
    },
    {
        "name": "Bruno Oliveira Santos",
        "email": "bruno.santos@lhc.net.br",
        "phone": "(19) 99922-3344",
        "has_key": True,
        "start_date": "2023-07-15",
    },
    {
        "name": "Carlos Eduardo Lima",
        "email": "carlos.lima@lhc.net.br",
        "phone": "(19) 99933-4455",
        "has_key": False,
        "start_date": "2023-08-01",
    },
    {
        "name": "Daniela Rodrigues",
        "email": "daniela.rodrigues@lhc.net.br",
        "phone": "(19) 99944-5566",
        "has_key": True,
        "start_date": "2023-09-10",
    },
    {
        "name": "Eduardo Ferreira Costa",
        "email": "eduardo.costa@lhc.net.br",
        "phone": "(19) 99955-6677",
        "has_key": False,
        "start_date": "2023-10-05",
    },
    {
        "name": "Fernanda Alves",
        "email": "fernanda.alves@lhc.net.br",
        "phone": "(19) 99966-7788",
        "has_key": True,
        "start_date": "2023-11-20",
    },
    {
        "name": "Gabriel Martins",
        "email": "gabriel.martins@lhc.net.br",
        "phone": "(19) 99977-8899",
        "has_key": False,
        "start_date": "2024-01-01",
    },
    {
        "name": "Helena Pereira",
        "email": "helena.pereira@lhc.net.br",
        "phone": "(19) 99988-9900",
        "has_key": True,
        "start_date": "2024-01-15",
    },
]

# Regras de Categorização
CATEGORIZATION_RULES = [
    {
        "priority": 1,
        "pattern": r".*mensalidade.*|.*contribuição.*",
        "category": "Contribuição Associativa",
        "tags": "mensalidade,membro",
    },
    {
        "priority": 2,
        "pattern": r".*pix.*|.*transferência.*",
        "category": "Transferência entre livros-caixa",
        "tags": "pix,transferencia",
    },
    {
        "priority": 3,
        "pattern": r".*tarifa.*|.*taxa.*",
        "category": "Tarifas Bancárias",
        "tags": "banco,tarifa",
    },
    {
        "priority": 4,
        "pattern": r".*aluguel.*|.*rent.*",
        "category": "Recorrente",
        "tags": "aluguel,recorrente",
    },
    {
        "priority": 5,
        "pattern": r".*energia.*|.*luz.*",
        "category": "Recorrente",
        "tags": "energia,recorrente",
    },
    {
        "priority": 6,
        "pattern": r".*internet.*|.*fibra.*",
        "category": "Recorrente",
        "tags": "internet,recorrente",
    },
    {
        "priority": 7,
        "pattern": r".*água.*|.*agua.*",
        "category": "Recorrente",
        "tags": "agua,recorrente",
    },
    {
        "priority": 8,
        "pattern": r".*manutenção.*|.*manutencao.*",
        "category": "Recorrente",
        "tags": "manutencao,equipamentos",
    },
]

# Transações de Janeiro 2024
JANUARY_TRANSACTIONS = [
    # MENSALIDADES
    {
        "date": "2024-01-05",
        "description": "PIX - Mensalidade Ana Carolina Silva",
        "amount": 89.00,
    },
    {
        "date": "2024-01-07",
        "description": "PIX - Mensalidade Bruno Oliveira Santos",
        "amount": 89.00,
    },
    {
        "date": "2024-01-10",
        "description": "PIX - Mensalidade Carlos Eduardo Lima",
        "amount": 89.00,
    },
    {
        "date": "2024-01-12",
        "description": "PIX - Mensalidade Daniela Rodrigues",
        "amount": 89.00,
    },
    {
        "date": "2024-01-15",
        "description": "PIX - Mensalidade Eduardo Ferreira Costa",
        "amount": 89.00,
    },
    {
        "date": "2024-01-18",
        "description": "PIX - Mensalidade Fernanda Alves",
        "amount": 89.00,
    },
    {
        "date": "2024-01-20",
        "description": "PIX - Mensalidade Gabriel Martins",
        "amount": 89.00,
    },
    {
        "date": "2024-01-22",
        "description": "PIX - Mensalidade Helena Pereira",
        "amount": 89.00,
    },
    # DOAÇÕES
    {
        "date": "2024-01-08",
        "description": "PIX - Doação para equipamentos",
        "amount": 150.00,
    },
    {"date": "2024-01-14", "description": "PIX - Doação anônima", "amount": 50.00},
    {
        "date": "2024-01-25",
        "description": "PIX - Doação para eventos",
        "amount": 200.00,
    },
    {"date": "2024-01-28", "description": "Dinheiro - Doação caixa", "amount": 25.00},
    # GASTOS
    {
        "date": "2024-01-03",
        "description": "Débito - Aluguel do espaço",
        "amount": -1200.00,
    },
    {
        "date": "2024-01-05",
        "description": "Débito - Energia elétrica",
        "amount": -180.50,
    },
    {
        "date": "2024-01-08",
        "description": "Débito - Internet fibra ótica",
        "amount": -89.90,
    },
    {"date": "2024-01-10", "description": "Débito - Água", "amount": -45.20},
    {
        "date": "2024-01-12",
        "description": "Débito - Material de limpeza",
        "amount": -67.80,
    },
    {"date": "2024-01-15", "description": "Débito - Tarifa bancária", "amount": -12.50},
    {
        "date": "2024-01-18",
        "description": "Débito - Manutenção equipamentos",
        "amount": -320.00,
    },
    {
        "date": "2024-01-22",
        "description": "Débito - Coffee break evento",
        "amount": -156.40,
    },
    {
        "date": "2024-01-25",
        "description": "Débito - Material para workshops",
        "amount": -89.90,
    },
    {
        "date": "2024-01-28",
        "description": "Débito - Taxa de processamento",
        "amount": -8.90,
    },
]

# Transações de Fevereiro 2024
FEBRUARY_TRANSACTIONS = [
    # MENSALIDADES
    {
        "date": "2024-02-05",
        "description": "PIX - Mensalidade Ana Carolina Silva",
        "amount": 89.00,
    },
    {
        "date": "2024-02-07",
        "description": "PIX - Mensalidade Bruno Oliveira Santos",
        "amount": 89.00,
    },
    {
        "date": "2024-02-10",
        "description": "PIX - Mensalidade Carlos Eduardo Lima",
        "amount": 89.00,
    },
    {
        "date": "2024-02-12",
        "description": "PIX - Mensalidade Daniela Rodrigues",
        "amount": 89.00,
    },
    {
        "date": "2024-02-15",
        "description": "PIX - Mensalidade Eduardo Ferreira Costa",
        "amount": 89.00,
    },
    {
        "date": "2024-02-18",
        "description": "PIX - Mensalidade Fernanda Alves",
        "amount": 89.00,
    },
    {
        "date": "2024-02-20",
        "description": "PIX - Mensalidade Gabriel Martins",
        "amount": 89.00,
    },
    {
        "date": "2024-02-22",
        "description": "PIX - Mensalidade Helena Pereira",
        "amount": 89.00,
    },
    # DOAÇÕES
    {
        "date": "2024-02-02",
        "description": "PIX - Doação para melhorias",
        "amount": 100.00,
    },
    {
        "date": "2024-02-14",
        "description": "PIX - Doação dia dos namorados",
        "amount": 75.00,
    },
    {"date": "2024-02-20", "description": "PIX - Doação anônima", "amount": 120.00},
    {"date": "2024-02-25", "description": "Dinheiro - Doação caixa", "amount": 30.00},
    # GASTOS
    {
        "date": "2024-02-03",
        "description": "Débito - Aluguel do espaço",
        "amount": -1200.00,
    },
    {
        "date": "2024-02-05",
        "description": "Débito - Energia elétrica",
        "amount": -195.30,
    },
    {
        "date": "2024-02-08",
        "description": "Débito - Internet fibra ótica",
        "amount": -89.90,
    },
    {"date": "2024-02-10", "description": "Débito - Água", "amount": -52.10},
    {
        "date": "2024-02-12",
        "description": "Débito - Material de escritório",
        "amount": -134.50,
    },
    {"date": "2024-02-15", "description": "Débito - Tarifa bancária", "amount": -12.50},
    {
        "date": "2024-02-18",
        "description": "Débito - Seguro do espaço",
        "amount": -89.90,
    },
    {
        "date": "2024-02-22",
        "description": "Débito - Lanches para reunião",
        "amount": -87.60,
    },
    {
        "date": "2024-02-25",
        "description": "Débito - Manutenção preventiva",
        "amount": -245.80,
    },
]


class Command(BaseCommand):
    help = "Cria dados iniciais completos para o sistema The Book - 2 meses de dados, 8 membros, R$89 mensais"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("🚀 Iniciando seed completo do sistema The Book...")
        )

        with transaction.atomic():
            # Reset completo
            self.reset_all_data()

            # Criar dados básicos
            self.create_bank_accounts()
            self.create_categorization_rules()

            # Criar membros e mensalidades
            self.create_members_and_memberships()

            # Criar transações
            self.create_transactions()

            # Categorizar transações automaticamente
            self.categorize_transactions()

            # Criar taxas a receber
            self.create_receivable_fees()

        self.stdout.write(self.style.SUCCESS("✅ Seed completo executado com sucesso!"))
        self.print_summary()

    def reset_all_data(self):
        """Remove todos os dados existentes"""
        self.stdout.write("🧹 Limpando dados existentes...")

        # Remover em ordem para evitar problemas de foreign key
        ReceivableFee.objects.all().delete()
        Membership.objects.all().delete()
        Member.objects.all().delete()
        Transaction.objects.all().delete()
        CategoryMatchRule.objects.all().delete()
        BankAccount.objects.all().delete()

        self.stdout.write("✅ Dados limpos com sucesso")

    def create_bank_accounts(self):
        """Cria livros de caixa"""
        self.stdout.write("🏦 Criando livros de caixa...")

        for bank_account_data in CASH_BOOKS_DATA:
            bank_account = BankAccount.objects.create(**bank_account_data)
            self.stdout.write(f"  ✅ {bank_account.name}")

    def create_categorization_rules(self):
        """Cria regras de categorização"""
        self.stdout.write("🏷️ Criando regras de categorização...")

        for rule_data in CATEGORIZATION_RULES:
            category, _ = Category.objects.get_or_create(name=rule_data["category"])

            CategoryMatchRule.objects.create(
                pattern=rule_data["pattern"],
                category=category,
                tags=rule_data.get("tags", ""),
            )
            self.stdout.write(f"  ✅ Regra: {rule_data['pattern']} -> {category.name}")

    def create_members_and_memberships(self):
        """Cria membros e suas mensalidades"""
        self.stdout.write("👥 Criando membros e mensalidades...")

        for member_data in MEMBERS_DATA:
            # Criar usuário
            user, created = User.objects.get_or_create(
                email=member_data["email"],
                defaults={
                    "first_name": member_data["name"].split()[0],
                    "last_name": " ".join(member_data["name"].split()[1:]),
                    "is_active": True,
                    "is_staff": False,
                },
            )

            # Definir senha padrão se o usuário foi criado
            if created:
                user.set_password("tijolo22")  # Senha padrão para desenvolvimento
                user.save()

            # Criar membro
            member = Member.objects.create(
                name=member_data["name"],
                phone_number=member_data["phone"],
                has_key=member_data["has_key"],
                user=user,
            )

            # Criar mensalidade
            start_date = datetime.datetime.strptime(
                member_data["start_date"], "%Y-%m-%d"
            ).date()
            membership = Membership.objects.create(
                member=member,
                start_date=start_date,
                membership_fee_amount=Decimal("89.00"),
                payment_interval=FeeIntervals.MONTHLY,
                payment_method=PaymentMethod.PIX,
                active=True,
            )

            self.stdout.write(f"  ✅ {member.name} - R$ 89,00/mês")

    def create_transactions(self):
        """Cria todas as transações"""
        self.stdout.write("💰 Criando transações...")

        # Buscar usuário admin (primeiro usuário criado)
        admin_user = User.objects.first()
        if not admin_user:
            admin_user = User.objects.create_user(
                email="admin@lhc.net.br",
                first_name="Admin",
                last_name="LHC",
                password="tijolo22",
                is_staff=True,
            )

        # Buscar livro de caixa principal
        main_bank_account = BankAccount.objects.get(slug="conta-principal")

        # Combinar todas as transações
        all_transactions = JANUARY_TRANSACTIONS + FEBRUARY_TRANSACTIONS

        for transaction_data in all_transactions:
            transaction_date = datetime.datetime.strptime(
                transaction_data["date"], "%Y-%m-%d"
            ).date()
            Transaction.objects.create(
                reference=f"SEED-{transaction_data['date']}-{hash(transaction_data['description']) % 10000}",
                date=transaction_date,
                description=transaction_data["description"],
                amount=Decimal(str(transaction_data["amount"])),
                bank_account=main_bank_account,
                created_by=admin_user,
            )

        self.stdout.write(f"  ✅ {len(all_transactions)} transações criadas")

    def categorize_transactions(self):
        """Aplica categorização automática"""
        self.stdout.write("🏷️ Aplicando categorização automática...")

        rules = CategoryMatchRule.objects.all()
        uncategorized_count = 0

        for transaction in Transaction.objects.all():
            transaction.categorize(rules=rules)
            if not transaction.category:
                uncategorized_count += 1

        self.stdout.write(
            f"  ✅ Categorização aplicada ({uncategorized_count} não categorizadas)"
        )

    def create_receivable_fees(self):
        """Associa transações existentes com taxas a receber"""
        self.stdout.write("📅 Associando transações com taxas a receber...")

        associated_count = 0

        for membership in Membership.objects.filter(active=True):
            # Buscar transações de mensalidade para este membro
            member_first_name = membership.member.name.split()[0]

            # Transações de janeiro
            jan_transactions = Transaction.objects.filter(
                description__icontains=member_first_name,
                date__year=2024,
                date__month=1,
                amount=Decimal("89.00"),
            )

            # Transações de fevereiro
            feb_transactions = Transaction.objects.filter(
                description__icontains=member_first_name,
                date__year=2024,
                date__month=2,
                amount=Decimal("89.00"),
            )

            # Associar transações com taxas a receber correspondentes
            for transaction in jan_transactions:
                # Buscar taxa a receber que corresponde a esta transação
                receivable_fee = ReceivableFee.objects.filter(
                    membership=membership,
                    start_date__year=2024,
                    start_date__month=1,
                    status=FeePaymentStatus.UNPAID,
                ).first()

                if receivable_fee and not receivable_fee.transaction:
                    receivable_fee.paid_with(transaction)
                    associated_count += 1

            for transaction in feb_transactions:
                # Buscar taxa a receber que corresponde a esta transação
                receivable_fee = ReceivableFee.objects.filter(
                    membership=membership,
                    start_date__year=2024,
                    start_date__month=2,
                    status=FeePaymentStatus.UNPAID,
                ).first()

                if receivable_fee and not receivable_fee.transaction:
                    receivable_fee.paid_with(transaction)
                    associated_count += 1

        self.stdout.write(
            f"  ✅ {associated_count} transações associadas com taxas a receber"
        )

    def print_summary(self):
        """Imprime resumo dos dados criados"""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("📊 RESUMO DO SEED:"))
        self.stdout.write("=" * 50)
        self.stdout.write(f"🏦 Livros de Caixa: {BankAccount.objects.count()}")
        self.stdout.write(f"👥 Membros: {Member.objects.count()}")
        self.stdout.write(f"💰 Transações: {Transaction.objects.count()}")
        self.stdout.write(f"🏷️ Categorias: {Category.objects.count()}")
        self.stdout.write(
            f"📋 Regras de Categorização: {CategoryMatchRule.objects.count()}"
        )
        self.stdout.write(f"📅 Taxas a Receber: {ReceivableFee.objects.count()}")
        self.stdout.write(f"👤 Usuários: {User.objects.count()}")

        # Resumo financeiro
        total_deposits = Transaction.objects.filter(amount__gt=0).aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0")

        total_withdraws = Transaction.objects.filter(amount__lt=0).aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0")

        balance = total_deposits + total_withdraws

        self.stdout.write("\n💰 RESUMO FINANCEIRO:")
        self.stdout.write(f"  📈 Total Depósitos: R$ {total_deposits:,.2f}")
        self.stdout.write(f"  📉 Total Saques: R$ {total_withdraws:,.2f}")
        self.stdout.write(f"  💰 Saldo Total: R$ {balance:,.2f}")

        self.stdout.write("\n🚀 Sistema pronto para uso!")
        self.stdout.write("   Acesse: http://127.0.0.1:8000")
        self.stdout.write("   Admin: http://127.0.0.1:8000/admin")

        self.stdout.write("\n🔑 CREDENCIAIS DE ACESSO:")
        self.stdout.write("   Senha padrão para todos: tijolo22")
        self.stdout.write("   👑 ADMINISTRADOR:")
        self.stdout.write("     • admin@lhc.net.br (superuser)")
        self.stdout.write("   👥 MEMBROS:")
        for member in Member.objects.all():
            self.stdout.write(f"     • {member.name}: {member.user.email}")
