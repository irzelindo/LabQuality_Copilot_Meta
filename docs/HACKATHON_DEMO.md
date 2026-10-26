# Roteiro de demonstração — LabQuality Copilot

Versão de trabalho para uma demonstração de cerca de três minutos. Ajuste a duração e o formato aos requisitos de submissão publicados pelos organizadores; a página do evento indica **4 de Novembro de 2026, 21h ET**, como limite sujeito a alterações. Não atribua à aplicação resultados clínicos ou benefícios medidos que ainda não foram demonstrados.

| Tempo aproximado | Ecrã e acção | Mensagem principal |
|---|---|---|
| 0:00–0:25 | Título e visão geral | Laboratórios precisam de transformar avaliações e achados em melhorias verificáveis. O LabQuality Copilot liga esses passos num único fluxo. |
| 0:25–0:55 | Dashboard; filtre Laboratório Sul | A demonstração tem três laboratórios fictícios e **nove avaliações legítimas, em três momentos diferentes por laboratório**. O Sul evolui para 80%, mas conserva um achado crítico: a média não oculta o risco. |
| 0:55–1:20 | Avaliações; abra o achado e as revisões | Cada avaliação tem data, origem, instrumento versionado e histórico. A reimportação de um registo igual é idempotente; uma correcção preserva a revisão anterior. |
| 1:20–1:55 | Planos de melhoria; evidência e verificação | Mostre responsável, prazo, transição de estado, anexo e verificação independente antes do encerramento. Esta é a entrega operacional do produto. |
| 1:55–2:25 | Documentos e assistente IA, **se a execução real tiver passado** | O modelo Meta recebe apenas fontes publicadas acessíveis ao utilizador; a proposta cita fontes e exige aceitação humana. Mostre o registo real de execução, nunca um resultado simulado como IA. |
| 2:25–2:50 | Configuração e próximos passos | Os testes da Meta, ODK e SMTP indicam o estado das ligações. O instrumento DEMO-QMS é fictício; a classificação SLIPTA oficial e o mapeamento do XLSForm continuam por validar. |

## Narração curta em inglês

> Laboratory quality assessments often end as scores and disconnected follow-up tasks. LabQuality Copilot turns each finding into an accountable improvement cycle: a dated assessment, a specific finding, an assigned action, supporting evidence, and independent verification. In this fictional three-laboratory scenario, nine assessments represent three distinct moments per laboratory. The South laboratory reaches 80 percent, yet a critical finding remains visible. Reimporting the same assessment does not create another record; corrections preserve a revision history. We also connect published, authorized documents to Meta Model API for a cited draft recommendation, subject to human review **[include this sentence only after a successful real inference]**. The demonstration rubric is fictional; official SLIPTA scoring and ODK form mapping still need domain validation. Our goal is to make quality improvement auditable from assessment to closure.

## Antes de gravar ou submeter

- Abra a branch [`feature/slipta-v3-scoring`](https://github.com/irzelindo/LabQuality_Copilot_Meta/tree/feature/slipta-v3-scoring), instale-a no clone Windows existente e preserve `.env`, SQLite e anexos locais; faça uma cópia de segurança antes de ensaios com dados reais.
- Execute `start-windows.ps1` com API, trabalhador e interface; confirme as nove avaliações e prepare o percurso sem mostrar palavras-passe, chaves ou informação identificável.
- Na página Configuração, verifique a Meta com **Testar**, confirme créditos em Billing e faça uma inferência real com o instrumento fictício antes de incluir a cena de IA. Se a inferência falhar, retire essa frase e apresente a integração como pendente de validação.
- Use ODK/SMTP na gravação apenas depois de os respectivos testes reais passarem. Não importe o XLSForm SLIPTA como pontuações oficiais até validar perguntas, máximos, Y/P/N/NA e identidade das submissões.
- Consulte o formulário e as regras finais do evento para saber que artefactos e formato são exigidos. A página pública consultada informa a data de entrega, mas não especifica duração de vídeo nem obriga a uma aplicação publicada.
- Identifique com transparência o trabalho iniciado antes de 26/10/2026 e confirme as regras de elegibilidade antes de declarar a entrega competitiva concluída.
