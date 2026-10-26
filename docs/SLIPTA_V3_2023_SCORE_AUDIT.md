# Conferência de pontuação da checklist SLIPTA V3:2023

Conferência inicial em 26/10/2026 da cópia fornecida para o projecto: `SLIPTA-Checklist-V3-22-Dec-2023.pdf`, 50 páginas, SHA-256 `d7a9616d0b3a2c5abde698df9db793eec2f1534ef95c839a05907e7cfd675856`. O PDF original não é incluído no repositório. Esta análise transcreve apenas números, códigos e resultados de reconciliação, sem republicar as perguntas.

Na página 5, o quadro de pontuação anuncia 12 secções, 145 perguntas e 373 pontos. Contando os itens principais numerados e somando os pontos máximos **impressos junto de cada item** nas páginas 6–47, obtemos:

| Secção | Perguntas numeradas | Soma dos máximos por pergunta | Total no quadro | Diferença |
|---|---:|---:|---:|---:|
| 01 Documentos e registos | 10 | 21 | 22 | +1 |
| 02 Organização e liderança | 11 | 26 | 26 | 0 |
| 03 Gestão de pessoal | 14 | 34 | 34 | 0 |
| 04 Foco no cliente | 10 | 24 | 24 | 0 |
| 05 Gestão de equipamentos | 16 | 37 | 44 | +7 |
| 06 Avaliação | 9 | 24 | 24 | 0 |
| 07 Fornecedores e inventário | 12 | 27 | 27 | 0 |
| 08 Gestão dos processos | 27 | 71 | 71 | 0 |
| 09 Gestão da informação | 10 | 24 | 24 | 0 |
| 10 Eventos não conformes | 5 | 13 | 13 | 0 |
| 11 Melhoria contínua | 3 | 7 | 7 | 0 |
| 12 Instalações e segurança | 24 | 57 | 57 | 0 |
| **Total** | **151** | **365** | **373** | **+8** |

A secção 1 tem itens 1.1–1.10: a página 6 imprime um item de 3 pontos e dois de 2; a página 7 imprime sete de 2 e o rodapé `/22`, quando os itens somam 21. A secção 5 tem itens 5.1–5.16 nas páginas 17–20; a soma dos máximos individuais é 37 e o rodapé da página 20 imprime `/44`. Estas são diferenças do documento recebido, observadas também na imagem das respectivas páginas; não identificámos uma indicação que diga qual pergunta deve ganhar outro valor nem seis perguntas que possam ser retiradas para chegar às 145 indicadas no resumo.

Para revisão com os auditores: na secção 1, `1.2` vale 3 pontos e os outros nove itens valem 2. Na secção 5, `5.1`, `5.6`, `5.7`, `5.10` e `5.11` valem 3; os outros onze itens valem 2. Para atingir o total impresso sem acrescentar perguntas, seria necessário alterar um item de 2 para 3 na secção 1 e sete na secção 5. O PDF não identifica quais seriam; estas alterações **não** foram aplicadas.

O quadro de estrelas da página 5 combina intervalos de pontos baseados em 373 com intervalos percentuais. Por exemplo, 241/373 = 64,61%, embora 241 pontos figurem na banda de 2 estrelas, cujo limiar percentual impresso é 65%. Analogamente, 353/373 = 94,64% e figura na banda de 5 estrelas, cujo limiar é 95%. É possível que o quadro pressuponha arredondamento para percentagens inteiras, mas o método não é explicitado. Com respostas **NA**, a própria instrução da página 5 manda subtrair do denominador os máximos dos itens principais assinalados NA e determinar as estrelas pela percentagem, aumentando a importância dessa definição.

As instruções também atribuem os pontos máximos a **Y**, 1 ponto a **P** e 0 a **N**; respostas P, N ou NA requerem comentário e NA requer justificação documentada. Para uma pergunta composta ser Y, as subperguntas têm de ser todas Y e/ou NA. O código actual não recolhe separadamente as subperguntas nem converte automaticamente respostas textuais ODK em pontos; essas regras exigem mapeamento verificado antes de activar a classificação oficial.

## Decisão de implementação nesta branch

- A rubrica fictícia `DEMO-QMS` mantém `sum_fixed_v1` e os seus resultados anteriores.
- Foi acrescentada `sum_applicable_v1` como regra **genérica**, disponível ao publicar outra versão de instrumento. NA só pode ser usado com pontuação vazia e comentário de justificação. Os pontos máximos dos itens NA saem do denominador do total e da respectiva secção; os máximos originais e as exclusões são apresentados separadamente. Uma resposta por avaliar continua sem percentagem, e um instrumento inteiramente NA não pode ser finalizado sem itens aplicáveis.
- A importação CSV/XLSX aceita `NA` ou `N/A` na coluna `value` com justificação na coluna `comment`; JSON aceita `not_applicable: true`. Reimportações idênticas preservam a identidade e correcções criam revisão.
- **Não** foi publicado um instrumento oficial SLIPTA, nem atribuídas estrelas a partir deste PDF inconsistente. Nenhum ponto foi acrescentado a perguntas por suposição.

Para completar o mapeamento oficial: obter uma versão/corrigenda validada dos pontos por pergunta e dos totais das secções 1 e 5, confirmar a contagem de perguntas efectivamente utilizada em Moçambique, definir o arredondamento das estrelas e validar com auditores o tratamento de subperguntas e a correspondência com o formulário ODK. Depois, publicar um instrumento versionado e testes de casos conhecidos, sem alterar avaliações anteriores.
