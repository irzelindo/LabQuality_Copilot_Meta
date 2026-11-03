# Actualizar no Windows sem substituir os dados

A entrega parte da versão disponível no GitHub. Correcções existentes apenas no disco D: precisam de ser comparadas antes de substituir código. O procedimento precisa de validação no computador do autor.

1. Pára API, trabalhador e frontend com Ctrl+C. Identifica a pasta actual e o caminho da base configurada em `.env`.
2. Preserva uma cópia da instalação. Para SQLite, dentro do backend actual, executa `..\.venv\Scripts\python.exe -m app.backup create ..\backups`. Conserva `.env` separadamente. Para PostgreSQL, usa o backup da instalação e uma cópia consistente dos anexos.
3. Extraia o ZIP para uma pasta nova. Não executes `install-windows.ps1` sobre a instalação real: esse instalador prepara a demonstração, não actualiza dados.
4. Compara as correcções locais e copia apenas o código actualizado para a instalação actual. Preserva `.env`, `.venv`, bases de dados, `storage`, `backups` e ficheiros privados.
5. Na raiz actual: `& .\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.lock`.
6. Dentro de backend: `& ..\.venv\Scripts\python.exe -m alembic upgrade head` e `& ..\.venv\Scripts\python.exe -m pytest -q`. Esta entrega não acrescenta tabelas nem migrations. Compara primeiro quaisquer migrations adicionais existentes apenas na tua instalação.
7. Dentro de frontend: `npm.cmd ci --no-audit --no-fund`, `npm.cmd run typecheck` e `npm.cmd run build`.
8. Inicia os três serviços pelo método actual. Confirma as nove avaliações e o histórico. Não repitas a importação ODK apenas para testar a actualização.
9. Em Documentos, pré-valida e importa `slipta_sources_v3.json`, como rascunhos. Revê e publica os critérios necessários, com aprovação independente.
10. Configura a chave Meta no `.env`, reinicia API e trabalhador e conclui a validação descrita no guia.

Se a contagem ou o histórico divergirem, pára os serviços e investiga a configuração da base antes de inserir ou apagar registos. Uma instalação nova com dados fictícios pode estar a utilizar outra base.

## Recriar as referências

Dentro de backend:

```powershell
& ..\.venv\Scripts\python.exe -m app.slipta_sources --pdf "CAMINHO\SLIPTA-Checklist-V3-22-Dec-2023.pdf" --xlsform "CAMINHO\SLIPTA_ODK_V3_validacao_tecnica.xlsx" --output ..\private\slipta_sources_v3.json
```

O pacote regista os hashes dos originais. Revê diferenças antes de publicar novas versões.

## Importação ODK opcional

Confere as identidades e o instrumento antes de utilizar uma ferramenta diferente da que importou as nove avaliações:

```powershell
& ..\.venv\Scripts\python.exe -m app.import_odk_pilot --project-id 1 --expected 9 --xlsform "CAMINHO\SLIPTA_ODK_V3_validacao_tecnica.xlsx" --admin-email "ADMINISTRADOR_DA_INSTALACAO"
```

Sem `--apply`, o comando apenas pré-valida e reverte toda a transacção. `--register-missing` permite preparar laboratórios e instrumento em falta dentro dessa transacção. `--apply` grava explicitamente. O acesso usa `LQ_ODK_URL`, `LQ_ODK_EMAIL` e `LQ_ODK_PASSWORD` do servidor. O conector apenas lê ODK.
