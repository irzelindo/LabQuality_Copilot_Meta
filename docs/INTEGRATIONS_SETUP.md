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

O XLSForm SLIPTA recebido ainda requer validação da pontuação e mapeamento explícito de respostas Y/P/N/NA e dos identificadores. **Não sincronize esse formulário como avaliações oficiais nesta fase.** Para experimentar a importação agora, use o CSV/Excel/JSON da demonstração e repita a importação: as nove avaliações de três momentos distintos permanecem e as reimportações idênticas não as duplicam. Quando houver um formulário ODK de ensaio com pontuações numéricas e identidade estável, preencha projecto, XML ID e campos no ecrã **Importar dados** e ensaie primeiro com submissões fictícias.

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

## Demonstração e limites

O percurso apresentável já cobre nove avaliações em momentos diferentes, filtros, achados, plano de melhoria, evidência e verificação independente. Mostre a IA apenas após uma execução real bem-sucedida e identifique o instrumento **DEMO-QMS 1.0** como fictício. A classificação oficial SLIPTA, o mapeamento do XLSForm e as integrações externas permanecem pendentes de validação. Consulte também [estado da implementação](IMPLEMENTATION_STATUS.md) e [auditoria da pontuação SLIPTA](SLIPTA_V3_2023_SCORE_AUDIT.md).
