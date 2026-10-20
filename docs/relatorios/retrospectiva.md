# Retrospectiva do projeto

Avaliação final do Cofre como experiência de **desenvolvimento com agente de IA no fluxo SDD** (Specification-Driven Development). Os números vêm do histórico do repositório em 2026-10-20; análises mais longas estão no [relatório técnico-ético](relatorio-etico-tecnico.md), no [relato de experiência](relato-de-experiencia.md) e em [ERROS.md](../ERROS.md).

## 1. Em números

| Medida | Valor |
|--------|------:|
| Período da implementação (primeiro commit a último PR de código) | 2026-09-13 a 2026-10-03 |
| Commits na `develop` / com coautoria do Claude | 88 / 70 |
| PRs mergeados (até o #81) | 22 |
| Linhas em `src/` / em `tests/` | 2.130 / 4.096 |
| Testes na suíte padrão / cobertura de linhas e ramificações | 420 / 98,83% |
| Specs / ADRs / refinamentos da especificação | 4 / 16 / 28 |
| Achados da revisão assistida por IA em 4 PRs de implementação | 38 |
| Erros lógicos documentados | 9 |

## 2. O que funcionou

- **Especificar antes de codar.** Com a spec e os casos de borda escritos, a implementação ficou quase mecânica: nas unidades de contas e do cofre, a primeira execução completa da suíte terminou sem exigir correção de código de produção (as 2 falhas da unidade do cofre eram defeitos dos próprios testes). Há mais código de teste (4.096 linhas) que de produção (2.130), e os casos de borda do catálogo viraram teste.
- **Contexto persistente para o agente.** O `CLAUDE.md` com as regras inegociáveis (sem spec aprovada não há código, testes antes do código, nada em `main` sem PR, regras de segurança) manteve o agente dentro do processo, e a constituição serviu de critério nas revisões.
- **Revisão em uma segunda passada.** O `/code-review` achou problemas graves com a suíte verde, como o bloqueio de login contornável por requisições paralelas e o avaliador que dava nota máxima a `"a"` repetido 100 vezes.
- **Rastreabilidade.** Cada mudança de rumo tem origem e motivo: 28 refinamentos, 16 ADRs, relatórios por incremento e o mapa requisito → testes gerado a cada execução.
- **Proteção de branches e CI obrigatório.** O CI pegou o que ninguém tinha visto, como a versão inexistente de uma ação, e limitou o raio de dano dos erros do agente.

## 3. Eficácia dos agentes de IA no fluxo SDD

O agente foi **eficaz como executor de uma especificação clara** e **pouco confiável como juiz do próprio trabalho**.

- Escreveu, em cerca de três semanas, uma API com criptografia em envelope, sessões, bloqueio de força bruta, cofre cifrado e gerador de senhas, com a documentação correspondente. O mantenedor decidia o problema, os requisitos, as decisões em aberto, a aprovação de cada spec e o merge de cada PR.
- Os erros mais caros não eram de sintaxe, e sim de suposição: um comportamento de biblioteca presumido, uma versão inventada, um teste que repetia a fórmula da spec em vez da intenção da regra. O mesmo padrão de corrida de dados voltou na unidade seguinte, mesmo já conhecido.
- Como o agente escrevia o código e os testes, os dois compartilhavam as mesmas suposições. O que reduziu o risco foi revisão independente e **testes de regressão que falham sem a correção**.

## 4. Ganho de produtividade

Não houve medição com e sem agente nem grupo de comparação, então este relatório **não** afirma um fator de ganho. O que o histórico mostra:

- Um mantenedor, sozinho, entregou em três semanas o que o roadmap dividia em cinco incrementos, com testes, documentação e CI.
- O ganho de **velocidade** foi grande. O ganho de **confiança** foi menor e custou revisão: de 38 achados, parte era de segurança.
- A produtividade depende de a spec estar certa. Cada refinamento (R-023 a R-028) mostra retrabalho evitável por uma especificação mais completa.

## 5. Dificuldades superadas

| Dificuldade | Como foi superada |
|-------------|-------------------|
| Trabalhar sozinho, sem revisão entre pares | Autorrevisão, `/code-review` publicado no PR com cada achado respondido, e leitura do diff pelo mantenedor ([ADR-0012](../adr/0012-revisao-de-codigo-em-projeto-individual.md)). Não equivale a uma revisão independente, e a limitação está registrada. |
| Corridas de concorrência (login, limite do cofre, `PATCH`) | Contagem atômica por `INSERT ... ON CONFLICT` e escritas serializadas por usuário; testes que falham sem a correção. |
| Segredos vazando em mensagens de erro | Regras de [docs/04 §5](../04-seguranca.md) viraram testes que procuram senhas, tokens e chaves nos logs e nas respostas. |
| Prazo e custo | Fluxo enxuto nas unidades 002 a 004 e corte do requisito *Could* (RF-16), com decisão registrada. |

## 6. Lições sobre governança

1. **Regras só valem se forem verificáveis.** O que ficou apenas escrito (como a exigência de `/security-review`) foi o que não foi cumprido. O que virou verificação automática (CI obrigatório, gate de cobertura, proteção de branch) foi cumprido sempre.
2. **Projeto individual precisa de um segundo olhar deliberado.** A revisão assistida por IA ajuda, mas tem ponto cego quando a mesma família de modelo escreve, testa e revisa.
3. **Registrar na hora.** Os erros, refinamentos e decisões ficaram mais fiéis quando anotados ao acontecer; o que foi reconstruído depois (por exemplo, o registro de erros com causa e prevenção) deu mais trabalho e perdeu detalhe.
4. **Revisão rápida vira carimbo.** Vários PRs foram mergeados minutos depois de abertos; o histórico do GitHub mostra isso, e a lição é separar, no tempo e no olhar, quem cria e quem revisa.
5. **Cortar escopo é uma decisão de projeto, não um fracasso**, desde que fique registrada: o RF-16 saiu do escopo com refinamento (R-028) e atualização de todos os documentos.

## 7. O que faria diferente

- Rodar o `/security-review` nas unidades de criptografia e autenticação desde o início.
- Gerar o registro de erros ao longo do desenvolvimento, e não no fim.
- Pedir ao agente, no começo de cada unidade, a lista de erros do incremento anterior como checklist (a corrida de concorrência se repetiu).
- Comparar de fato duas configurações ou ferramentas, para ter dados de produtividade em vez de impressões.
