# LabQuality Copilot

Plataforma de gestão da qualidade laboratorial: avaliações → achados → planos de melhoria → evidências → verificação. Backend FastAPI, interface Next.js/TypeScript e PostgreSQL em Docker. O desenvolvimento local também funciona com SQLite.

Versão de desenvolvimento **0.1.0**, iniciada em 23/10/2026. A definição completa da V1 continua a orientar o produto. Consulte [o estado das funcionalidades](docs/IMPLEMENTATION_STATUS.md) antes de apresentar a solução como pronta para utilização institucional.

## Instalação no directório Windows solicitado

Destino predefinido:

```text
D:\irzelindo\Documentos Pessoais\Candidaturas\Meta Hackathon\hackathon
```

Requisitos: **Python 3.12 ou superior**, **Node.js 22 ou superior**, npm e acesso à Internet para instalar dependências. O caminho `python` ou o launcher `py` deve estar disponível no terminal.

1. Descarregue e extraia o ZIP para uma pasta temporária, por exemplo `Downloads\LabQuality_Copilot`.
2. Abra PowerShell nessa pasta e execute:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install-windows.ps1 -Start
```

O instalador copia o projecto para o destino, cria `.env` com palavras-passe aleatórias, prepara `.venv`, instala as dependências fixadas, aplica as migrations, cria a demonstração e executa os testes do backend e a verificação TypeScript. Não substitui um destino que já contenha ficheiros. Se já extraiu o pacote directamente para o destino, execute o instalador dentro dessa pasta.

`-ExecutionPolicy Bypass` aplica-se apenas ao processo PowerShell invocado; o instalador não altera a política global do Windows.

Três janelas iniciam a API, o trabalhador e a interface. Abra **http://localhost:3000** quando a interface indicar que está pronta. Para parar, prima Ctrl+C nas três janelas. Para voltar a iniciar:

```powershell
Set-Location -LiteralPath 'D:\irzelindo\Documentos Pessoais\Candidaturas\Meta Hackathon\hackathon'
.\start-windows.ps1
```

A interface precisa da API; a análise por IA, as sincronizações ODK e o envio de email precisam também do trabalhador.

Se a API e o trabalhador falharem com `ImportError: DLL load failed while importing _util_cy: An Application Control policy has blocked this file`, o Windows bloqueou uma extensão nativa do SQLAlchemy. Pare as três janelas e, na raiz da instalação, execute:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\repair-sqlalchemy-windows.ps1
.\start-windows.ps1
```

O reparador usa a versão fixada em `backend/requirements.lock` e instala o SQLAlchemy a partir do código-fonte, sem extensões Cython. Precisa de acesso à Internet para obter o pacote. Preserva `.env`, contas e avaliações; a política de segurança do Windows permanece activa. O instalador passou a detectar esta falha e a executar o reparador automaticamente. Se surgir outro módulo bloqueado depois da reparação, guarde o novo traceback para diagnóstico.

## Contas da demonstração

Todas utilizam a palavra-passe gerada no ficheiro local `.env`, campo `LQ_DEMO_PASSWORD`. Essa palavra-passe só serve para as contas fictícias da instalação inicial. Alterá-la em `.env` não redefine palavras-passe de contas já existentes.

| Email | Acesso |
|---|---|
| `admin@labquality.local` | Administração da instituição e de toda a rede. |
| `qualidade@labquality.local` | Operações do Laboratório Sul. |
| `gestor@labquality.local` | Gestão e aprovação no Laboratório Sul. |
| `verificador@labquality.local` | Verificação nos três laboratórios. |
| `coordenacao@labquality.local` | Consulta da rede; sem edição operacional. |
| `parceiro@labquality.local` | Indicadores agregados. |

O cenário renovado tem Sul, Centro e Norte, com **três auditorias simuladas por laboratório** em Agosto, Setembro e Outubro de 2026. Os 151 itens principais e os 365 pontos calculáveis foram extraídos do XLSForm fornecido. As observações descrevem problemas plausíveis para ensaiar achados e planos; **não são dados recolhidos nesses laboratórios nem atribuem classificação oficial SLIPTA**.

A [conferência da checklist SLIPTA V3:2023](docs/SLIPTA_V3_2023_SCORE_AUDIT.md) identifica diferenças entre os totais das secções 1 e 5 e os máximos impressos por pergunta. Por isso, o instrumento `SLIPTA-ODK-PILOT 2026.10` tem pontuação **provisória** e não atribui estrelas. A regra `sum_applicable_v1` exclui do denominador itens NA justificados. A rubrica antiga `DEMO-QMS` permanece apenas como exemplo legado nos testes.

O [XLSForm ODK de Moçambique também foi conferido](docs/SLIPTA_V3_2023_SCORE_AUDIT.md#conferência-do-xlsform-odk-recebido): os seus 151 cálculos principais somam 365 pontos e confirmam a divergência do PDF. Foi preparada uma cópia piloto corrigida para a relevância do comentário 7.9(i), o resultado sem denominador e um media ausente. O instrumento publicado na demonstração é provisório; o formulário ainda não foi carregado ou ensaiado num servidor ODK real.

Para substituir os dados antigos **apenas da organização de demonstração** no SQLite Windows, pare API, trabalhador e interface; na raiz do repositório execute:

```powershell
Set-Location .\backend
..\.venv\Scripts\python.exe -m app.bootstrap --refresh-demo
Set-Location ..
.\start-windows.ps1
```

O comando cria antes um backup da base e evidências em `backend\.backups`, elimina as análises e acções da demonstração antiga e recria as nove avaliações do piloto. As sessões das contas de demonstração são revogadas: use a palavra-passe `LQ_DEMO_PASSWORD` do `.env`. **Recusa a limpeza** se houver submissões ODK/manuais ou contas adicionais naquela organização; nunca apaga outras organizações. Em PostgreSQL, use backup/migração controlada, pois este comando só aceita SQLite local. Executar `--demo` numa instalação existente não faz esta substituição.

## Utilizar a aplicação

Para um percurso completo com as nove submissões ODK, os avisos de avaliação incompleta, a publicação de fontes SLIPTA e o primeiro ensaio Meta, consulte o [guia de utilização](docs/GUIA_UTILIZADOR.md). O resumo também está disponível no menu **Guia de utilização** da aplicação.

1. Entre como administrador e consulte os indicadores. Experimente os filtros de laboratório e datas.
2. Em Avaliações, abra um resultado, consulte os achados e as revisões. Crie uma avaliação ou uma correcção.
3. Em Importar dados, descarregue o exemplo CSV, pré-valide-o e aplique a importação. Repetir o mesmo conteúdo não cria avaliações duplicadas.
4. Em Planos de melhoria, atribua uma acção e avance pelos estados. Anexe uma evidência e solicite verificação. Outra pessoa autorizada deve confirmar a eficácia para encerrar.
5. Em Documentos, guarde um rascunho, submeta-o a revisão e peça a outra pessoa a aprovação. Só documentos publicados entram no contexto da IA.
6. Consulte riscos, ocorrências, competências e equipamentos nos registos operacionais.
7. Depois de configurar a Meta API, solicite uma análise, consulte as fontes e reveja a proposta antes de a converter numa acção.

CSV e Excel usam as mesmas colunas do novo exemplo em `frontend/public/demo/slipta-pilot-assessments.csv`. O JSON correspondente ao novo piloto está em `backend/samples/slipta-pilot-assessments.json`. Uma linha tabular corresponde a um critério; a identidade da avaliação é a combinação da instituição, origem e identificador externo. Pontuações em falta permanecem em falta.

Para um instrumento publicado com `sum_applicable_v1`, indique `NA` ou `N/A` em `value` e uma justificação em `comment` no CSV/XLSX; no JSON use `{"not_applicable": true, "comment": "justificação"}` sem valor numérico. NA difere de uma resposta ainda por avaliar. A percentagem usa os pontos aplicáveis como denominador e o resultado apresenta também o máximo original e a quantidade de itens NA. Um instrumento com todos os itens NA não produz percentagem final. O piloto usa os cálculos do XLSForm para cada item principal; não atribui estrelas nem substitui a revisão das subperguntas pelo auditor.

## Configurar a Meta Model API

Siga o [guia de configuração e testes das três integrações](docs/INTEGRATIONS_SETUP.md) na sua instalação Windows. A página **Configuração** permite ao administrador testar Meta, ODK e SMTP sem importar avaliações ou enviar emails.

Obtenha a chave da conta autorizada em [Meta Model API](https://dev.meta.ai/products/meta-model-api). No `.env` da raiz:

```dotenv
LQ_MODEL_API_KEY=coloque-a-chave-localmente
LQ_MODEL_ID=muse-spark-1.3
LQ_MODEL_BASE_URL=https://api.meta.ai/v1
```

Reinicie a API e o trabalhador. A interface apresenta configuração e histórico; a execução real só fica confirmada quando uma análise terminar com sucesso. Sem chave, a operação devolve estado indisponível. Não existem respostas simuladas apresentadas como inferência real.

O adaptador usa a Responses API e valida uma estrutura JSON. As referências devem corresponder a documentos publicados acessíveis ao utilizador, e as citações devem existir no texto enviado. Esses controlos não provam que a recomendação é semanticamente correcta; a revisão humana continua obrigatória. Registam-se modelo, versão do prompt, fontes, consumo, duração e aceitação.

[Guia oficial de integração consultado](https://dev.meta.ai/docs/quickstart). O acesso efectivo da conta, os créditos e o modelo disponível ainda precisam de confirmação na instalação do utilizador.

## ODK e email

Configure `LQ_ODK_URL`, `LQ_ODK_EMAIL` e `LQ_ODK_PASSWORD` no servidor. O ficheiro XLSForm que define o questionário pode ser pré-validado em **Instrumentos → Carregar XLSForm SLIPTA**: a revisão exacta conferida cria o instrumento piloto caso ainda não exista, sem duplicá-lo. Outras revisões exigem revisão do mapeamento antes da publicação. O XLSForm não é um ficheiro de avaliações. Em **Importar dados**, um administrador ou gestor define projecto, formulário e mapeamento explícito dos campos. O campo de identidade tem de se manter estável nas edições. Para o XLSForm `slipta_v3_2023_mozambique`, o servidor mapeia os 151 cálculos de pontuação, NA e comentários conferidos. Os restantes instrumentos exigem mapeamento explícito das pontuações numéricas.

O conector lê OData por HTTPS e aplica as mesmas regras de importação. Não altera nem submete formulários no ODK. Uma sincronização aceita até 500 avaliações e é transaccional. A paginação só aceita o mesmo servidor e caminho esperados.

No ecrã **Importar dados**, escolha o instrumento piloto e indique o **ID do projecto ODK** que contém o formulário XML `slipta_v3_2023_mozambique`. Use **Pré-validar submissões ODK** para verificar laboratórios, datas, campos em falta e alterações previstas sem gravar. Cadastre os códigos reais `tf_numero_laboratorio` na instituição; `SUL`, `CENTRO` e `NORTE` pertencem apenas à demonstração. Depois, use **Sincronizar agora**, confira a tarefa e as avaliações marcadas **Real · ODK**, e só então active a sincronização automática (aproximadamente a cada cinco minutos). Filtre **Visão geral** e **Avaliações** por **Submissões reais ODK** para não misturar os indicadores com as nove simulações, sem precisar de apagar dados. A identidade `__id` evita duplicados; alterações do conteúdo criam revisões históricas. A configuração e as credenciais ficam no servidor. A validação da API com as submissões actuais deve ser efectuada na instalação autorizada, seguindo o [guia operacional](docs/INTEGRATIONS_SETUP.md#odk-central--ligação-antes-do-mapeamento).

Para email, configure `LQ_SMTP_*`. Sem SMTP, as notificações permanecem disponíveis na aplicação. Os emails enviados contêm apenas um aviso genérico para entrar na aplicação. Eventos são deduplicados na base de dados. Uma falha depois da tentativa de entrega fica como `uncertain`; o trabalhador não repete automaticamente uma entrega possivelmente concluída.

## PostgreSQL e Docker

O `.env` deve existir e conter `POSTGRES_PASSWORD` e `LQ_DEMO_PASSWORD` não vazios. O instalador Windows gera ambos. Alternativamente, copie `.env.example` e preencha esses valores com palavras-passe aleatórias; para o campo usado no URL PostgreSQL, prefira caracteres hexadecimais.

```bash
docker compose up --build -d
docker compose logs -f api worker web
```

O Compose configura PostgreSQL, API, trabalhador e interface, com volumes separados para a base de dados e evidências. Só a interface é publicada, em `127.0.0.1:3000`. O frontend encaminha os pedidos para a API interna; a chave do modelo nunca é enviada ao navegador.

Esta configuração é uma proposta executável, mas não foi executada em Docker nesta sessão. Antes de alojar no Coolify, validar as imagens, o domínio e o proxy, definir `LQ_ALLOWED_ORIGINS` com a origem HTTPS real, activar `LQ_COOKIE_SECURE=true`, rever recursos e ensaiar recuperação. Desactive `LQ_SEED_DEMO` numa instalação institucional. Não foi efectuado deploy.

Uma instituição nova pode ser criada explicitamente com `python -m app.bootstrap --admin-email email@instituicao.org --organization "Nome da instituição"`, fornecendo `LQ_ADMIN_PASSWORD` por variável de ambiente. Este comando nunca redefine uma conta existente.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `backend/app` | API, autorização, cálculo, importação, IA, trabalhador e integrações. |
| `backend/migrations` | Migration Alembic inicial. |
| `backend/tests` | Regressões de cálculo, autorização, estados, IA e recuperação. |
| `frontend/src` | Interface, filtros, formulários e encaminhamento da API. |
| `frontend/tests` | Percurso integrado no navegador, em ambiente isolado. |
| `scripts` | Arranque dos serviços no Windows. |
| `docs` | Âmbito, estado e validação desta entrega. |

## Desenvolvimento manual e testes

Depois da instalação Windows, no directório `backend`:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m alembic check
```

No directório `frontend`:

```powershell
npm.cmd run typecheck
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

O teste de navegador inicia API e interface próprias nas portas **18000 e 3100**, com base temporária e serviços externos desactivados. Não reutiliza os serviços de desenvolvimento nem as suas credenciais. Para uma localização diferente do Python, defina `LQ_TEST_PYTHON`.

Em Linux/WSL, use Python 3.12+ para criar `.venv` na raiz, instale `backend/requirements.lock`, copie e preencha `.env`, execute `python -m app.bootstrap --demo` dentro de `backend` e inicie API, trabalhador e `npm run dev` em terminais separados. A configuração lê `.env` na raiz ou em `backend`.

## Cópias de segurança locais

Dentro de `backend`, com o Python da `.venv`:

```powershell
..\.venv\Scripts\python.exe -m app.backup create ..\backups
..\.venv\Scripts\python.exe -m app.backup restore ..\backups\NOME_DO_BACKUP ..\recuperacao-teste
```

A ferramenta SQLite usa a API de backup da base de dados e copia os anexos privados. A recuperação verifica hashes e aceita apenas um destino vazio. O backup não contém `.env`; as configurações devem ser preservadas separadamente. Configure `LQ_DATABASE_URL` e `LQ_STORAGE_DIR` para os caminhos recuperados antes de iniciar a cópia restaurada.

Para PostgreSQL, preparar backup com `pg_dump` e cópia do volume de evidências, com política de consistência e recuperação ensaiada no ambiente de implantação. Os objectivos de perda e tempo de recuperação da proposta ainda não foram medidos.

## Sincronização do código

O código está no repositório [LabQuality_Copilot_Meta](https://github.com/irzelindo/LabQuality_Copilot_Meta). As alterações em desenvolvimento são feitas em branches `feature/*` e, depois de validadas, podem ser enviadas directamente para o repositório sem pull request. Execute `git fetch origin` e mude para a branch pretendida no clone do projecto; conserve o `.env`, a base SQLite e os anexos locais fora dos commits. O ZIP 0.1.0 corresponde à entrega inicial e não recebe automaticamente as alterações das branches.

## Participação e próximos marcos

Este código começou a ser preparado em **23/10/2026**, por instrução do autor do projecto. A compatibilidade de trabalho anterior com a submissão competitiva precisa de confirmação nas regras finais do hackathon. Preserve o histórico e identifique a contribuição desenvolvida no período elegível.

Os próximos marcos incluem testar a Meta API com a conta autorizada, validar o mapeamento oficial SLIPTA, testar ODK e SMTP reais, ensaiar PostgreSQL/Docker e recuperação no servidor e executar um piloto com profissionais de qualidade. Não existem parceiros formalizados ou benefícios medidos nesta entrega.
