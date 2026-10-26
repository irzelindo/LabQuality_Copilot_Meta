# Registo de requisitos

Fonte: especificação V1 de 19/10/2026, anterior ao início da implementação. Para o estado actual, consultar IMPLEMENTATION_STATUS.md. O âmbito abaixo é a referência da versão completa; não é uma declaração de funcionalidades concluídas.

# LabQuality Copilot

## Especificação técnica da versão completa V1

Data: 19 de Outubro de 2026.
Estado: definição proposta para desenvolvimento e discussão com parceiros.
Autor da proposta: Irzelindo Salvador.

Esta especificação define a plataforma a construir. Não representa software já implementado, uma verificação de produção ou um mapeamento SLIPTA validado. A candidatura ao hackathon foi submetida. A demonstração técnica e a institucional utilizarão o mesmo produto e identificarão o estado real de cada capacidade.

## 1 Objectivo e âmbito

Permitir o ciclo completo de qualidade laboratorial: configurar a organização e o instrumento, realizar ou importar a avaliação, identificar achados, preparar acções, atribuir responsáveis, anexar evidências, verificar a eficácia e acompanhar a evolução.

A V1 inclui organizações e acessos; avaliações versionadas; importações CSV e Excel e integração ODK Central; não conformidades e acções; evidências; documentos controlados; riscos e ocorrências; registos essenciais de competências e equipamentos; indicadores; IA; notificações; administração e auditoria.

Português e inglês na interface. Os conteúdos originais dos instrumentos conservam o idioma e a versão; uma tradução deve ter revisão identificada. ODK será a via inicial para recolha em conectividade limitada. O portal web terá gravação frequente, retoma e estados de erro claros.

## 2 Arquitectura proposta

| Camada | Escolha inicial | Regra |
|---|---|---|
| Web | Next.js e TypeScript | Interface acessível e adaptável a computador e telemóvel. |
| API | FastAPI e OpenAPI | Validação e autorização de todas as operações. |
| Dados | PostgreSQL e migrations | Transacções, integridade, versões e histórico. |
| Ficheiros | Object storage compatível com S3 | Anexos privados com metadados e versões. |
| Tarefas | Fila e trabalhadores | Importação, geração de relatórios, email e inferência. |
| Modelos | Adaptador para Meta Model API | Modelo, consumo e resultado registados por execução. |
| Operação | Docker e opção Coolify | Ambientes de apresentação, teste e produção separados. |

Começar por uma aplicação modular com trabalhadores separados. Seleccionar as versões das dependências e o modelo concreto depois de consultar a documentação actual no início da implementação. Pesquisa lexical e filtros por metadados são suficientes para a primeira base documental; acrescentar pesquisa vectorial quando a avaliação demonstrar necessidade.

## 3 Modelo de dados

| Entidade | Campos ou relações essenciais |
|---|---|
| Organization e Laboratory | Identidade, rede, localização, estado e vínculo institucional. |
| User e Membership | Identidade, organização, perfil, laboratórios autorizados e validade da atribuição. |
| Checklist e ChecklistVersion | Código, versão, idioma, origem, licença, regras e revisão técnica. |
| Section e Criterion | Versão do instrumento, código, texto autorizado e regra de pontuação. |
| Assessment | Laboratório, instrumento, datas, avaliador, estado e número de revisão. |
| Response e Finding | Critério, resposta, pontos, comentário, criticidade validada e origem. |
| ImportRun | Origem, identificador externo, versão recebida, checksum, estado e erros. |
| Nonconformity e Action | Achado de origem, causa, prioridade, responsável, prazo e estado. |
| ActionVerification | Acção, verificador, evidências, resultado e motivo de reabertura. |
| Evidence e EvidenceVersion | Ficheiro, hash, autor, data, acesso e ligações aos registos. |
| ControlledDocument | Versões, revisor, aprovador, vigência e âmbito de publicação. |
| Risk e Occurrence | Descrição, classificação acordada, tratamento, responsável e revisão. |
| CompetencyRecord e EquipmentRecord | Formação e verificação; manutenção e calibração; prazos e evidências. |
| ReferenceSource e ReferenceChunk | Organização, documento, versão, direitos, trecho e permissões herdadas. |
| AIExecution e Recommendation | Modelo, versão do prompt, contexto, referências, consumo, estado e revisão humana. |
| Notification e AuditEvent | Destinatário ou actor, operação, entidade, data e identificador de correlação. |

Entidades privadas terão organization_id, datas e actor da alteração. A integridade entre laboratório, avaliação, anexos, fontes e organização será validada no servidor e, quando aplicável, por restrições da base de dados. Dados de uma organização não podem ser associados a registos privados de outra.

## 4 Estados e revisões

Avaliação: rascunho, em recolha, em revisão, finalizada, substituída por revisão.

Acção: proposta, aprovada, em execução, em verificação, encerrada ou reaberta. O atraso é calculado pelo prazo e pelo estado; não substitui o estado operacional.

Documento: rascunho, em revisão, aprovado, publicado, substituído ou retirado.

Uma avaliação finalizada será imutável. A correcção cria revisão com motivo e ligação à versão anterior. A publicação de documentos e o encerramento de acções exigem os privilégios definidos. A separação entre executor e verificador será configurável por instituição.

## 5 Importação e cálculo

O conector ODK utilizará identificadores estáveis da submissão e da versão. A correspondência entre uma edição e uma avaliação existente será explícita. Uma repetição da mesma importação deverá ser idempotente.

Fluxo: receber, validar o esquema, identificar a origem e versão, calcular diferenças, apresentar erros ou conflitos e só depois aplicar a transacção. Importações parcialmente inválidas terão relatório claro e política de rejeição ou aplicação parcial definida pelo administrador.

Cada avaliação conservará a versão do instrumento, das regras e dos resultados. Valores ausentes e aplicabilidade terão tratamento conforme a regra aprovada dessa versão. Não aplicar automaticamente uma fórmula genérica ao SLIPTA.

Para a demonstração, pode ser criada uma rubrica inteiramente fictícia, identificada como tal. As pontuações esperadas serão calculadas e revistas antes de testar a IA. A demonstração não atribuirá classificações oficiais a esta rubrica.

Comparações apresentarão cobertura, período e versão. Agregações documentarão se representam soma de pontos ou média de avaliações. Itens críticos individuais permanecerão visíveis mesmo com melhoria da pontuação agregada.

## 6 Permissões e protecção dos dados

Perfis: gestor de laboratório, responsável de qualidade, avaliador, mentor ou verificador, coordenação, parceiro com visão autorizada e administrador.

1. Autorização no servidor por organização, laboratório e operação.
2. Convites e permissões temporárias revogáveis.
3. Acesso da coordenação limitado à rede autorizada.
4. Acesso de parceiros limitado aos agregados e períodos acordados.
5. Registo auditável das alterações relevantes, exportações, partilhas e operações de suporte.
6. Ficheiros privados, tipos e tamanhos permitidos, validação do conteúdo e acesso com validade limitada.
7. Credenciais de modelos e integrações mantidas no servidor, com rotação e controlo de exposição.
8. Fontes de IA sujeitas às mesmas permissões dos documentos originais.
9. Políticas de retenção, exportação e eliminação definidas antes do piloto.
10. Autenticação institucional e segundo factor avaliados conforme os requisitos de implantação.

A demonstração utilizará exclusivamente dados e documentos fictícios ou reutilizáveis com autorização. O piloto exigirá acordo sobre dados e responsabilidades.

## 7 Operações da API

Os caminhos seguintes são uma proposta de contrato a detalhar, não endpoints já disponíveis.

| Área | Operações principais |
|---|---|
| Organizações e laboratórios | Criar, consultar, actualizar, arquivar e conceder acesso. |
| Utilizadores | Convidar, associar perfis, revogar e consultar atribuições. |
| Instrumentos | Criar versões, validar e publicar o catálogo. |
| Avaliações | Criar, guardar respostas, submeter a revisão, finalizar e criar revisão. |
| Importações | Validar CSV ou Excel, sincronizar ODK e consultar erros e alterações. |
| Achados e acções | Registar causas, aprovar, atribuir, actualizar, verificar e reabrir. |
| Evidências | Enviar, versionar, consultar metadados e autorizar acesso. |
| Documentos | Rever, aprovar, publicar, retirar e pesquisar versões autorizadas. |
| Riscos e registos | Criar e acompanhar riscos, ocorrências, competências e equipamentos. |
| Indicadores | Consultar séries, comparações, atrasos, cobertura e relatórios. |
| IA | Solicitar análise, acompanhar execução, rever e aceitar sugestões. |
| Administração | Consultar auditoria, configurar alertas e gerir exportações. |

Operações em lote terão identificadores de correlação e resultados por registo. Listagens terão paginação e filtros. Alterações concorrentes usarão controlo de versão; uma gravação antiga não deverá sobrescrever silenciosamente uma mais recente.

## 8 Assistência por IA

Usar recuperação de fontes autorizadas para fundamentar a resposta. A aplicação cria um pacote de factos com pontuações calculadas, achados, acções existentes e trechos de referência. O modelo propõe uma estrutura que a API valida.

Cada recomendação terá título, justificação, prioridade proposta, passos, critério de conclusão, finding_ids, source_ids e revisão humana. Referências inválidas ou afirmações sem suporte serão rejeitadas ou apresentadas para correcção. Identificadores válidos, por si só, não provam suporte: a correspondência entre afirmação e trecho será avaliada.

O assistente deverá reconhecer informação insuficiente. Conteúdo dos documentos não pode substituir instruções da aplicação, alterar acessos ou executar operações administrativas. Aceitar uma recomendação cria uma proposta de acção; aprovação e atribuição seguem o fluxo do laboratório.

Registar modelo, configuração, versão do prompt, versões das fontes, latência, consumo e avaliação. A primeira integração será preparada para Meta Model API, com selecção do modelo e acesso real confirmados antes dos testes de inferência.

## 9 Cenário partilhado das demonstrações

Três laboratórios fictícios, Sul, Centro e Norte, com três avaliações sucessivas cada. Demonstrar melhoria, deterioração e estabilidade, incluindo uma não conformidade crítica que permaneça visível apesar da melhoria global.

Preparar avaliações, achados, acções abertas e encerradas, documentos fictícios e evidências sem dados pessoais. O cenário terá versões conhecidas e resultados esperados. A reposição do cenário será controlada pelo administrador da apresentação.

Uma conta mostra o laboratório; outra mostra a coordenação autorizada. Mostrar importação, comparação, IA com fontes, revisão humana, atribuição, evidência e verificação. Uma falha de inferência deve produzir um estado de erro real; qualquer gravação usada como apoio será identificada.

## 10 Critérios de aceitação da V1

| Código | Verificação necessária |
|---|---|
| AC01 | Um utilizador não consulta nem altera registos privados de outra organização. |
| AC02 | A revogação de uma atribuição impede novos acessos e pesquisas em documentos privados. |
| AC03 | Reimportar o mesmo conteúdo conserva a mesma avaliação, sem duplicação. |
| AC04 | Uma edição recebida tem correspondência, revisão ou conflito explícito. |
| AC05 | Os cálculos reproduzem os casos aprovados do instrumento e respectiva versão. |
| AC06 | Dados em falta e falta de comparabilidade aparecem nos indicadores. |
| AC07 | Uma avaliação finalizada só é corrigida através de revisão rastreável. |
| AC08 | Uma acção conserva achado, responsável, prazo, evidências e verificação. |
| AC09 | As versões de documentos publicadas e retiradas são respeitadas na pesquisa. |
| AC10 | A IA funciona com uma integração real e referencia fontes acessíveis ao utilizador. |
| AC11 | Informação insuficiente e referências sem suporte são detectadas no conjunto de teste. |
| AC12 | Riscos, competências e equipamentos permitem registo, revisão e alertas previstos. |
| AC13 | Exportações reproduzem dados e filtros autorizados, com data e versão. |
| AC14 | Alertas são enviados uma vez por evento, com tentativa e falha registadas. |
| AC15 | As interfaces essenciais funcionam em português e inglês e em ecrã pequeno. |
| AC16 | Base de dados e anexos são recuperados num exercício documentado. |
| AC17 | Os módulos não têm botões sem operação ou resultados apresentados como reais quando simulados. |
| AC18 | O piloto documenta problemas, correcções, formação e aceitação pelos utilizadores. |

Estes são requisitos a testar. Não existem ainda resultados de aprovação destes casos para esta plataforma.

## 11 Testes e observabilidade

Criar testes significativos para isolamento entre instituições, importação idempotente, cálculo versionado, concorrência e estados do ciclo de acções. A avaliação da IA terá casos com evidência suficiente, evidência em falta, fontes contraditórias, instruções maliciosas em documentos e pedidos de dados não autorizados.

Medir a utilidade das sugestões com revisores de qualidade e registar as alterações efectuadas. Medir tempo até ao primeiro plano, tempo médio de resolução e proporção de acções verificadas, sempre com denominadores e datas definidos. Benefícios permanecem hipóteses até serem medidos no piloto.

Definir um perfil de carga e medir importação, navegação, relatórios e inferência. Configurar registos estruturados, correlação, duração das tarefas, falhas, consumo de modelos e alertas operacionais.

## 12 Entrega e operação

Entregar todos os módulos acordados através de marcos acumulativos na mesma aplicação: fundação e acessos; ciclo de avaliação e melhoria; documentação e registos; inteligência e relatórios; verificação e piloto.

Referência inicial de esforço: 12 a 16 semanas para dois profissionais de desenvolvimento com dedicação integral e apoio parcial de qualidade, produto e testes. Trata-se de hipótese de dimensionamento, a rever após detalhe das integrações; não representa uma equipa ou prazo contratado.

Para o hackathon, rever as regras oficiais sobre trabalho anterior, ferramentas e submissão antes de implementar o código a apresentar. O calendário anunciado começa em 26 de Outubro, com entrega em 4 de Novembro às 21h00 ET, equivalente a 5 de Novembro às 04h00 em Moçambique.

A apresentação institucional utilizará a mesma plataforma e indicará quais os módulos disponíveis, em desenvolvimento e planeados. A designação de versão completa dependerá de todos os critérios de aceitação relevantes estarem cumpridos.

Implantação inicial proposta em Docker, com possibilidade de Coolify. Validar capacidade, isolamento e continuidade no servidor escolhido. Referências iniciais de continuidade a negociar: perda máxima de 24 horas de dados e recuperação em até quatro horas, verificadas por exercício.

## 13 Cooperação institucional

Propor a discussão e o desenho de um piloto em três a cinco laboratórios, mediante acordos. Registar contribuições de conhecimento técnico, implantação, formação, integração e financiamento. Entidades apresentadas como potenciais interlocutores não serão anunciadas como parceiras confirmadas.

Definir propriedade dos dados e do código, direitos sobre conteúdos, licenças das contribuições, exportação e condições de saída. Rever os termos do hackathon no modelo de cooperação. Modelos de financiamento e manutenção serão discutidos com os interessados; ainda não existem preços ou compromissos estabelecidos.

## 14 Fontes e revisão

- SLIPTA V3: https://aslm.org/resource/whos-stepwise-laboratory-quality-improvement-process-towards-accreditation-slipta-checklist/
- ISO 15189:2022: https://www.iso.org/standard/76677.html
- Hackathon: https://dev.meta.ai/events/global-hackathon
- Termos da participação: https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver

Fontes consultadas em 19 de Outubro de 2026. A reprodução de conteúdos normativos exige direitos adequados; esta especificação não reproduz o texto integral desses instrumentos. Regras técnicas de cálculo e classificação dependem de validação específica.
