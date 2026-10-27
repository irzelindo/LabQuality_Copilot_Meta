# Estado da implementação — 0.1.0

Data: 23/10/2026. Plataforma em desenvolvimento. Este registo distingue código funcional, integrações ainda sem validação externa e trabalho pendente da V1.

Actualização do percurso ODK/Meta em 27/10/2026: a instalação do utilizador confirmou autenticação no ODK e no SMTP e aceitação da chave Meta/modelo. A pré-validação ODK foi acrescentada para consultar o formulário piloto, apresentar laboratórios e contagens de submissões e simular a importação sem persistir dados. O XLSForm da revisão já conferida pode ser pré-validado e criar o instrumento piloto em **Instrumentos**, com importação idempotente. **Visão geral** e **Avaliações** permitem separar submissões ODK e simulações. Uma exportação CSV histórica confirmou os 151 caminhos calculados para uma submissão; **a leitura das submissões actuais pela API OData, a primeira importação e uma análise Meta de avaliação real ainda não foram verificadas nesta instalação**. A imagem do ODK mostra nove submissões em 27/10/2026; não foram importadas aqui. Consulte o [percurso de validação](INTEGRATIONS_SETUP.md#odk-central--ligação-antes-do-mapeamento).

| Módulo V1 | Implementado nesta entrega | Limites e validação seguinte |
|---|---|---|
| Organizações e acessos | Instituição, laboratórios, contas, perfis, sessão HttpOnly revogável e autorização no servidor. | Convites por email, SSO/MFA e controlo distribuído de tentativas por implementar. Administração de uma instituição por sessão. |
| Avaliações e instrumentos | Instrumento versionado, questionário, achados, cálculo determinístico, finalização e correcções com revisão. | Apenas soma com denominador fixo; sem classificação oficial SLIPTA. Instrumentos reais exigem revisão técnica. |
| Importação e integração | CSV, XLSX, JSON, pré-validação, lote transaccional, idempotência e revisões; conector ODK OData. | ODK apenas testado com resposta controlada; mapeamento real de identidade e pontuações por validar. Limite de 500 avaliações/lote. |
| Não conformidades e acções | Achado ligado à acção, causa, prioridade, responsável, prazo, estados, verificação independente e reabertura. | Não existe ainda catálogo complexo de causas, subtarefas ou configuração institucional da separação de funções. |
| Evidências | Ficheiro privado, hash, autor, ligação à acção, histórico de anexos e download autorizado. | Volume local; adaptador S3, análise antimalware e política de retenção por implementar. Novos anexos não substituem os anteriores. |
| Documentos controlados | Rascunho, revisão, aprovação por outra pessoa, publicação e retirada de versões; texto pesquisado para IA. | Edição cria nova revisão. Não extrai conteúdo de PDFs, imagens ou documentos Office. |
| Riscos e ocorrências | Registos, responsáveis, prazos, atributos locais, acompanhamento e revisão de estado. | Matrizes institucionais, ligações entre ocorrências e CAPA e edição detalhada de registos por ampliar. |
| Competências e equipamento | Registos essenciais, responsáveis, prazos e revisão com atributos específicos. | Não substitui um sistema completo de gestão de activos ou formação; anexos próprios destes registos por implementar. |
| Indicadores e relatórios | Laboratório/data, evolução, secções, críticos, acções em atraso, média de resolução, lista de casos prolongados e CSV autorizado. | Sem gráficos oficiais SLIPTA; comparações entre instrumentos distintos ficam sinalizadas e não geram média única. Exportação PDF/Word por implementar. |
| Assistência por IA | Adaptador Meta Responses, fila persistida, esquema, fontes publicadas autorizadas, verificação de citações e conversão humana em proposta. | Sem execução real nesta sessão: falta a chave da conta. Verificação semântica exige revisão; conversa livre e avaliação com especialistas por ampliar. |
| Comunicação | Notificações na aplicação, leitura, deduplicação, avisos diários de atraso e envio SMTP opcional pelo trabalhador. | SMTP real por testar. Entrega SMTP incerta não é repetida automaticamente. Preferências de notificações por implementar. |
| Administração e auditoria | Acessos, auditoria, estados de integração, tarefas, alteração de palavra-passe e backup/recuperação SQLite com hashes. | PostgreSQL/Docker, consistência do backup institucional, retenção, carga e observabilidade operacional por ensaiar. |

## Percurso demonstrável

Os três laboratórios fictícios têm nove avaliações com resultados esperados conhecidos. O percurso inclui consulta, filtros, importação repetida sem duplicação, atribuição de acção, evidência, verificação por outra pessoa e encerramento. A inferência real requer configuração da Meta API; a demonstração não apresenta respostas simuladas como resultados do modelo.

## Critérios de qualidade

Os testes automatizados cobrem isolamento, revogação, cálculo, versões, importação, transições, acesso a evidências, fontes da IA, adaptação ODK e backup local. O adaptador Meta é testado com transporte controlado; esses testes não comprovam acesso real à conta nem qualidade semântica das recomendações.

As interfaces principais têm português/inglês e disposição responsiva. O conteúdo dos instrumentos e as mensagens de erro da API conservam português. Uma avaliação de acessibilidade completa e testes Windows/telemóveis físicos continuam pendentes.

## Antes do piloto institucional

Validar referenciais e direitos de utilização; executar as integrações reais; testar PostgreSQL e armazenamento no servidor; definir retenção e continuidade; medir carga e recuperação; rever segurança e acessibilidade; formar utilizadores e documentar a aceitação do piloto.

Os ficheiros não foram escritos directamente no disco D: do utilizador, que não está acessível no ambiente desta sessão. O instalador do pacote prepara esse destino quando executado no Windows.

## Actualização em branch de trabalho, 26/10/2026

A página Configuração inclui agora testes de ligação exclusivos para o administrador: consulta da lista de modelos Meta, autenticação ODK e autenticação SMTP sem envio. Os indicadores reflectem a presença dos campos necessários, não a validação externa. [Guia de configuração](INTEGRATIONS_SETUP.md). As nove avaliações da demonstração são momentos distintos e foram preservadas.

O motor passou a suportar, como opção por versão de instrumento, um denominador ajustado para itens NA com justificação. Mantém os resultados da demonstração anterior e não altera esquemas da base de dados: a coluna `scoring_rule` já existia e as respostas são JSON. Os máximos original/aplicável e a contagem NA passam a estar disponíveis nos resultados, no dashboard e na exportação. Consulte [a conferência da checklist V3:2023](SLIPTA_V3_2023_SCORE_AUDIT.md) antes de qualquer mapeamento ou classificação oficial; o PDF recebido contém totais inconciliáveis nas secções 1 e 5.

O XLSForm ODK recebido confirma os 151 itens e os 365 pontos calculáveis. Uma cópia piloto foi corrigida em três pontos documentados na conferência, preservando o ficheiro original. Falta compilar e ensaiar o formulário no ODK, decidir a completude de 34 subitens opcionais e validar uma submissão OData antes de implementar a conversão das respostas `sim`/`nao`/`parcial`/`na` com exclusões e comentários no conector. A classificação oficial mantém-se por homologar.

## Piloto SLIPTA e sincronização ODK — 26/10/2026

Foi acrescentado um instrumento piloto com 151 itens principais e 365 pontos calculáveis extraídos do XLSForm, sem classificação oficial. Nove auditorias **simuladas e identificadas como tal** foram criadas para três laboratórios em três datas, com observações de equipamentos, controlo de qualidade, documentação, competências, amostras e segurança. O comando `--refresh-demo` faz backup SQLite e substitui apenas a organização de demonstração, recusando avaliações não demonstrativas. O importador ODK aplica o mapeamento de cálculos, NA justificado e comentários deste XLSForm; uma subscrição por instituição permite consulta automática pelo trabalhador a cada cinco minutos. Os testes de transporte são controlados: a primeira exportação OData real e o fluxo com NA/subperguntas no formulário publicado ainda exigem confirmação.
