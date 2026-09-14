# Auditoria geral da documentação

| Campo | Valor |
|-------|-------|
| **Data** | 2026-09-13 |
| **Participantes** | @GuidaGaita (solicitante) · Claude Code (Claude Opus 5) |
| **Pedido** | "Faça uma auditoria geral e, se achado algum erro ou inconsistência, arrume." |
| **Escopo** | `docs/` (todos os documentos, ADRs e registros), `README.md`, `CLAUDE.md`, constituição, templates do GitHub e configuração do Spec Kit |
| **Base** | `develop` após a release `v0.1.0` |
| **Resultado** | 25 achados, todos corrigidos; 11 refinamentos registrados (R-008 a R-018) |

## 1. Método

1. **Leitura cruzada** de todos os documentos, procurando contradições entre requisitos, arquitetura, segurança, testes, processo, roadmap e ADRs.
2. **Análise de segurança** do modelo de ameaças e do ciclo de vida das chaves, procurando caminhos não cobertos pelas mitigações.
3. **Verificação de fatos contra as ferramentas**, lendo os scripts e as skills instalados do Spec Kit 1.0.6 em vez de confiar na documentação escrita.
4. **Verificações automáticas** de links, âncoras, IDs de requisitos e referências a ADRs, antes e depois das correções.

## 2. Fatos verificados nas ferramentas

| Afirmação da documentação | Verificação | Resultado |
|---------------------------|-------------|-----------|
| Branches `spec/NNN-slug` funcionam com o Spec Kit sem a extensão git | `common.py` localiza a feature por `SPECIFY_FEATURE` ou `.specify/feature.json`, nunca pelo nome da branch | ✅ Correta |
| Status das specs em pt-BR não quebra os comandos | Nenhuma skill `speckit-*` lê o valor de **Status** | ✅ Correta |
| Toda spec termina com *Histórico de revisões* sem editar templates | O template padrão não tem a seção; `common.py` consulta `.specify/templates/overrides/` antes dos templates padrão | ❌ Inconsistente → A18 |
| `/speckit-taskstoissues` publica tarefas como issues | A skill usa ferramentas do **servidor MCP do GitHub** (`list_issues`), não configurado no projeto | ❌ Incompleta → A19 |

## 3. Achados e correções

**Severidade:** 🔴 Alta (segurança ou regra que levaria a implementação errada) · 🟡 Média (inconsistência que bloquearia ou confundiria uma unidade) · 🟢 Baixa (clareza, completude ou desatualização).

| ID | Sev. | Achado | Correção | Refinamento |
|----|:----:|--------|----------|-------------|
| A01 | 🔴 | Quem tivesse um token roubado podia adivinhar a senha mestra **sem limite** por RF-06 (troca de senha) e RF-07 (exclusão de conta), porque RN-14 só protegia o login. | Nova RN-16: falhas contam no mesmo controle de tentativas; no limite, 429 e revogação de todas as sessões. Ameaça A11 em `04`. | R-008 |
| A02 | 🟡 | Senha mestra atual errada em sessão válida respondia 401, que clientes interpretam como sessão expirada. | Novo erro 403 `INVALID_MASTER_PASSWORD`. | R-008 |
| A03 | 🟡 | O modelo de dados tinha coluna `nonce` só em `credentials`; `wrapped_dek` e `session_wrapped_dek` também usam AES-GCM e não tinham onde guardar o nonce. | Formato único `nonce ‖ texto cifrado ‖ tag` em uma coluna, documentado em `04 §3.2`. | R-010 |
| A04 | 🟡 | Senha mestra sem normalização Unicode: "é" pré-composto e "e" + acento combinante geram hashes diferentes. | RN-02 e `04`: normalização NFKC antes de validar, gerar hash ou derivar chaves. | R-009 |
| A05 | 🟢 | SHA-256 e HKDF "sobre o token" sem definir se a entrada é a string base64url ou os bytes. | Operações sobre os 32 bytes decodificados; token de outro tamanho → 401. | R-011 |
| A06 | 🟢 | `login_throttles` guarda SHA-256 **sem sal** de e-mails tentados, sem registro do risco. | Novo ativo e novo risco aceito em `04`. | R-011 |
| A07 | 🟢 | RN-08 (nunca retornar senhas em listas) não cobria o relatório de saúde, que agrupa credenciais por senha reutilizada. | RN-08 inclui RF-16; caso de borda na unidade 005. | R-013 |
| A08 | 🟢 | Caso de borda do avaliador citava "limite definido na spec", um limite inexistente. | RN-11: entrada de 1 a 1024 caracteres. | R-012 |
| A09 | 🟢 | E-mail sem formato nem tamanho máximo definidos. | RN-01: formato válido, até 254 caracteres. | R-013 |
| A10 | 🟡 | RN-10 proibia "comprimento menor que o número de conjuntos", o que é **inalcançável** (mínimo 8 > 4 conjuntos); o catálogo tinha um teste impossível ("comprimento 3 com 4 conjuntos" já cai no mínimo). | Cláusula substituída por explicação; teste trocado por "comprimento 8 com 4 conjuntos e `exclude_ambiguous`". | R-012 |
| A11 | 🟡 | Métrica de cobertura divergente: "linhas" em CS-03 e RNF-09; "linhas e *branches*" no ADR-0013 e em `07` (`--cov-branch`). | "Linhas e ramificações" em todos. | R-016 |
| A12 | 🟢 | RNF-12 omitia RF-07 (também usa Argon2id) e RF-16, e não definia o tamanho das credenciais na medição. | Operações completas e cofre de credenciais de até 1 KB. | R-016 |
| A13 | 🟡 | Banco padrão `sqlite:////data/cofre.db` (caminho absoluto de Linux) faria o comando `uv run uvicorn` documentado falhar no Windows. | Padrão relativo `./data/cofre.db`; o compose define `/data`. | R-015 |
| A14 | 🟡 | `uvicorn cofre.main:app` pressupõe um `app` de módulo, mas a arquitetura e os testes usam a fábrica `create_app(settings, clock)`. | `uvicorn cofre.main:create_app --factory`; seção "Inicialização" em `03 §5`. | R-015 |
| A15 | 🟢 | RNF-14 e RNF-15 não estavam em nenhuma unidade; RN-16 (nova) e RN-08 faltavam no roadmap. | Unidade 001 recebe RNF-14/RNF-15; 002 recebe RN-16; 005 recebe RN-08. | R-016 |
| A16 | 🟢 | RNF-12 exigia "teste de desempenho" sem nível de teste correspondente; `03 §2.3` listava menos diretórios de teste que `07`. | Nível `perf` (fora da execução padrão), inclusive no ADR-0013; árvore de diretórios alinhada. | R-016 |
| A17 | 🟢 | `/health` sem contrato para banco indisponível. | 200 `{"status": "ok"}` ou 503 `SERVICE_UNAVAILABLE`. | R-014 |
| A18 | 🟡 | O processo exigia *Histórico de revisões* em toda spec, mas o template não tinha a seção e era proibido editar templates. | Override `.specify/templates/overrides/spec-template.md` com versão, status `Rascunho`, citação de IDs e histórico. | R-018 |
| A19 | 🟡 | `/speckit-taskstoissues` depende do servidor MCP do GitHub, não configurado; a documentação o apresentava como pronto. | Requisito documentado, com alternativa via `gh issue create`. | R-017 |
| A20 | 🟢 | `README.md` e `CLAUDE.md` descreviam o incremento 0 como em andamento, apesar da release `v0.1.0`. | Estado atualizado e próximo passo explícito. | — |
| A21 | 🟢 | Link relativo no template de PR não resolve dentro da descrição de um PR. | Caminho em texto. | — |
| A22 | 🟢 | Relatórios de testes "obrigatórios a cada incremento" incluíam o incremento 0, que não tem testes. | Obrigatórios a partir do incremento 1. | — |
| A23 | 🟢 | Governança não indicava que o board ainda não existe nem que as labels já foram criadas. | Situação explícita em `06 §5`. | — |
| A24 | 🟢 | Lista quebrada em `03 §3` e termos usados sem definição no glossário (NFKC, bloqueio de login). | Lista unificada; termos adicionados. | — |
| A25 | 🟢 | Diagrama de status da spec não previa refinamento **antes** da implementação. | Transição de refinamento no estado `Aprovada`. | — |

## 4. Verificado sem achados

- Fluxo de chaves (cadastro, login, requisição, logout) coerente entre `03`, `04`, ADR-0008 e ADR-0009.
- Tabela de ADRs do `README.md` idêntica ao índice de `docs/adr/`.
- Constituição, `CLAUDE.md` e `05-processo-sdd.md` descrevem o mesmo fluxo de duas fases.
- Exceções de exposição de senha (RNF-04) coerentes com os endpoints.
- Nenhum ADR aceito precisou mudar de decisão. O ADR-0013 recebeu apenas a correção da lista de marcadores, coerente com o teste de desempenho que ele já previa.

## 5. Versões resultantes

| Documento | Antes | Depois |
|-----------|-------|--------|
| `01-visao-geral.md` | 1.0.0 | 1.0.1 |
| `02-requisitos.md` | 1.0.0 | 1.1.0 |
| `03-arquitetura.md` | 1.0.0 | 1.1.0 |
| `04-seguranca.md` | 1.0.0 | 1.1.0 |
| `05-processo-sdd.md` | 1.0.0 | 1.1.0 |
| `06-governanca.md` | 1.0.0 | 1.0.1 |
| `07-estrategia-de-testes.md` | 1.0.0 | 1.1.0 |
| `08-ambiente-e-agentes.md` | 1.0.0 | 1.1.0 |
| `09-roadmap.md` | 1.0.0 | 1.0.1 |
