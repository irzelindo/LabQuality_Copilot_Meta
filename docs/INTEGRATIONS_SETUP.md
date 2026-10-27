# Configurar e verificar as integrações da demonstração

Faça estas alterações no ficheiro `.env` da **raiz do projecto instalado no seu Windows**. As credenciais não devem ser enviadas em mensagens nem guardadas no Git. Pare as três janelas da aplicação com Ctrl+C, edite o ficheiro local, guarde-o e execute `.\start-windows.ps1` de novo no PowerShell. Entre como administrador e abra **Configuração → Ligações e serviços**. O selo «Configurado» indica apenas que os campos estão preenchidos; o botão **Testar** verifica a ligação sem criar avaliações, executar inferência ou enviar email.

## Meta Model API — prioridade para a apresentação

1. Na conta Meta autorizada para o hackathon, confirme o crédito na página **Billing**, o meio de pagamento exigido pela Meta e, se pretendido, um limite de despesa. O email de participação indica que os créditos são atribuídos em lotes após o formulário de candidatura; a aceitação no hackathon não equivale a crédito activo.
2. Crie uma chave no [painel Meta Model API](https://dev.meta.ai/products/meta-model-api) e preencha no `.env`:

```dotenv
LQ_MODEL_API_KEY=<chave_da_conta>
LQ_MODEL_ID=muse-spark-1.3
LQ_MODEL_BASE_URL=https://api.meta.ai/v1
```

3. Reinicie **API e trabalhador**, clique em **Testar** e confirme «Chave aceite e modelo disponível». Se o modelo não constar da lista, escolha no painel o identificador realmente permitido à sua conta e altere `LQ_MODEL_ID`.
4. Para confirmar uma execução completa, abra uma avaliação fictícia da demonstração e use **Analisar com Meta**. O trabalhador deve estar activo; consulte o resultado, as citações e o estado da tarefa. Uma ligação bem-sucedida, por si só, não confirma créditos, inferência nem qualidade da resposta. Mantenha a revisão humana antes de converter a proposta em acção.

Se uma análise mostrar **Falhou** com «Unterminated string», confirme que instalou a versão actual desta branch e reinicie o trabalhador. Esse erro surgiu depois de uma resposta HTTP 200 com texto JSON incompleto. O adaptador passou a limitar a resposta a três propostas concisas, reservar mais tokens para a saída e reconhecer explicitamente respostas incompletas. As análises já marcadas como falhadas continuam no histórico; faça uma **nova análise** depois da actualização. Se voltar a falhar, consulte a mensagem em **Consultar** e os registos do trabalhador, sem divulgar a chave.

Se aparecer «A fonte não se aplica aos critérios indicados», a Meta citou um documento cujo âmbito não inclui o critério daquele achado. A aplicação rejeita essa proposta. A versão actual envia ao modelo a lista de fontes permitidas por achado, mas continua a exigir uma citação textual exacta e a recusar associações incompatíveis. Volte a ensaiar com uma nova análise após actualizar o código; se persistir, reveja os códigos dos critérios atribuídos aos documentos publicados e o detalhe do achado, sem alterar retroactivamente documentos controlados.

## ODK Central — ligação antes do mapeamento

Se já existe um servidor ODK Central seu ou autorizado, use a URL base HTTPS, sem `/v1` no fim, e uma conta com acesso ao projecto e autenticação compatível com Basic Auth:

```dotenv
LQ_ODK_URL=https://central.exemplo.org
LQ_ODK_EMAIL=<utilizador_odk>
LQ_ODK_PASSWORD=<palavra_passe_odk>
```

Reinicie a API e clique em **Testar**. O teste consulta somente `/v1/users/current` e confirma a autenticação, mas não verifica um projecto, formulário ou submissão. Contas que exigem SSO podem não autenticar por este método.

Se o teste devolver **HTTP 401**, confira que `LQ_ODK_EMAIL` e `LQ_ODK_PASSWORD` pertencem a um **utilizador Web** do Central, não a um App User do ODK Collect; confirme a palavra-passe no próprio Central. Se o servidor usa SSO/OIDC, o Basic Auth necessário a esta integração não funciona e será preciso outro método de autenticação. **HTTP 403** indica falta de permissão para o pedido de teste; a permissão no projecto e formulário terá de ser conferida depois, na sincronização. Redireccionamento ou **HTTP 404** sugere conferir a URL base HTTPS, sem `/v1`, caminho de formulário ou `/login`. Não publique credenciais nem copie o cabeçalho `Authorization` ao relatar o erro.

O XLSForm `SLIPTA_ODK_V3_validacao_tecnica.xlsx` define o questionário, não as respostas das auditorias. O carregamento em **Importar dados → Importar avaliações** devolve agora uma indicação para abrir **Instrumentos → Carregar XLSForm SLIPTA**. Pré-valide o ficheiro nessa página e, se o instrumento ainda não existir, clique em **Criar instrumento**. A versão conferida pelo projecto é `2026090801` e tem `form_id=slipta_v3_2023_mozambique`, 151 itens e 365 pontos calculáveis. Se o mesmo instrumento já existir, o processo preserva-o sem duplicar. Uma revisão diferente do XLSForm exige conferência do mapeamento e da pontuação antes da publicação; o carregamento não altera o formulário alojado no ODK.

No ecrã **Importar dados → ODK Central**, indique o ID do projecto ODK (a imagem recebida mostra `1`) e seleccione `SLIPTA-ODK-PILOT 2026.10`. O formulário XML esperado é `slipta_v3_2023_mozambique`. Clique em **Pré-validar submissões ODK**: a aplicação consulta o formulário sem importar, mostra os códigos e nomes de laboratórios, datas, respostas por avaliar e o número de avaliações novas, revistas ou inalteradas. O teste de ligação em **Configuração** não substitui esta validação. A imagem do servidor mostra nove submissões em 27/10/2026 às 17:49 (hora de Moçambique); a contagem efectiva da API deve ser verificada na pré-validação. Uma exportação CSV histórica recebida contém apenas uma submissão e não representa necessariamente as nove actuais.

Para importar as nove submissões directamente na **instalação Windows que contém o seu `.env` e a sua base SQLite**, actualize primeiro a branch `feature/slipta-v3-scoring`, pare a API, o frontend e o trabalhador e abra PowerShell em `LabQuality_Copilot_0.1.0\backend`. Confirme que as migrações foram aplicadas (`..\.venv\Scripts\python.exe -m alembic upgrade head`); se precisar de migrar uma base existente, faça uma cópia de segurança antes. Execute uma consulta sem gravação:

```powershell
..\.venv\Scripts\python.exe -m app.import_odk_pilot --project-id 1 --expected 9
```

Confira a contagem, os códigos e os nomes dos laboratórios apresentados. Se forem os esperados, execute a importação, incluindo o cadastro dos códigos ainda ausentes:

```powershell
..\.venv\Scripts\python.exe -m app.import_odk_pilot --project-id 1 --expected 9 --apply --register-missing
```

Se receber **«Instrumento SLIPTA-ODK-PILOT 2026.10 ausente»**, a base ainda só contém o instrumento fictício da demonstração. Carregue o XLSForm original em **Instrumentos → Carregar XLSForm SLIPTA**, ou indique o caminho do XLSForm original em ambas as execuções com `--xlsform`:

```powershell
..\.venv\Scripts\python.exe -m app.import_odk_pilot --project-id 1 --expected 9 --xlsform "C:\caminho\SLIPTA_ODK_V3_validacao_tecnica.xlsx"
..\.venv\Scripts\python.exe -m app.import_odk_pilot --project-id 1 --expected 9 --apply --register-missing --xlsform "C:\caminho\SLIPTA_ODK_V3_validacao_tecnica.xlsx"
```

Substitua `C:\caminho` pela localização real do ficheiro. O importador só cria o instrumento se ele não existir **e** o XLSForm corresponder exactamente ao ficheiro e ao formulário previamente validados; uma versão existente divergente nunca é substituída. O comando aborta se a API devolver uma contagem diferente, identidades repetidas ou nomes incompatíveis com laboratórios existentes. Antes de gravar, pré-valida o lote completo e cria uma cópia SQLite e dos anexos em `LabQuality_Copilot_0.1.0\backups`. Indica quantas avaliações são novas, revistas ou inalteradas; voltar a executá-lo sem alteração das respostas não cria avaliações duplicadas. Se todos os laboratórios já estiverem cadastrados, omita `--register-missing`. Reinicie os serviços, filtre **Submissões reais ODK** e confira nove avaliações da fonte `odk:1:slipta_v3_2023_mozambique`. O comando usa exclusivamente as credenciais do `.env` local; não as coloque na linha de comandos nem envie o ficheiro para o Git.

Se aparecerem códigos ODK sem cadastro, crie os laboratórios em **Laboratórios** com o código exacto `tf_numero_laboratorio` e confirme o nome com o responsável; os códigos fictícios `SUL`, `CENTRO` e `NORTE` da demonstração não correspondem automaticamente a números da conta real. Volte a pré-validar e só então use **Sincronizar agora**. Mantenha o trabalhador activo e confirme a tarefa em **Importar dados → Tarefas de integração**; abra as avaliações marcadas **Real · ODK** e reveja a pontuação, os NA, as observações e os achados. Uma avaliação incompleta pode ficar sem percentagem. As nove avaliações da demonstração continuam identificadas como **Simulada** e não devem ser confundidas com as submissões da conta ODK.

Depois da primeira importação bem-sucedida, confirme projecto e laboratórios e active a sincronização automática; o trabalhador consulta aproximadamente a cada cinco minutos. A identidade `__id` evita duplicados por repetição da mesma submissão; uma edição de respostas ou comentários cria revisão histórica. Se o trabalhador indicar `no such table: odk_sync_configs`, pare os processos, faça uma cópia da base SQLite e, em `backend`, execute `..\.venv\Scripts\python.exe -m alembic upgrade head` antes de voltar a iniciar. **Não apresente os resultados ou estrelas como classificação SLIPTA oficial:** os totais do formulário e do PDF divergem em algumas secções e a importação da API em produção ainda precisa de ser confirmada na instalação autorizada.

Não é necessário apagar as nove avaliações simuladas para importar submissões reais. Os registos são identificados pela origem e podem coexistir sem colisão de identidade. Em **Visão geral** e **Avaliações**, escolha **Submissões reais ODK** no filtro de origem para apresentar só essas avaliações e os indicadores/acções a elas associados; os CSV exportados respeitam o mesmo filtro. Qualquer limpeza definitiva da demonstração deve acontecer apenas depois de validar a importação e de garantir uma cópia de segurança.

Para demonstrar a Meta com uma avaliação real, publique primeiro documentos normativos ou procedimentos institucionais aplicáveis ao laboratório e aos critérios relevantes, com a revisão apropriada. Revise os comentários para evitar enviar dados pessoais desnecessários à Meta API; o modelo recebe achados, excertos de comentários e conteúdo dos documentos publicados acessíveis. Solicite a análise, aguarde a tarefa e confira se as citações apontam para o texto autorizado e se os passos propostos fazem sentido. A pontuação vem da aplicação; o modelo sugere intervenções e a equipa aprova ou corrige cada proposta antes de criar uma acção.

## Email SMTP — opcional

Use uma conta SMTP autorizada, remetente válido e uma palavra-passe de aplicação quando o fornecedor a exigir:

```dotenv
LQ_SMTP_HOST=smtp.exemplo.org
LQ_SMTP_PORT=587
LQ_SMTP_USERNAME=<utilizador_smtp>
LQ_SMTP_PASSWORD=<palavra_passe_smtp>
LQ_SMTP_FROM=notificacoes@exemplo.org
LQ_SMTP_STARTTLS=true
```

Para SMTP sobre TLS implícito, use `LQ_SMTP_PORT=465`; os testes e o trabalhador utilizam essa modalidade automaticamente. Reinicie API e trabalhador e clique em **Testar**. Esse teste autentica e encerra a ligação sem enviar mensagem. Para ensaiar a entrega real, associe uma conta de teste com endereço sob o seu controlo, provoque uma notificação e confirme o estado no trabalhador e na caixa de entrada. Os endereços `@labquality.local` da demonstração não recebem emails. Sem SMTP, as notificações continuam disponíveis na aplicação.

Se surgir **SMTP 535**, o servidor recusou a autenticação: confira o login exacto do fornecedor e use uma chave SMTP activa ou palavra-passe de aplicação quando exigida, em vez da chave de API ou da palavra-passe normal da conta. Se utilizar **Brevo**, o servidor é `smtp-relay.brevo.com`, a porta normal é `587` com `LQ_SMTP_STARTTLS=true`, o utilizador é o **SMTP login** indicado em *SMTP & API*, e a senha é uma **chave SMTP**; confirme que não foi desactivada por inactividade. Um erro de STARTTLS/TLS pede conferir a combinação porta e cifragem; um timeout aponta para rede, firewall ou porta. O teste não verifica o remetente `LQ_SMTP_FROM` nem a entrega, pois não envia mensagens.

Para **Gmail pessoal**, use `LQ_SMTP_HOST=smtp.gmail.com`, `LQ_SMTP_PORT=587`, `LQ_SMTP_STARTTLS=true`, o endereço Gmail como utilizador e remetente, e a palavra-passe de aplicação dessa mesma conta. A verificação em dois passos deve estar activa para criar a palavra-passe de aplicação. Se o teste disser que a ligação foi interrompida, execute `Test-NetConnection smtp.gmail.com -Port 587` no PowerShell do mesmo computador: `TcpTestSucceeded=False` indica que o bloqueio ocorre antes da autenticação. Pode testar a porta 465 e, se estiver disponível, configurar `LQ_SMTP_PORT=465` (TLS implícito, sem STARTTLS adicional). Se a porta estiver acessível, a mensagem actualizada do teste indica se a interrupção ocorreu durante o início SMTP, STARTTLS ou autenticação; nunca partilhe a palavra-passe de aplicação nem o texto bruto da resposta SMTP.

## Demonstração e limites

O percurso de contingência cobre nove avaliações simuladas. A demonstração com dados reais depende da pré-validação e da importação da API ODK na instalação autorizada; ainda não foi confirmada nesta sessão. Mostre a IA apenas após uma execução real bem-sucedida, assinale a origem de cada avaliação e identifique o instrumento **SLIPTA-ODK-PILOT 2026.10** como provisório. Consulte também [estado da implementação](IMPLEMENTATION_STATUS.md) e [auditoria da pontuação SLIPTA](SLIPTA_V3_2023_SCORE_AUDIT.md).
