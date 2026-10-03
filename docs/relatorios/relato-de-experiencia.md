# Relato de experiência

> **Rascunho para o mantenedor.** Os fatos abaixo vêm do histórico do repositório. As seções marcadas com **[escrever]** pedem a sua voz: o que você sentiu, aprendeu e mudaria. Elas não podem ser escritas pelo agente, porque o relato é sobre a **sua** experiência. Apague este aviso antes de entregar.

## 1. Contexto

Projeto individual do Bootcamp III: o **Cofre**, uma API REST multiusuário de gerenciamento de senhas (Python 3.13, FastAPI, SQLite), desenvolvida com **Specification-Driven Development** (GitHub Spec Kit) e o Claude Code como agente. Embora o enunciado fale em desenvolvimento em grupo, o trabalho foi **individual**: um mantenedor ([@GuidaGaita](https://github.com/GuidaGaita)) e um agente de IA. A "revisão entre pares" foi substituída por autorrevisão, revisão assistida por IA publicada em cada PR e merge pelo mantenedor ([ADR-0012](../adr/0012-revisao-de-codigo-em-projeto-individual.md)).

## 2. O que foi feito, em ordem

| Etapa | Entrega | Referência |
|-------|---------|------------|
| Incremento 0 | Documentação, ADRs, constituição, templates e proteção de branches | PRs #1, #3, #6; `v0.1.0`, `v0.1.1` |
| Incremento 1 | Fundação: `/health`, erros padronizados, configuração, logs, harness de testes, Docker e CI | PRs #7, #63, #64, #65; `v0.2.0` |
| Incremento 2 | Contas e sessões: cadastro, login com bloqueio, token, troca de senha, exclusão | PRs #66, #69 |
| Incremento 3 | Cofre de credenciais cifradas, com busca e teste de desempenho | PR #70 |
| Incremento 4 | Gerador e avaliador de senhas | PR #71 (spec) |

## 3. Desafios

- **A especificação precisa estar certa antes do código.** Vários refinamentos (R-023 a R-026) nasceram de falhas que testes ou revisão revelaram, como a ordem de tarefas que exigia um cabeçalho antes de existir quem o implementasse.
- **Confiar, mas verificar.** O agente produziu uma versão de ação de CI que não existe, mensagens de erro que vazavam parte de uma senha e uma corrida de concorrência que se repetiu em duas unidades. Todas foram achadas por revisão ou CI, não pelos testes que o próprio agente escreveu (detalhes no [relatório técnico-ético](relatorio-etico-tecnico.md)).
- **Trabalhar sozinho com revisão assistida.** Sem colegas, a revisão ficou concentrada em você e na IA. **[escrever]** Como foi decidir o que revisar com atenção e o que aceitar?
- **Prazo e custo.** Para entregar tudo no prazo, o fluxo foi simplificado (sem algumas skills do Spec Kit e sem o `/security-review`). **[escrever]** O que você sacrificou e como avalia essa troca?

## 4. Aprendizados

Observados no histórico, para você confirmar ou corrigir:

1. Especificar primeiro, com casos de borda, tornou a implementação quase mecânica: nas unidades 002 e 003 a suíte passou na primeira execução completa.
2. O ganho de velocidade com o agente foi grande, mas o ganho de **confiança** exigiu revisão independente e testes de regressão que falham sem a correção.
3. Registrar decisões (ADRs e refinamentos) deu rastreabilidade: cada mudança de rumo tem motivo e origem.

**[escrever]** Aprendizados pessoais: o que mudou na sua forma de programar, de testar, de especificar e de usar IA?

## 5. O que faria diferente

**[escrever]** Por exemplo: pedir revisão humana de um colega nas partes de criptografia, definir a licença do código no início, ou medir tempo e custo desde o começo.
