# Registro de erros lógicos

Erros que compilavam e rodavam, mas faziam a coisa errada, encontrados durante o desenvolvimento do Cofre (incrementos 1 a 4). Cada entrada traz detecção, causa, correção e prevenção. Quando a causa-raiz estava na especificação, ela aponta para o refinamento em [registro-de-refinamentos.md](registro-de-refinamentos.md).

**Critério de classificação.** Um programador perfeito, lendo só a spec, teria escrito o código certo? Se sim, o erro é de **implementação** e fica só aqui. Se não, é **defeito de especificação** e também entra no registro de refinamentos.

**Como cada erro foi detectado.** Nenhum foi detectado por revisão humana independente: o projeto é individual, e a revisão foi feita pela própria IA (`/code-review`) e lida depois pelo mantenedor ([ADR-0012](adr/0012-revisao-de-codigo-em-projeto-individual.md)). Os detectores foram testes, o CI e a revisão assistida por IA. Isso é uma limitação do processo, discutida no [relatório técnico-ético](relatorios/relatorio-etico-tecnico.md#2-pilar-1-alucinação-e-código-inseguro-ou-destrutivo).

| ID | Erro | Detectado por | Origem | Classe |
|----|------|---------------|--------|--------|
| E-01 | Gate de cobertura ativo em execuções parciais | Teste do harness | Unidade 001 | Implementação |
| E-02 | Testes herdavam `COFRE_*` do shell | `/speckit-converge` e teste vermelho | Unidade 001 | Implementação |
| E-03 | Tag de ação de CI inexistente | CI, no primeiro push | PR #63 | Implementação (informação inventada) |
| E-04 | Trecho da senha do banco na mensagem de erro | `/code-review` | PR #63 | Implementação |
| E-05 | `/health` respondia 200 com o banco corrompido | `/code-review` | PR #63 | Plano da unidade 001 (R-025) |
| E-06 | Bloqueio de login contornável com logins em paralelo | `/code-review` | PR #69 | Especificação (R-026) |
| E-07 | Corrida no limite do cofre e no `PATCH` | `/code-review` | PR #70 | Implementação |
| E-08 | Avaliador dava nota máxima a `"a"` × 100 | `/code-review` | PR #74 | Especificação (R-027) |
| E-09 | Testes que não podiam falhar | Leitura dos testes na revisão | PR #70 e unidade 004 | Teste |

## E-01 · Gate de cobertura ativo em execuções parciais

- **Detecção:** testes de autoverificação do harness (`pytester`) falharam ao rodar com `-m unit`, `-k` e caminho explícito.
- **Causa:** o `pytest-cov` guarda um *namespace* de opções próprio, criado antes da leitura completa da linha de comando. O plugin do harness zerava a opção do `pytest`, mas não a do `pytest-cov`, e uma execução parcial falhava por cobertura baixa.
- **Correção:** o plugin passou a zerar também `_cov.options.cov_fail_under`.
- **Prevenção:** os testes de autoverificação cobrem `-m`, `-k` e caminho explícito.

## E-02 · Testes herdavam variáveis `COFRE_*` do shell

- **Detecção:** `/speckit-converge` (FR-029), confirmado por teste vermelho: `COFRE_LOG_LEVEL=WARNING` no shell quebrava os testes de log.
- **Causa:** o `pydantic-settings` lê o ambiente mesmo com argumentos explícitos e em `model_validate`. A primeira correção proposta pela IA (`model_validate`) também falhou no teste.
- **Correção:** subclasse de teste `IsolatedSettings`, com `settings_customise_sources` restrito aos argumentos (T056).
- **Prevenção:** a fixture `settings` de `tests/conftest.py` usa `IsolatedSettings`, que ignora o ambiente do shell; o comportamento da biblioteca passou a ser verificado por teste, não presumido.

## E-03 · Tag de ação de CI inexistente

- **Detecção:** o CI falhou no primeiro push do [PR #63](https://github.com/GuidaGaita/bootcamp/pull/63).
- **Causa:** o workflow usava `astral-sh/setup-uv@v10`. A IA deduziu a tag a partir da release `v10.2.0`, mas o projeto publica só versões completas.
- **Correção:** versão fixada em `v10.2.0`.
- **Prevenção:** conferir no repositório da ação se a tag existe antes de commitar o workflow. `tests/unit/test_ci_workflow.py` lê o workflow, mas não valida tags; o CI continua sendo o detector.

## E-04 · Trecho da senha do banco na mensagem de erro

- **Detecção:** `/code-review` do [PR #63](https://github.com/GuidaGaita/bootcamp/pull/63), com a suíte verde (achado R1).
- **Causa:** `make_url` lança `ValueError` com um trecho da URL. Com `COFRE_DATABASE_URL=postgresql://user:p@ss:w0rd@host/db`, a `ConfigurationError` mostrava `w0rd@host`, o que viola FR-019 e RNF-04. A IA tinha escrito um teste de "nunca ecoar o valor", mas só para um tipo de erro.
- **Correção:** o erro é capturado e a mensagem não inclui o valor recebido.
- **Prevenção:** teste de regressão com senha na URL; a regra de [docs/04 §5](04-seguranca.md) passou a ser testada para cada caminho de erro, não só para o mais provável.

## E-05 · `/health` respondia 200 com o banco corrompido

- **Detecção:** `/code-review` do [PR #63](https://github.com/GuidaGaita/bootcamp/pull/63) (achado R2).
- **Causa:** o `ping` reaproveitava a conexão do *pool*, e `SELECT 1` não lê o arquivo do banco. Falha do plano (research R6), não da spec, que já exigia 503 com o banco indisponível (FR-003).
- **Correção:** banco em arquivo com `NullPool`; `ping` lê `sqlite_master`; banco em memória com `StaticPool`. Refinamento **R-025**.
- **Prevenção:** teste com arquivo de banco corrompido (`tests/integration/test_database.py`).

## E-06 · Bloqueio de login contornável com logins em paralelo

- **Detecção:** `/code-review` do [PR #69](https://github.com/GuidaGaita/bootcamp/pull/69) (achados 1, 2 e 3), com a suíte verde.
- **Causa:** consultar o bloqueio, verificar a senha e contar a falha eram passos separados ("ler, somar, gravar"). Vinte e quatro logins paralelos passavam do limite de 5 tentativas (RN-14, RN-16), e duas primeiras falhas simultâneas geravam `IntegrityError` (500). A spec não dizia que a contagem precisava ser atômica.
- **Correção:** a tentativa é contada antes da verificação, por um `INSERT ... ON CONFLICT DO UPDATE` atômico. Refinamento **R-026** (spec 002, FR-006 e FR-007).
- **Prevenção:** teste com 24 logins paralelos que admite no máximo 5 palpites.

## E-07 · Corrida no limite do cofre e no `PATCH`

- **Detecção:** `/code-review` do [PR #70](https://github.com/GuidaGaita/bootcamp/pull/70).
- **Causa:** verificar a contagem e depois inserir, e ler-mesclar-recifrar o blob, permitiam passar de 1.000 credenciais e perder alterações de dois `PATCH` paralelos. É o mesmo padrão do E-06, já conhecido na unidade anterior, e voltou na unidade seguinte.
- **Correção:** as escritas de cada usuário são serializadas pelo bloqueio de escrita do SQLite.
- **Prevenção:** dois testes de regressão que **falham sem o bloqueio** e passam com ele. A lição de processo é que um erro corrigido numa unidade deve virar item de checklist da próxima.

## E-08 · Avaliador dava nota máxima a `"a"` × 100

- **Detecção:** `/code-review` do [PR #74](https://github.com/GuidaGaita/bootcamp/pull/74) (achados 1 a 4).
- **Causa:** cada caractere repetido somava 1 bit sem teto, então `"a"` × 100 tinha 104 bits, nota 4 e "séculos" para quebrar, o oposto do propósito de RN-11. A spec dava a fórmula, mas não o teto, e os testes verificavam a fórmula, não a intenção. Também faltava dizer se "sequência" valia para a senha inteira, e as letras acentuadas eram tratadas como sem maiúsculas.
- **Correção:** repetições somam no máximo `distintos` bits; sequência vale para a senha inteira; senha vazia tem 0 bit; letras acentuadas contam como maiúsculas e minúsculas. Refinamento **R-027** e spec 004 v1.0.1.
- **Prevenção:** testes de intenção para entradas degeneradas, em `tests/unit/test_strength_estimator.py` (senha vazia, letras acentuadas, repetições).

## E-09 · Testes que não podiam falhar

- **Detecção:** leitura dos testes durante a revisão do [PR #70](https://github.com/GuidaGaita/bootcamp/pull/70) e antes da primeira execução da unidade 004.
- **Causa:** uma asserção `A or B` em que só `B` podia ser verdadeira, um teste de `PATCH` com UUID inválido que enviava o `PATCH` sem corpo e passava pelo motivo errado, e uma asserção `... or True`. Os testes eram escritos pelo mesmo agente que escreveu o código e compartilhavam suas suposições.
- **Correção:** testes reforçados; a asserção vacuamente verdadeira foi removida antes da primeira execução.
- **Prevenção:** para cada teste novo, conferir que ele falha quando o código está errado, e preferir testes de regressão que falham sem a correção (E-06 e E-07).
