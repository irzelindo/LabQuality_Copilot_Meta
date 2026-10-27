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

O instrumento `SLIPTA-ODK-PILOT 2026.10` contém os 151 itens e 365 pontos calculáveis do XLSForm partilhado. No ecrã **Importar dados**, indique o projecto ODK e seleccione este instrumento: o servidor usa os campos calculados, as respostas NA e os comentários mapeados para esta versão. Faça a primeira sincronização com uma submissão de ensaio e confirme o código de laboratório, a data, os achados e a exclusão NA. Só depois active a sincronização automática, com verificação aproximadamente a cada cinco minutos. **Não apresente as avaliações ou estrelas como classificação SLIPTA oficial:** o formulário ainda tem divergências de totais face ao PDF e os caminhos OData carecem de teste num servidor real. As submissões idênticas não duplicam e as edições ficam em revisões.

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

O percurso apresentável cobre nove avaliações simuladas com critérios do XLSForm, em momentos diferentes, filtros, achados, plano de melhoria, evidência e verificação independente. Mostre a IA apenas após uma execução real bem-sucedida e identifique o instrumento **SLIPTA-ODK-PILOT 2026.10** como provisório e as avaliações como simuladas. A classificação oficial SLIPTA e a integração com uma submissão ODK real permanecem pendentes de validação. Consulte também [estado da implementação](IMPLEMENTATION_STATUS.md) e [auditoria da pontuação SLIPTA](SLIPTA_V3_2023_SCORE_AUDIT.md).
