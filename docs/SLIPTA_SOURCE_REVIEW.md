# Revisão dos ficheiros SLIPTA fornecidos

Data da revisão: 31/10/2026. Esta análise não homologa o instrumento.

Foram lidos a checklist original de 50 páginas e o XLSForm piloto, versão `2026090801`, formulário `slipta_v3_2023_mozambique`. A preparação identificou 151 questões principais, com correspondência de texto e página no PDF para todas elas. Cada referência contém a tradução do XLSForm, o trecho original em inglês e os códigos de critérios, incluindo aliases dos campos ODK. O pacote JSON fica privado e não é incluído no GitHub.

| Verificação | Resultado observado |
| --- | ---: |
| Questões principais extraídas | 151 |
| Questões com trecho em inglês e página localizados | 151 |
| Soma dos pesos impressos por questão no PDF | 365 |
| Total declarado no PDF | 373 |
| Soma dos pesos extraídos do XLSForm | 364 |
| Critério 8.22: peso no XLSForm | 2 |
| Critério 8.22: peso no PDF | 3 |

A folha VALIDAÇÃO_TÉCNICA do próprio XLSForm já assinala a divergência entre a contagem de perguntas, os pesos impressos e os totais declarados. A comparação adicional encontrou a diferença de um ponto em 8.22 entre o formulário e o texto original. Estes valores são diagnósticos das fontes, não uma proposta de correcção da norma.

O importador piloto recebe os campos calculados do ODK e valida-os contra os pesos do XLSForm fornecido. Não avalia fórmulas arbitrárias nem altera pontuações existentes. Um campo em falta permanece em falta. Quando uma questão é totalmente N/A, suspende a percentagem final para revisão, em vez de tratar N/A como zero ou conformidade total. Esse tratamento conservador é diferente do ajuste automático de denominador implementado no XLSForm e precisa de validação institucional antes de qualquer classificação oficial.

O projecto não atribui estrelas oficiais, certificação ou acreditação. A instituição deve decidir e documentar o instrumento homologado, o tratamento de N/A e o denominador antes do uso oficial. Não substitua o instrumento de uma avaliação antiga: mantenha a versão e crie uma nova versão para alterações aprovadas.

## Proveniência

- PDF SHA-256: `d7a9616d0b3a2c5abde698df9db793eec2f1534ef95c839a05907e7cfd675856`.
- XLSForm SHA-256: `279e5340ef544ce7af465f4afae48282c578433026a3539f2053204a196dd511`.
- Originais fornecidos pelo autor do projecto. Referências preparadas para revisão interna, sem endosso institucional implícito.
