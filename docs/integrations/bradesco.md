# Integração com o Banco Bradesco

## Extrato da Conta-Corrente (processo manual)

O Bradesco não fornece nenhuma API ou Webhook que possamos utilizar para fazer a
ingestão automática das transações realizadas na Conta-Corrente. Porém temos um
importador que aceita o arquivo OFX que conseguimos baixar dentro do Internet Banking
do Bradesco. Este importador está localizado em `integrations.bradesco.importers.ofx.OFXImporter`.

Você pode enviar um desses arquivos manualmente na página de transações do The Book, dentro
da conta bancária "Bradesco" na opção "Import OFX". Instruções detalhadas de como gerar o arquivo
manualmente podem ser encontradas [aqui](https://discourse.lhc.net.br/t/importar-transa%C3%A7%C3%B5es-do-bradesco/995).

> **O arquivo OFX gerado pelo Bradesco altera eventualmente o valor do campo <FITID> da mesma transação (que é como identificamos transações únicas). Por esse motivo, se importarmos o mesmo arquivo para o mesmo período mais de uma vez, há a possibilidade (grande) de termos transações duplicadas.**

Caso as transações nunca tenham sido importadas para aquele período, é seguro importar o arquivo em toda sua totalidade. Caso alguma transação já tenha sido importada anteriormente, você deverá informar o período de datas que você quer que seja considerado no arquivo a ser importado. Neste cenário, valide manualmente as transações inseridas e exclua as possíveis duplicadas.
