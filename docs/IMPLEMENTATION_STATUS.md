# Estado da implementação — 0.1.0

Data: 23/10/2026. Plataforma em desenvolvimento. Este registo distingue código funcional, integrações ainda sem validação externa e trabalho pendente da V1.

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
