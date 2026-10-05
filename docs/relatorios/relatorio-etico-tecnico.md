# Relatório técnico-ético: uso do Claude Code no desenvolvimento do Cofre

> **Escopo.** Avaliação crítica do uso de **um** agente de IA, o Claude Code (modelos Claude Opus 5.5 e Sonnet 5.5), no ciclo de vida do projeto Cofre. **Não houve comparação com outras ferramentas** (Codex CLI, Cursor, Antigravity): o projeto adotou o Claude como agente único ([ADR-0003](../adr/0003-claude-code-como-agente-unico.md)), e a comparação exigiria acesso às outras ferramentas e um experimento controlado, descrito na seção 7. Todos os casos abaixo vêm do histórico real do repositório e podem ser verificados nos PRs e nos relatórios citados.

## 1. Resumo em números

| Medida | Valor |
|--------|------:|
| Período (primeiro commit a esta data) | 2026-09-13 a 2026-10-03 |
| Commits no repositório / com coautoria do Claude (`Co-Authored-By`), à data da redação | 81 / 65 |
| PRs mergeados (documentação, especificação, implementação, release) | 16 |
| ADRs / refinamentos de especificação registrados | 16 / 27 |
| Testes automatizados na suíte padrão (unidades 001 a 004) | 420, todos aprovados, cobertura de 99% |
| Achados de revisão assistida por IA nos PRs de implementação | 38 (PR #63: 10, #69: 9, #70: 9, #74: 10) |
| Dos 38: corrigidos, mitigados ou esclarecidos na spec / mantidos com justificativa | 29 / 9 |
| Falhas que só o CI revelou (depois de a suíte local passar) | 2 |

Fontes: [relatório do incremento 1](2026-09-30-incremento-1.md), [do 2](2026-10-01-incremento-2.md), [do 3](2026-10-01-incremento-3.md), [do 4](2026-10-03-incremento-4.md) e o [registro de refinamentos](../registro-de-refinamentos.md).

## 2. Pilar 1: alucinação e código inseguro ou destrutivo

### 2.1 O que a IA errou

| Caso | O que aconteceu | Quem detectou | Gravidade |
|------|-----------------|---------------|-----------|
| **Versão inventada** | O workflow de CI usava `astral-sh/setup-uv@v10`, uma tag que não existe. A IA deduziu a tag a partir da release `v10.2.0` sem verificar. | O próprio CI, no primeiro push ([PR #63](https://github.com/GuidaGaita/bootcamp/pull/63)) | Média: bloqueou o merge, sem dano |
| **Comportamento de biblioteca presumido** | O gate de cobertura não era desligado em execuções parciais, porque o `pytest-cov` guarda um objeto de opções próprio. Depois, a primeira correção do vazamento de variáveis de ambiente nos testes (`model_validate`) também estava errada: o `pydantic-settings` lê o ambiente mesmo assim. | Testes de autoverificação do harness e teste vermelho | Baixa |
| **Código morto e escape corrompido** | Um *hook* que lia um atributo inexistente (`report.config`) e um caractere de controle ESC gravado literalmente no código-fonte. | Revisão do diff pela própria IA antes do commit | Baixa |
| **Segredo na mensagem de erro** | `COFRE_DATABASE_URL=postgresql://user:p@ss:w0rd@host/db` fazia a mensagem de configuração mostrar `w0rd@host`: um trecho da senha. A IA tinha escrito um teste para "nunca ecoar o valor", mas só cobria um tipo de erro. | `/code-review` ([PR #63](https://github.com/GuidaGaita/bootcamp/pull/63)) | **Alta** (RNF-04) |
| **Saúde verde com banco corrompido** | `GET /health` respondia 200 com o arquivo do banco corrompido: `SELECT 1` não lê o arquivo e o pool reaproveitava a conexão. | `/code-review` | Alta (FR-003) |
| **Bloqueio de força bruta contornável** | O contador de falhas de login era "ler, somar, gravar" em Python: 24 logins paralelos passavam do limite de 5 tentativas. | `/code-review` ([PR #69](https://github.com/GuidaGaita/bootcamp/pull/69)) | **Alta** (RN-14, RN-16) |
| **A mesma falha, de novo** | Na unidade seguinte, o limite do cofre (1.000 credenciais) e o `PATCH` tinham a mesma corrida de leitura-e-escrita, e dois `PATCH` paralelos perdiam uma alteração. A IA já conhecia o padrão da unidade anterior e repetiu o erro. | `/code-review` ([PR #70](https://github.com/GuidaGaita/bootcamp/pull/70)) | Alta |
| **Canal de tempo** | O hash fictício usado para igualar o tempo de login de e-mails inexistentes era calculado só no primeiro uso. | `/code-review` | Média (docs/04, ameaça A3) |
| **Regra errada que os testes confirmavam** | O avaliador de senhas dava a nota máxima a `"a" × 100`: cada repetição somava 1 bit sem teto. Os testes escritos junto com o código verificavam a fórmula da spec, não a intenção da regra (RN-11). | `/code-review` ([PR #74](https://github.com/GuidaGaita/bootcamp/pull/74)) | Média |
| **Entrada sem limite** | Senhas e e-mails sem tamanho máximo antes de rodar Argon2; tabela de tentativas que cresce sem limite com e-mails inexistentes; URL validada num formato e guardada em outro. | `/code-review` | Média |

### 2.2 Testes verdes não bastam

Nos quatro incrementos a suíte estava **verde** quando a revisão encontrou problemas graves. Os testes eram escritos pelo mesmo agente que escreveu o código, então compartilhavam as mesmas suposições. Houve também testes que não podiam falhar: uma asserção `A or B` em que só `B` podia ser verdadeira, e um teste de `PATCH` com UUID inválido que enviava o `PATCH` sem corpo e passava pelo motivo errado. A defesa que funcionou foi dupla: revisar o código com uma segunda passada independente e escrever testes de regressão que **falham sem a correção** (confirmado para a corrida do cofre).

### 2.3 Risco destrutivo

Nenhum dado foi perdido, e há três registros de controle:

- A camada de permissões **negou** dois comandos que a IA propôs: um `rm -rf reports` encadeado com a suíte e uma sequência PowerShell com `Remove-Item -Recurse -Force`. A IA reescreveu os dois sem apagar nada.
- Um `git add docs` incluiu, sem querer, arquivos que o mantenedor tinha mandado ignorar. Foi percebido ao conferir `git show --stat` e corrigido com `git commit --amend` **antes** do push.
- As regras do projeto (nunca commitar em `main` ou `develop`, sempre PR, proteção de branch com CI obrigatório) limitaram o raio de dano de qualquer erro.

## 3. Pilar 2: vazamento de dados, privacidade e confidencialidade

**Exposição de contexto ao modelo.** O agente lê arquivos do repositório e o conteúdo das conversas, e esse material é enviado ao provedor do modelo. No Cofre isso é aceitável porque o repositório é **público**, não há segredos versionados (`.env.example` só documenta variáveis) e os testes usam valores marcadores (`MARCADOR-SENHA-...`) em vez de senhas reais. Em um projeto privado ou com dados reais, a mesma prática exigiria decidir antes quais pastas o agente pode ler e usar um plano com garantias contratuais sobre retenção e treinamento.

**Dados pessoais.** O contexto da sessão inclui o e-mail do mantenedor, e a instrução do ambiente proíbe usá-lo fora de autoria e atribuição. O nome completo e o RA, exigidos no PDF da entrega, **não** foram colados nas sessões e não devem ser. Cada informação colada em um chat de terceiros deve ser tratada como publicada.

**O mesmo risco, no produto.** A IA foi usada para construir um gerenciador de senhas, onde vazamento é o risco central. Por isso as regras de [docs/04 §5](../04-seguranca.md) viraram testes: nenhuma senha ou token em logs, mensagens de erro ou `repr`; nenhum campo de credencial em claro no arquivo SQLite; mensagens de erro de configuração sem o valor recebido. O caso do trecho de senha na mensagem de erro (2.1) mostra que a regra existia e a primeira implementação ainda a violou.

**Experimento descartado.** Cogitou-se colar o contexto do projeto em chats web de outras ferramentas para comparação. O risco (enviar especificação e código a terceiros sem controle de retenção) foi um dos motivos de registrar a comparação como trabalho futuro.

## 4. Pilar 3: propriedade intelectual e direitos autorais

- **Autoria.** A legislação brasileira define autor como pessoa física (Lei 9.610/98, art. 11), e o enquadramento do código gerado por IA não está consolidado. O que sustenta a autoria humana neste projeto é o que a IA **não** decidiu sozinha: a escolha do problema, os requisitos e regras de negócio, as decisões registradas em ADRs, a aprovação de cada especificação e o merge de cada PR. Convém tratar essa parte como a contribuição criativa do mantenedor e o código gerado como produto de uma ferramenta.
- **Procedência.** Os commits trazem `Co-Authored-By`, o que torna visível, em 60 dos 72 commits, quais mudanças tiveram a IA como coautora. É uma boa prática de transparência e deve acompanhar o código.
- **Risco de código derivado.** Modelos podem reproduzir trechos de código licenciado. O código aqui usa padrões comuns (FastAPI, SQLAlchemy, `cryptography`, `argon2-cffi`) e **não** foi verificado contra bases de código aberto: não foi usada nenhuma ferramenta de detecção de similaridade. É um risco residual, não medido.
- **Licenças.** As dependências são de código aberto (por exemplo, FastAPI e `argon2-cffi` sob licenças permissivas) e os créditos do README citam o Spec Kit e as skills de `grill-me` (MIT). **Lacuna encontrada na redação deste relatório: o repositório não tinha arquivo de licença própria**, o que deixaria o código em "todos os direitos reservados" por padrão. O mantenedor escolheu a **licença MIT**, e o arquivo [LICENSE](../../LICENSE) foi adicionado em 2026-10-03. A MIT é permissiva e compatível com as licenças das dependências e dos modelos de fluxo citados.
- **Termos do provedor.** Os termos de uso do Claude definem a quem pertencem as saídas e o que acontece com os dados enviados. Eles mudam e dependem do plano contratado; devem ser conferidos pelo mantenedor na data de uso e citados na entrega.

## 5. Pilar 4: a centralidade da revisão humana no fluxo SDD

O fluxo SDD usado separa **o que construir** (decisão humana) de **como construir** (execução da IA), com portões em que só uma pessoa pode passar:

| Portão | Quem decide | Exemplo real |
|--------|-------------|--------------|
| Escolha do problema e dos requisitos | Mantenedor | RF-01 a RF-16, sessão `grill-me` |
| Decisões em aberto | Mantenedor | 409 no cadastro, endpoints públicos, 30 min de sessão e 5 falhas (confirmadas em 2026-09-30) |
| Aprovação da especificação | Mantenedor (merge do PR de spec) | PRs #7, #66 e #71 |
| Merge da implementação | Mantenedor (a proteção de branch exige PR e CI verde) | PRs #63, #69, #70 e #74 |
| Decisões de processo | Mantenedor | cortar `/speckit-*`, uma issue por unidade e adiar o `/security-review` para economizar tokens |

Três observações críticas:

1. **O ciclo de re-especificação funcionou.** 27 refinamentos foram registrados; vários nasceram de falhas reveladas por testes ou revisão (R-023 a R-027), e a regra "spec primeiro" impediu que a correção ficasse só no código.
2. **A revisão da IA tem ponto cego.** O mesmo agente escreveu código, testes e (em instâncias separadas) a revisão. A segunda passada encontrou muito, mas também repetiu a mesma classe de erro entre unidades, e uma revisão da mesma família de modelo tende a ter os mesmos pontos cegos que o gerador. Falta, neste projeto, um revisor humano que leia o diff com atenção a concorrência e criptografia.
3. **A economia de revisão tem custo.** Por decisão do mantenedor, o `/security-review`, exigido pelo `CLAUDE.md` para criptografia e autenticação, **não foi executado** nas unidades 002 e 003, e as especificações das unidades 002 a 004 foram escritas sem `/speckit-clarify` e `/speckit-analyze` (a revisão da 004 achou uma ambiguidade de spec que esse passo talvez tivesse antecipado). Isso está registrado nos PRs, mas é uma redução deliberada de garantia. O registro mostra aprovação por merge; o quanto do diff foi lido por uma pessoa não é medido aqui, e o mantenedor deve declarar isso na entrega.

## 6. Conclusões e recomendações

1. Use a IA para executar uma especificação já decidida, não para decidir. Os melhores resultados vieram de requisitos, contratos e casos de borda escritos **antes** do código.
2. Trate "suíte verde" como condição necessária, não suficiente. Exija ao menos uma revisão independente de código e testes de regressão que falhem sem a correção.
3. Verifique tudo que a IA afirma sobre o mundo externo (versões, tags, APIs). O custo de uma versão inventada foi um CI vermelho; em outro contexto seria uma dependência maliciosa.
4. Quando um erro é corrigido, **registre a classe do erro**, não só a instância: o padrão de concorrência reapareceu na unidade seguinte.
5. Defina, antes de começar, o que o agente pode ler e enviar, a licença do código e quais portões de revisão não podem ser cortados por economia.

## 7. Limites deste relatório e trabalho futuro

- **Uma ferramenta e uma pessoa.** Não há comparação entre ferramentas, e os resultados dependem de um mantenedor, de um modelo e de um projeto.
- **Casos selecionados pelo agente.** A lista de erros foi montada pelo registro do repositório; erros não detectados não aparecem.
- **Comparativo futuro.** Um experimento controlado exige a mesma tarefa, o mesmo ponto de partida sem histórico e as mesmas métricas (testes, `ruff`, aderência à especificação, alucinações, intervenções humanas, tempo e custo), executado por quem tem acesso às outras ferramentas.
- **Verificação jurídica.** As observações sobre autoria e termos de uso não substituem consulta a um profissional nem a leitura dos termos vigentes.
