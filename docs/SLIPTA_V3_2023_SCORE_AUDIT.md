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

## Conferência do XLSForm ODK recebido

Em 26/10/2026 foi conferido, sem incluir o ficheiro no repositório, `SLIPTA_ODK_V3_validacao_tecnica.xlsx` (SHA-256 `279e5340ef544ce7af465f4afae48282c578433026a3539f2053204a196dd511`). O formulário declara `form_id=slipta_v3_2023_mozambique`, versão original `2026090801`; a folha `VALIDAÇÃO_TÉCNICA` apresenta-o como piloto e reconhece a divergência de 145/373 versus 151/365.

Na folha `survey`, há 613 respostas `select_one answers` com valores internos `sim`, `nao`, `parcial`, `na`, 151 cálculos de pontuação de **perguntas principais** (`p2_s{secção}_{secção}_{pergunta}_calculate`) e doze totais de secção. A distribuição das 151 perguntas e a soma dos seus máximos reproduzem exactamente a coluna de pontos individuais da tabela acima. Cada total de secção refere cada cálculo principal uma vez, sem omissões ou duplicações; os doze cálculos de exclusão N/A têm 151 termos e os respectivos pesos somam igualmente 365. As fórmulas de pontuação são expressões XLSForm/ODK na coluna `calculation`, não fórmulas de célula Excel.

O máximo calculável da versão recebida é **365**, gravado explicitamente em `survey!M2899`, e `denominador_aplicavel` retira `pontos_na_total`. O resultado e as estrelas são apresentados como **provisórios**. A soma do formulário confirma os pesos individuais, mas não resolve os 8 pontos nem as 6 perguntas de diferença em relação ao quadro do PDF. Não se deve trocar silenciosamente o denominador por 373 ou publicar a classificação como oficial.

| Constatação no XLSForm recebido | Localização | Tratamento na cópia corrigida |
|---|---|---|
| O comentário obrigatório de 7.9(i) dependia de 7.9(g). | `survey!G1479` | Passa a depender de 7.9(i). |
| Sem itens aplicáveis, a percentagem era zero e o resultado mostrava zero estrelas. | `survey!M2901:M2903`, `C2904` | Percentagem vazia e classificação «Indeterminada (sem itens aplicáveis)». |
| A nota inicial ainda referia `WHO_LOGO.svg`, apesar da indicação de que o media fora retirado. | `survey!C3`, `H3`, `S3`; `VALIDAÇÃO_TÉCNICA!D5` | A nota apresenta título textual; remove a referência ao ficheiro ausente. |

A cópia corrigida foi gerada separadamente, com `settings!C2=2026102601` e registo das três correcções em `VALIDAÇÃO_TÉCNICA!A18:D20`. O original continua intacto. Conferimos todas as células de conteúdo antes/depois: fora as células indicadas, a versão do formulário, o texto de data da folha de validação e as três linhas novas, não houve alterações nos valores das folhas. A exportação e essa comparação não equivalem a uma compilação do formulário nem a testes de submissão no ODK.

Há ainda **34 subitens `select_one answers` sem `required=yes`**, concentrados nas perguntas 2.5, 2.6, 2.8 e 2.9. As fórmulas podem tratar respostas ausentes como zero enquanto uma parte da pergunta obtém pontos. Esta política de completude deve ser decidida com os auditores antes de a alterar: campo opcional pode corresponder a um fluxo intencional de recolha. Confirmar também as regras de arredondamento das estrelas, uma submissão real OData (caminhos dos grupos e identidade estável), e o comportamento nos clientes ODK Collect e Enketo, incluindo todos N/A e gravações incompletas.

O conector da aplicação só consome **pontuações numéricas por critério** através de campos explicitamente mapeados; ainda não importa os subitens `sim`/`nao`/`parcial`/`na`, as justificações, nem identifica automaticamente uma pergunta principal inteiramente N/A. Mapear apenas os 151 campos `*_calculate` agora faria uma pergunta totalmente N/A parecer uma resposta numérica zero e perderia a exclusão do denominador. Por isso, a cópia piloto não foi ligada a um instrumento publicado nem usada para importar avaliações reais.

### Actualização do piloto demonstrativo, 26/10/2026

Foi gerado um catálogo **provisório** `SLIPTA-ODK-PILOT 2026.10` a partir desse XLSForm verificado, com 151 itens principais e soma 365. O conector lê o cálculo de cada item, as respostas individuais usadas para reconhecer um item inteiramente NA e os respectivos comentários. Quando todos os campos de um item estão NA, exige justificação e exclui o máximo do denominador; quando não há dados, deixa o item por avaliar, sem transformar ausência em zero. As nove avaliações fornecidas para a apresentação são cenários **simulados**, não importações reais do ODK. A integração OData dispõe agora de sincronização automática a cada cinco minutos, com identidade estável e revisão imutável; a estrutura concreta das submissões, as regras de subitens opcionais e a classificação oficial ainda exigem validação com um auditor e com uma submissão real de ensaio. O parágrafo anterior regista a limitação observada antes desta implementação.

O título da pergunta **8.18** no XLSForm repete por lapso «Laboratórios de Referência e Consultores Técnicos», embora o enunciado e os subitens tratem da monitorização diária das condições ambientais. No catálogo piloto apresentamos o título descritivo «Monitorização diária das condições ambientais», sem alterar o código, os subitens ou os cálculos do XLSForm original. Solicitar confirmação da equipa de auditoria antes de corrigir o formulário publicado.
