# Validação da entrega 0.1.0

Verificações executadas no ambiente Linux desta sessão, com Python 3.12.14 e Node.js 24.19.0.

| Verificação | Resultado |
|---|---|
| Backend, pytest | 18 testes passaram. |
| TypeScript | Verificação sem erros. |
| Frontend, Next.js 16.4.3 | Build de produção concluído. |
| Migration Alembic | Aplicada em SQLite; `alembic check` sem operações pendentes. |
| Migration PostgreSQL | SQL de criação gerado pelo dialecto PostgreSQL, sem ligação a servidor. Não equivale a execução real. |
| Navegador | Um percurso integrado passou, com API e frontend reais e base temporária. |
| Vista desktop | Inspeccionada a 1440 px. |
| Vista móvel | Inspeccionada a 390 px, menu testado e ausência de transbordamento horizontal confirmada. |
| Dependências | Versões Python e npm conservadas nos ficheiros de lock; variantes SWC Windows x64 e Linux musl presentes no lock npm. |

O percurso de navegador executou entrada, indicadores, filtro por laboratório, consulta de avaliação, pré-validação e importação idempotente, início da acção, upload de evidência, solicitação de verificação, encerramento por outra pessoa, mudança para inglês e navegação móvel. Não ocorreram erros JavaScript de página nesse percurso.

Os testes de backend cobrem cálculo, incompletude, instrumentos não comparáveis, importação, revisões, transições, sessão, protecção de pedidos, isolamento, revogação imediata, perfil de parceiro, acesso a evidências, documentos, contrato do adaptador Meta, citações, retirada de fontes, revogação de análise em fila, mapeamento ODK e recuperação de SQLite com anexos e hashes.

O adaptador Meta e a leitura ODK foram exercitados com respostas controladas de teste. Não foram feitas chamadas autenticadas a contas externas.

Não executado nesta sessão: instalação PowerShell/Windows, Docker, PostgreSQL real, Meta API real, ODK real, SMTP real, testes de carga, recuperação institucional ou piloto. O ambiente não disponibiliza o disco D: do utilizador.

As capturas usadas na revisão visual são resultados internos dos testes e não integram o pacote de código.

## Branch de pontuação com NA, 26/10/2026

Após a análise do PDF recebido, a suite do backend passou de 18 para 21 testes, todos aprovados; os testes novos cobrem subtracção do denominador por secção e total, justificação NA, rejeição em instrumento de máximo fixo, importação CSV, idempotência, revisões imutáveis e denominador zero. A compilação de produção do Next.js (incluindo TypeScript) passou. Dois percursos no navegador passaram: o fluxo original da demonstração e a publicação de um instrumento com NA seguida de uma avaliação pelo formulário. Estas verificações foram executadas no ambiente Linux de desenvolvimento; a instalação Windows do utilizador e as integrações externas reais continuam por validar.
