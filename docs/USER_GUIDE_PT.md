# LabQuality Copilot: guia de utilização

## Antes de actualizar

A versão entregue melhora o percurso existente. As nove avaliações importadas estão no teu computador e não foram acedidas ou alteradas nesta execução. Faz uma cópia de segurança da base de dados e dos anexos antes de substituir código. Preserva `.env`, bases SQLite, `storage`, `backups` e as configurações do servidor. Não executes a criação da demonstração numa instalação que deva conter apenas dados reais.

Se trabalhas a partir de Git, actualiza primeiro a cópia remota com correcções locais que ainda não estejam no repositório. Esta entrega parte da versão `main` disponível no GitHub; não contém alterações que existam apenas no teu disco D:.

Com a API e o trabalhador parados, aplica o código actualizado, instala `backend/requirements.lock`, aplica `alembic upgrade head`, executa os testes e reconstrói o frontend. Não foi adicionada nenhuma alteração de esquema nesta entrega. O roteiro de actualização está em `docs/UPDATE_WINDOWS.md`.

## Palavras importantes

- **Avaliação:** as respostas de uma auditoria para um laboratório e uma data.
- **Achado:** uma lacuna registada num critério com pontuação abaixo do máximo. Resposta em falta não é convertida automaticamente num achado.
- **Referência:** o requisito ou orientação que ajuda a fundamentar uma decisão.
- **Procedimento:** instrução aprovada sobre a forma de trabalhar no laboratório.
- **Acção:** trabalho atribuído para resolver um achado.
- **Evidência:** registo ou ficheiro que demonstra o trabalho realizado.
- **Verificação:** revisão da eficácia da acção por outra pessoa autorizada.

## 1. Conferir uma avaliação

Entra com a tua conta. No menu **Avaliações**, abre um dos nove registos. Confirma laboratório, data, instrumento, revisão, respostas e comentários. Os dados em falta continuam em falta. Os resultados do piloto não atribuem estrelas SLIPTA oficiais.

Se houver um erro na origem, corrige-o no ODK e utiliza uma importação que preserve a identidade externa. Uma alteração cria uma revisão, sem apagar o histórico. Antes de repetir uma importação por uma ferramenta diferente, verifica se usa a mesma combinação de instituição, origem e identificador externo, para evitar duplicados.

## 2. Preparar os documentos

O ficheiro `slipta_sources_v3.json` acompanha a entrega privada. Foi preparado a partir da checklist e do XLSForm partilhados. Contém 151 referências, com texto português, trechos originais em inglês, páginas e códigos de critérios.

Como administrador, abre **Documentos**, escolhe o pacote JSON e carrega em **Pré-validar referências**. Confirma a contagem e escolhe **Importar rascunhos**. Repetir exactamente o pacote não cria cópias adicionais.

Pesquisa o critério de um achado, por exemplo `1.1`. Abre o documento e compara o conteúdo com o original. Carrega em **Submeter à revisão**. Outra pessoa autorizada entra com a sua própria conta e escolhe **Aprovar documento** e depois **Publicar versão**. A pessoa que criou o documento não pode aprová-lo. Para começar, basta rever os documentos correspondentes ao pequeno grupo de achados que vais demonstrar.

A checklist é uma referência externa. Publicá-la na aplicação não significa que o laboratório cumpre os requisitos nem que esse texto é um procedimento local. Acrescenta os procedimentos locais autorizados quando forem necessários.

## 3. Configurar e verificar a Meta

No `.env` da raiz do projecto, configura localmente:

```dotenv
LQ_MODEL_API_KEY=chave-da-tua-conta
LQ_MODEL_ID=muse-spark-1.3
LQ_MODEL_BASE_URL=https://api.meta.ai/v1
```

Confirma o modelo disponível na tua conta. Mantém a chave fora do Git, do chat e das capturas de ecrã. Reinicia a API e o trabalhador depois de alterar estas variáveis.

Em PowerShell, dentro de `backend`, podes testar o acesso sem enviar dados laboratoriais:

```powershell
& ..\.venv\Scripts\python.exe -m app.verify_meta --probe --output ..\private\meta_probe.json
```

Este teste envia um pequeno pedido para responder READY. Um resultado positivo confirma o acesso à conta. A qualidade de uma análise fundamentada precisa de validação separada na aplicação.

## 4. Analisar com Meta

Na avaliação, carrega em **Analisar com Meta**. A aplicação abre **Copiloto de qualidade** com essa avaliação seleccionada. Também podes escolher a avaliação directamente nesse menu.

A preparação mostra revisão actual, número de achados, fontes aplicáveis e configuração da chave. Selecciona até cinco achados e o idioma das propostas. O sistema começa pelos primeiros cinco, dando prioridade aos marcados como críticos. Os restantes podem ser analisados em novos grupos.

Abre **Fontes que a Meta irá receber**. Confirma a autorização de utilização dos comentários e trechos. Se aparecer falta de fonte, volta a Documentos e conclui a publicação de uma referência associada ao código do critério. Usa **Verificar novamente** depois de resolver o requisito.

Quando estiver pronto, carrega em **Gerar propostas com Meta**. A API cria uma tarefa e o trabalhador executa-a. A janela actualiza o estado automaticamente. A chave configurada, por si só, não comprova uma execução bem-sucedida.

## 5. Rever e criar uma acção

Numa análise concluída, lê a justificação, os passos, o critério de conclusão e a passagem citada. Abre as fontes quando precisares de contexto. A correspondência textual da citação não prova que a recomendação é adequada.

Carrega em **Rever e criar acção**. Ajusta o texto, escolhe um responsável e define o prazo. A aplicação guarda uma proposta de acção. O modelo não executa o trabalho nem encerra o achado automaticamente.

Usa **Relatório para impressão / PDF** para abrir uma versão para impressão, com modelo, versão do prompt, fontes, duração e estado da proposta. No navegador, utiliza Imprimir e Guardar como PDF.

## 6. Executar e verificar

Em **Planos de melhoria**, abre a acção. O gestor aprova a proposta. O responsável inicia o trabalho, regista a execução e anexa uma evidência verdadeira. Depois solicita verificação.

Outra pessoa autorizada selecciona a evidência e regista se a acção foi eficaz, com justificação. Uma acção eficaz pode ser encerrada. Um resultado ineficaz exige acompanhamento e reabertura.

## Resolver dificuldades

| Situação | O que verificar |
| --- | --- |
| Faltam fontes publicadas | Estado publicado, acesso ao laboratório e códigos de critérios correspondentes. |
| Sem achados | Respostas e instrumento da avaliação. Não cries lacunas fictícias para activar o botão. |
| Falta configurar a chave | `.env`, conta Meta e reinício da API e trabalhador. |
| Na fila durante muito tempo | Trabalhador iniciado na mesma base de dados e com a mesma configuração. |
| Falha HTTP 401/403 | Chave, permissões da conta e endpoint. Não publiques a chave no erro. |
| Falha HTTP 429 | Créditos e limites do fornecedor. Aguarda e volta a tentar com um grupo menor. |
| Resposta incompleta ou citação inválida | Reduz o grupo, confere o texto das fontes e solicita nova análise. |
| Fonte retirada ou avaliação revista | Executa nova análise sobre a revisão actual e fontes publicadas. |

## Antes de apresentar ao júri

Valida uma execução real da Meta, revê as recomendações com um profissional de qualidade e mede o tempo de preparação de um plano aceite. Utiliza `docs/PILOT_EVALUATION.csv` para registar medições reais. A apresentação em inglês inclui seis slides e notas de fala. Enquanto faltar a validação real, mantém essa limitação explícita.
