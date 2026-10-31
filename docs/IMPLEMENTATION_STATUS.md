# Estado da implementação - 0.2.0

31/10/2026. Candidato para demonstração, com validação externa pendente. O produto completo V1 continua descrito em PRODUCT_SPECIFICATION_V1.md. Uma funcionalidade implementada ou testada não representa autorização de uso institucional nem uma garantia de prémio.

| Área | Implementado | Limites e validação pendente |
| --- | --- | --- |
| Acessos e histórico | Instituição, laboratórios, perfis, sessões HttpOnly, revisões imutáveis e autorização no servidor. | Sem SSO/MFA e operação distribuída validada. |
| Avaliações | Cálculo determinístico por instrumento, cobertura, achados, revisões e importação repetível. | Fontes SLIPTA inconsistentes. Sem estrelas oficiais. |
| Preparação da análise | Diagnóstico por avaliação, selecção explícita de até cinco achados, cobertura de fontes, bloqueios e encaminhamento desde a avaliação. | Disponibilidade de fontes não comprova adequação semântica. |
| Integração Meta | Responses API, saída estruturada, PT/EN, comentários do auditor, citações e critérios verificados, revisão humana, filas e relatório para impressão. | Chave real não disponibilizada. Testes com transporte controlado não provam inferência real. Sem benefício medido. |
| Referências SLIPTA | 151 documentos preparados a partir dos originais fornecidos, com trecho inglês, texto português, página e hashes. Pré-validação e importação repetível como rascunho. | Revisão, aprovação independente e publicação precisam de ocorrer na instalação do autor. PDF/XLSForm processados pelo comando de preparação, não por upload directo de PDF na interface. |
| ODK | Conector genérico e CLI piloto específico com OData/JSON, pré-validação por defeito, contagem esperada, campos calculados e histórico. | Sem credenciais ODK nem base local nesta execução. Nove avaliações importadas são progresso relatado pelo autor. Identidades precisam de conferência antes de migrar ferramentas. |
| Planos, evidências e verificação | Atribuição, aprovação, execução, ficheiros privados, revisão independente, encerramento e reabertura. | Exige evidência verdadeira e revisão técnica pelo utilizador. |
| Guia de utilização | Percurso PT/EN na aplicação, guia PT, actualização Windows, validação e roteiro EN de quatro minutos. | Executar o roteiro de actualização e o ensaio com a instalação real. |
| Indicadores | Filtros, evolução, secções, críticos, atrasos e exportação CSV. | Sem média única de instrumentos incompatíveis e sem comparação institucional homologada. |
| Operação | Backup SQLite, auditoria, trabalhador e estrutura Docker/PostgreSQL herdada. | Docker/PostgreSQL, SMTP real, Windows e recuperação institucional não executados nesta entrega. |
| Apresentação | Seis slides em inglês com notas de fala e indicação de validação real pendente. | Actualizar alegações somente após executar o piloto e recolher medições. |

## Critérios de demonstração

A demonstração completa exige uma análise real da Meta, fontes publicadas autorizadas, revisão do conteúdo, criação de acção e evidência com verificação independente. O controlo automático de citações não substitui a revisão profissional. O produto não emite acreditação nem garante resultados de concurso.

O código de base começou antes do hackathon. Preservar o histórico e identificar o trabalho elegível na submissão. Não foram formalizadas parcerias nem efectuado deploy nesta execução.
