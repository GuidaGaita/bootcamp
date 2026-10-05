# Relato de experiência

## 1. Contexto

Projeto individual do Bootcamp III: o **Cofre**, uma API REST multiusuário de gerenciamento de senhas (Python 3.13, FastAPI, SQLite), desenvolvida com **Specification-Driven Development** (GitHub Spec Kit) e o Claude Code como agente. Embora o enunciado fale em desenvolvimento em grupo, o trabalho foi **individual**: um mantenedor ([@GuidaGaita](https://github.com/GuidaGaita)) e um agente de IA. A "revisão entre pares" foi substituída por autorrevisão, revisão assistida por IA publicada em cada PR e merge pelo mantenedor ([ADR-0012](../adr/0012-revisao-de-codigo-em-projeto-individual.md)).

## 2. O que foi feito, em ordem

| Etapa | Entrega | Referência |
|-------|---------|------------|
| Incremento 0 | Documentação, ADRs, constituição, templates e proteção de branches | PRs #1, #3, #6; `v0.1.0`, `v0.1.1` |
| Incremento 1 | Fundação: `/health`, erros padronizados, configuração, logs, harness de testes, Docker e CI | PRs #7, #63, #64, #65; `v0.2.0` |
| Incremento 2 | Contas e sessões: cadastro, login com bloqueio, token, troca de senha, exclusão | PRs #66, #69 |
| Incremento 3 | Cofre de credenciais cifradas, com busca e teste de desempenho | PR #70 |
| Incremento 4 | Gerador e avaliador de senhas | PRs #71, #74 |
| Fechamento | Relatórios, licença MIT, README final, ADRs consolidados e release `v1.0.0` | PRs #72, #75, #76, #77 e #78 |

## 3. Desafios

- **A especificação precisa estar certa antes do código.** Vários refinamentos (R-023 a R-027) nasceram de falhas que testes ou revisão revelaram, como a ordem de tarefas que exigia um cabeçalho antes de existir quem o implementasse.
- **Confiar, mas verificar.** O agente produziu uma versão de ação de CI que não existe, mensagens de erro que vazavam parte de uma senha e uma corrida de concorrência que se repetiu em duas unidades. Todas foram achadas por revisão ou CI, não pelos testes que o próprio agente escreveu (detalhes no [relatório técnico-ético](relatorio-etico-tecnico.md)).
- **Trabalhar sozinho com revisão assistida.** Sem colegas, a revisão ficou concentrada em mim e na IA. Tive que tomar cuidado extra para identificar quais etapas eram relevantes e para conseguir revisar com uma mente diferente da que desenvolveu, sempre consultando os documentos e os checklists da entrega.
- **Prazo e custo.** Para entregar tudo no prazo, o fluxo foi simplificado (sem algumas skills do Spec Kit e sem o `/security-review`). Considero que a troca faz sentido, dada a pouca mão de obra disponível em um projeto individual.

## 4. Aprendizados

Observados no histórico do projeto:

1. Especificar primeiro, com casos de borda, tornou a implementação quase mecânica: nas unidades 002 e 003 a suíte passou na primeira execução completa.
2. O ganho de velocidade com o agente foi grande, mas o ganho de **confiança** exigiu revisão independente e testes de regressão que falham sem a correção.
3. Registrar decisões (ADRs e refinamentos) deu rastreabilidade: cada mudança de rumo tem motivo e origem.

Essas práticas já estão interligadas à minha jornada de trabalho, mas é muito bom ver que a IA traz cada vez mais recursos de criação e empodera a nós, programadores.

## 5. O que faria diferente

Diminuiria o escopo da entrega.
