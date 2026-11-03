# Fontes de verificação das 12 secções SLIPTA V3:2023

Foram preparados **12 documentos independentes**, um por secção, para revisão e publicação em **Documentos** do LabQuality Copilot. Cada um inclui os códigos/títulos e uma **verificação de evidência específica para cada um dos 151 critérios do instrumento ODK piloto**. O catálogo de correspondência está em [criterion_evidence.tsv](../backend/samples/slipta_sources/criterion_evidence.tsv). A referência externa é a [checklist SLIPTA V3:2023 publicada pela ASLM](https://aslm.org/wp-content/uploads/2019/12/SLIPTA-Checklist-V3-22-Dec-2023.pdf). Estes roteiros não são procedimentos internos, prova de conformidade, decisão do auditor ou classificação oficial. As diferenças de contagem/pontuação entre o resumo do PDF e os itens numerados continuam documentadas na [conferência de pontuação](SLIPTA_V3_2023_SCORE_AUDIT.md); não foram corrigidas por suposição.

| Secção | Documento no repositório | Critérios do piloto |
|---|---|---:|
| 01 Documentos e registos | [SLIPTA-SEC-01-2023.txt](../backend/samples/slipta_sources/SLIPTA-SEC-01-2023.txt) | 10 |
| 02 Organização e liderança | [SLIPTA-SEC-02-2023.txt](../backend/samples/slipta_sources/SLIPTA-SEC-02-2023.txt) | 11 |
| 03 Gestão de pessoal | [SLIPTA-SEC-03-2023.txt](../backend/samples/slipta_sources/SLIPTA-SEC-03-2023.txt) | 14 |
| 04 Foco no cliente | [SLIPTA-SEC-04-2023.txt](../backend/samples/slipta_sources/SLIPTA-SEC-04-2023.txt) | 10 |
| 05 Gestão de equipamentos | [SLIPTA-SEC-05-2023.txt](../backend/samples/slipta_sources/SLIPTA-SEC-05-2023.txt) | 16 |
| 06 Avaliação | [SLIPTA-SEC-06-2023.txt](../backend/samples/slipta_sources/SLIPTA-SEC-06-2023.txt) | 9 |
| 07 Fornecedores e inventário | [SLIPTA-SEC-07-2023.txt](../backend/samples/slipta_sources/SLIPTA-SEC-07-2023.txt) | 12 |
| 08 Gestão dos processos | [SLIPTA-SEC-08-2023.txt](../backend/samples/slipta_sources/SLIPTA-SEC-08-2023.txt) | 27 |
| 09 Gestão da informação | [SLIPTA-SEC-09-2023.txt](../backend/samples/slipta_sources/SLIPTA-SEC-09-2023.txt) | 10 |
| 10 Eventos não conformes | [SLIPTA-SEC-10-2023.txt](../backend/samples/slipta_sources/SLIPTA-SEC-10-2023.txt) | 5 |
| 11 Melhoria contínua | [SLIPTA-SEC-11-2023.txt](../backend/samples/slipta_sources/SLIPTA-SEC-11-2023.txt) | 3 |
| 12 Instalações e segurança | [SLIPTA-SEC-12-2023.txt](../backend/samples/slipta_sources/SLIPTA-SEC-12-2023.txt) | 24 |
| **Total** | **12 documentos** | **151** |

Os três ficheiros anteriores `SLIPTA-REF-*` permanecem no repositório e, se já foram importados, na base de dados. O importador cria ou revê **apenas** os 12 documentos por secção; não apaga nem altera as fontes anteriores. Cada documento fica associado aos códigos exactos da sua secção. Os títulos reproduzem o instrumento piloto, inclusive alguns títulos ainda em inglês; o auditor deve confrontá-los com o XLSForm e a revisão adoptada antes de publicar. O texto foi redigido como **perguntas de verificação e evidências a pedir**, não como afirmações de que determinado laboratório falhou.

## Carregar rascunhos na instalação Windows

Depois do pull da branch, execute **a partir de `backend`**, com o `.env` da instalação já configurado:

```powershell
Set-Location -LiteralPath 'D:\irzelindo\Documentos Pessoais\Candidaturas\Meta Hackathon\hackathon\LabQuality_Copilot_0.1.0\backend'
& ..\.venv\Scripts\python.exe -m app.import_slipta_sources --admin-email admin@labquality.local --new-revisions
& ..\.venv\Scripts\python.exe -m app.import_slipta_sources --admin-email admin@labquality.local --apply --new-revisions
```

Use o email de um administrador activo da instituição **onde estão as nove avaliações ODK** se for diferente. O primeiro comando pré-valida sem gravar; o segundo cria os documentos como **rascunhos de âmbito institucional**. `--new-revisions` permite criar uma nova revisão em rascunho quando uma das 12 fontes já existe com conteúdo anterior; a versão publicada mantém-se até a nova ser aprovada e publicada. Repetir o comando com o mesmo conteúdo não cria duplicados. Uma fonte **retirada** bloqueia a importação e exige revisão manual. O pull do Git não modifica a base de dados local. Nenhuma avaliação ou pontuação é alterada.

1. Em **Documentos**, verifique os 12 textos, os códigos dos critérios, a versão da checklist e se o âmbito institucional é adequado aos laboratórios abrangidos. Para procedimentos específicos de um laboratório, crie fontes com âmbito desse laboratório.
2. Submeta as versões à revisão. **Outra pessoa autorizada**, diferente do autor, confirma a correspondência com a checklist, as evidências necessárias e a aplicabilidade; só depois aprova e publica. Publicar estas referências não substitui os procedimentos e registos próprios do laboratório.
3. Em **Avaliações**, abra uma submissão ODK e consulte os achados e a prontidão da análise. A Meta recebe apenas fontes **publicadas e autorizadas** pertinentes aos achados, com limite de 12 fontes e 30 achados por análise; o prompt pede **no máximo três propostas** priorizadas. Revise as citações e propostas no **Copiloto de qualidade** antes de criar uma acção. As fontes ajudam a formular verificações, mas não tornam a pontuação uma prova da causa ou da conformidade.
4. Se houver achados fora do contexto enviado, seleccione outra avaliação ou complemente a revisão manual. Um documento de referência oferece perguntas de verificação; a conclusão depende da submissão, de registos locais e da observação do auditor.

Fontes verificadas em 2 de Novembro de 2026. Se a instituição adoptar outra versão do formulário ou da checklist, revise os mapeamentos, edite os textos por nova revisão controlada e repita a validação antes de os publicar.
