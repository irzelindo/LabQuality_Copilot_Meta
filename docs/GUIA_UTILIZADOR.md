# Guia de utilização — LabQuality Copilot 0.1.0

Este guia acompanha a versão de desenvolvimento da aplicação. O percurso é **auditoria → achado → fonte revista → análise Meta → acção → evidência → verificação**. As decisões e a validação técnica pertencem à equipa; as sugestões da Meta não são conclusões automáticas da auditoria.

## Começar com as nove submissões ODK já importadas

1. Inicie a API, o trabalhador e a interface com `start-windows.ps1`. Abra `http://localhost:3000` e entre com a conta atribuída. A API serve os dados; o trabalhador processa as análises Meta, sincronizações agendadas e notificações.
2. Abra **Avaliações** e escolha **Submissões reais ODK** no filtro **Origem dos dados**. Escolha **Todos os laboratórios** para ver a rede ou seleccione Maputo, Beira ou Nampula. Limpe os filtros de data se uma auditoria não aparecer. “Real · ODK” identifica a origem da submissão; os nomes `TESTE - ...` indicam casos de ensaio, não dados clínicos ou pontuação oficial.
3. Abra uma avaliação e percorra os critérios e respectivos comentários. Um valor abaixo do máximo cria um **achado**; uma resposta vazia aparece como `—`, não como zero. Use **Origem e revisões** para confirmar a identidade e as alterações históricas.
4. Para a avaliação da **Beira** mostrada nas imagens: **317/365** são pontos *provisórios*; **99,34% de cobertura** significa 150 dos 151 critérios respondidos. A percentagem final fica `—` enquanto faltar uma resposta. A interface actualizada mostra o código do critério em falta e desactiva **Finalizar avaliação** até a avaliação estar completa. Não atribua zero ou `NA` só para fazer desaparecer o aviso.
5. Confirme a resposta e a evidência no ODK Central. Se a submissão estiver incorrecta, edite-a no ODK e sincronize novamente. Uma edição importada cria outra revisão da mesma avaliação. **Criar correcção** também permite registar uma revisão local com motivo, mas, numa avaliação com origem ODK, uma sincronização posterior pode substituir a correcção local. Use `NA` apenas quando o critério realmente não for aplicável e registe a justificação.
6. **Finalizar avaliação** é uma decisão humana de um administrador, gestor ou verificador, após rever todas as respostas aplicáveis. A Meta pode analisar achados de uma avaliação ainda em revisão, desde que existam fontes adequadas; a finalização e a análise são passos diferentes.

## Preparar as fontes e executar a Meta

O aviso **“A análise Meta ainda não tem fontes suficientes”** é um controlo de qualidade. A chave da Meta pode estar configurada, mas a aplicação só envia achados com **documentos publicados, acessíveis ao laboratório e pertinentes**. Os três documentos `DEMO-*` da instalação são exemplos fictícios associados a `C05`, `C06` etc. Os achados SLIPTA usam códigos como `1.5`, `2.9` ou `11.1`; aqueles exemplos não são fontes válidas para eles.

1. Na avaliação, leia a lista **Critérios sem fonte** e escolha **Ver documentos**. A lista apresenta até dez códigos por vez; não assuma que são os únicos achados da auditoria.
2. Em **Documentos → Novo documento**, escolha **Toda a instituição** se a fonte aprovada for válida para todos os laboratórios, ou escolha o laboratório correcto para um procedimento local. Identifique a versão, escreva um título e transcreva apenas **texto original ou autorizado**, pertinente para os critérios. O campo **Códigos de critérios** recebe os códigos exactos separados por vírgula, por exemplo `1.5, 2.9`. Uma fonte geral sem códigos pode ser recuperada em vários contextos; reserve-a para material que realmente se aplique a todos esses contextos.
3. Guarde o rascunho, abra-o e seleccione **Submeter à revisão**. Outra pessoa com perfil de aprovação deve confirmar conteúdo, âmbito e códigos, escolher **Aprovar documento** e depois **Publicar versão**. O autor não pode aprovar a própria revisão. Se criar um documento para um dos laboratórios `TESTE`, confirme em **Equipa e acessos** que o aprovador tem esse laboratório atribuído; se ainda não houver outra pessoa autorizada, o administrador tem de configurar uma conta adequada. Só a versão publicada entra no contexto da Meta. Actualmente o motor procura o **texto registado**; anexar simplesmente um PDF ou carregar o XLSForm em Instrumentos não publica uma fonte para IA.
4. Volte a **Avaliações**, abra a mesma revisão e confirme que o aviso reconhece ao menos um achado com fonte. Escolha **Analisar com Meta**. A análise entra numa fila: mantenha o trabalhador em execução. Em **Copiloto de qualidade**, veja o estado e depois a proposta, os trechos citados e os achados associados.
5. Confira que cada citação se aplica ao critério e que a proposta é segura e exequível. Um achado sem fonte pode continuar sem recomendação mesmo que outros sejam analisados. Aceite apenas as propostas adequadas; uma proposta aceite pode originar uma acção. Erros de fornecedor, créditos, limite de utilização ou resposta inválida aparecem na execução. A aplicação não inventa uma resposta da Meta em caso de falha.

**Para o primeiro ensaio:** escolha um achado real de uma das nove avaliações com comentário e pontuação abaixo do máximo. Publique um pequeno texto institucional autorizado para *esse* código depois de revisão por outra pessoa. Verifique a prontidão, execute a análise e confirme as citações. Não é necessário criar de imediato um documento para todos os 151 critérios.

## Criar e acompanhar um plano de melhoria

**Planos de melhoria → 0 acções** é normal logo depois de importar o ODK: a importação cria avaliações e achados, mas **não** cria acções. O filtro **Laboratório** também limita a lista. Para começar, abra um achado em **Avaliações → Criar acção**, ou use **Planos de melhoria → Nova acção** e escolha o achado de origem. Indique a causa ou a investigação necessária, passos concretos, critério de conclusão, prioridade, responsável e prazo.

O percurso de uma acção é **Proposta → Aprovada → Em execução → Em verificação → Encerrada**. Um responsável regista trabalho e anexa evidências PDF, imagem ou TXT; um administrador, gestor ou verificador que **não seja o responsável** revê as evidências e regista se a acção foi eficaz. Se não foi, pode reabri-la com motivo. O quadro e a lista mostram os mesmos registos por laboratório. Uma recomendação Meta não executa nem encerra uma acção por si.

## O que faz cada ecrã

| Ecrã | Quando utilizar |
|---|---|
| **Visão geral** | Acompanhar indicadores; filtrar laboratório, datas e origem para não misturar as nove simulações locais com as nove submissões ODK. Não interpretar pontuação do piloto como classificação oficial SLIPTA. |
| **Avaliações** | Abrir a auditoria, rever critérios e achados, ver revisões, criar correcção fundamentada, finalizar quando completa e pedir análise Meta. |
| **Planos de melhoria** | Criar acções ligadas a achados, atribuir responsáveis, acompanhar prazos, anexar evidências e verificar eficácia. |
| **Copiloto de qualidade** | Consultar a fila e os resultados Meta, conferir citações e decidir se aceita uma proposta. |
| **Documentos** | Manter texto controlado com âmbito e códigos de critérios; passar por rascunho, revisão, aprovação e publicação. |
| **Registos operacionais** | Acompanhar riscos, ocorrências, competências e equipamentos; não substituem o formulário de auditoria. |
| **Importar dados** | Ler respostas CSV/XLSX ou submissões ODK. O exemplo CSV tem **uma linha por critério**; o XLSForm que define o questionário não é um ficheiro de respostas. |
| **Instrumentos** | Consultar a versão e os critérios, pré-validar e carregar o XLSForm SLIPTA conferido. A pontuação de 365 é provisória, sem estrelas oficiais. |
| **Laboratórios** | Confirmar os códigos estáveis do ODK e os laboratórios a que a equipa pode aceder. |
| **Equipa e acessos** | Um administrador define perfis, laboratórios autorizados e revoga acessos. |
| **Auditoria** | Consultar o histórico de operações, conforme as permissões. |
| **Configuração** | Testar a ligação Meta, ODK e SMTP, ver o estado e alterar a própria palavra-passe. “Configurado” indica parâmetros presentes, não garante uma análise concluída. |
| **Guia de utilização** | Ver o percurso resumido e os avisos mais frequentes dentro da aplicação. |

## Ler ou sincronizar novas submissões ODK

Em **Importar dados → ODK Central**, indique o projecto (no seu servidor piloto, `1`) e escolha `SLIPTA-ODK-PILOT v2026.10`. O formulário XML `slipta_v3_2023_mozambique` e os caminhos conhecidos são preenchidos pelo conector. Use **Pré-validar submissões ODK**: confirme o número de submissões, códigos dos laboratórios, datas e pontuações em falta. Se um laboratório não existir, cadastre o código indicado em **Laboratórios**. Depois seleccione **Sincronizar agora** e acompanhe **Tarefas de integração**. Quando o percurso estiver validado, o administrador pode activar a sincronização automática (aproximadamente a cada cinco minutos). A mesma submissão sem alterações não cria duplicados; alterações produzem revisões.

Se as nove avaliações já aparecem em **Avaliações**, não precisa importar novamente para iniciar a revisão e preparar a primeira análise Meta. Guarde as credenciais apenas no `.env` local e reinicie os serviços quando mudar a configuração; nunca introduza palavras-passe no formulário de documentos.

## Papéis e limites

O administrador gere a instituição. Gestores, responsáveis da qualidade e avaliadores operam conforme o laboratório; administradores, gestores e verificadores podem aprovar determinadas etapas, com separação de pessoas para aprovação de documento e verificação de eficácia. A coordenação consulta a rede; o parceiro vê indicadores agregados. Se um botão não aparecer, confira o perfil e a atribuição ao laboratório com o administrador.

O piloto SLIPTA usa 151 itens e um total calculável de 365 pontos do XLSForm recebido. Existem divergências entre o XLSForm e totais publicados na checklist de referência; por isso, não atribui estrelas nem uma classificação oficial. Os laboratórios `TESTE` e os documentos `DEMO` servem para ensaio. Antes de utilização institucional, valide o instrumento, as fontes, as permissões, as integrações e a política de dados com a equipa responsável.
