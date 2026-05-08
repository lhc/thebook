# Integração com o Banco Cora

Duas ações podem ser realizadas no The Book em relação às movimentações
na conta bancária do Cora:

- Importação do extrato com as transações em Conta-Corrente (automatizado)
- Importação da fatura do Cartão de Crédito (semi-automatizado)

## Extrato da Conta-Corrente

O Cora não fornece nenhuma API ou Webhook que possamos utilizar para fazer a
ingestão automática das transações realizadas na Conta-Corrente, porém é
possível gerar relatórios enviados por e-mail nos formatos CSV, PDF e OFX. Esses
relatórios podem ser gerados manualmente ou configurados para que eles
sejam gerados e enviados automaticamente para endereços pré-determinados com
uma determinada freqüência. A menor freqüência possível é semanal (toda segunda-feira).

O The Book possui um importador capaz de processar os arquivos OFX gerados pelo
sistema do Cora. Este importador está localizado em
`integrations.cora.importers.ofx.CoraOFXImporter`.

Você pode enviar um desses arquivos manualmente na página de transações do The Book, dentro
da conta bancária "Cora" na opção "Import OFX". Instruções detalhadas de como gerar o arquivo
manualmente podem ser encontradas [aqui](https://discourse.lhc.net.br/t/importar-transa%C3%A7%C3%B5es-do-cora/1173).

Atualmente o sistema do Cora está configurado para que o arquivo OFX do mês atual seja enviado
semanalmente (todas as segundas-feira) para o endereço de e-mail thebook@lhc.net.br. A
caixa de entrada deste endereço pode ser processada através do comando de
gerenciamento localizado em `bookkeeping.management.process_cora_email` que irá verificar
novos e-mails, baixar o extrato em OFX e importá-lo automaticamente.

A execução deste comando de gerenciamento está sendo feita automaticamente semanalmente
através do Github Actions definido em `.github/workflows/process_cora_email.yml`. Assim
não é necessário fazer o processamento destes arquivos manualmente e os dados da conta
do Cora devem estar atualizados com os dados de pelo menos até a segunda-feira anterior
mais próxima.

> **É importante conferir se o processo está sendo realizado automaticamente. Caso perceba que
estamos a mais de uma semana sem nenhuma transação, verifique se o sistema está funcionando
corretamente.**

O arquivo OFX do Cora é bem definido, sendo possível importar o mesmo arquivo múltiplas vezes
e não ter nenhuma transação duplicada sendo inserida.

## Fatura do Cartão de Crédito

O Cora não fornece nenhuma API, Webhook ou a possibilidade de enviar automaticamente
um relatório das transações com Cartão de Crédito, porém é possível solicitar a
fatura em formato CSV manualmente para ser enviada para um e-mail determinado. Esta
fatura pode ser importada no sistema de maneira manual através do importador
`integrations.cora.importers.credit_card_invoice.CoraCreditCardInvoiceImporter`.

Após solicitar o arquivo CSV no aplicativo do Cora e baixá-lo para o seu endereço de
e-mail, você pode enviá-lo na página de transações do The Book, dentro
da conta bancária "Cora - Cartão de Crédito" na opção "Import Credit Card Cora CSV".

O arquivo CSV fornecido não possui um identificador único de cada transação, mas
o importador está configurado para considerar qualquer transação com a mesma
`description`, `amount` e `date` na conta "Cora - Cartão de Crédito" como duplicada,
**não sendo importadas em duplicidade**.

A transação de pagamento da fatura não aparece nesses relatório, porém ela está em débito
automático na conta-corrente e ao importar o extrato, essa transação será identificada
automaticamente, sendo lançada também na conta "Cora - Cartão de Crédito".
