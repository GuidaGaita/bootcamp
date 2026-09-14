# 01 — Visão Geral e Definição do Problema

> **Status:** Aprovado · **Versão:** 1.0.0 · **Última revisão:** 2026-09-13
> Documento de nível de projeto. As specs por unidade (`specs/NNN-*/spec.md`) derivam daqui e de [02-requisitos.md](02-requisitos.md).

## 1. O problema

Pessoas acumulam dezenas de contas online e, sem uma ferramenta adequada, acabam:

- **reutilizando a mesma senha** em vários serviços, de modo que um único vazamento compromete todas as contas;
- **escolhendo senhas fracas e previsíveis**, fáceis de memorizar e fáceis de quebrar;
- **guardando senhas em lugares inseguros**, como planilhas, blocos de notas, e-mails para si mesmas ou papéis.

Falta um lugar **único, confiável e cifrado** onde cada pessoa guarde suas credenciais e as consulte quando precisar, sem que o próprio sistema (ou quem obtiver uma cópia do banco de dados) consiga lê-las.

## 2. A proposta: Cofre

**Cofre** é uma **API REST multiusuário** de gerenciamento de senhas. Cada usuário tem um **cofre pessoal** protegido por uma **senha mestra**:

- as credenciais (título, usuário, senha, URL, notas) são **cifradas em repouso** com uma chave que só pode ser liberada com a senha mestra do dono;
- o sistema **gera senhas fortes** e **avalia a força** de senhas existentes;
- toda a interação acontece por uma API documentada (OpenAPI/Swagger), pensada para ser consumida por qualquer cliente futuro (web, CLI, mobile).

## 3. Objetivos

| ID | Objetivo |
|----|----------|
| O1 | Permitir que cada usuário armazene, consulte, edite e remova suas credenciais com segurança. |
| O2 | Garantir que um vazamento do banco de dados, sozinho, **não** exponha nenhuma senha ou dado de credencial. |
| O3 | Incentivar senhas fortes e únicas com gerador e avaliador de força. |
| O4 | Demonstrar um processo de engenharia guiado por especificação (SDD), com rastreabilidade entre requisitos, specs, testes e código. |
| O5 | Manter o sistema **simples**: uma aplicação, um banco, um comando para subir. |

## 4. Partes interessadas

| Parte interessada | Interesse |
|-------------------|-----------|
| **Usuário final** | Guardar e recuperar credenciais com segurança. Interage via cliente HTTP ou Swagger UI. |
| **Desenvolvedor de cliente** (futuro) | Contratos de API estáveis, bem documentados e com erros previsíveis. |
| **Mantenedor** (@GuidaGaita) | Especificações claras, testes confiáveis e ambiente reprodutível para evoluir o sistema com apoio do Claude Code. |
| **Avaliação do bootcamp** | Evidências de SDD, governança, uso de agentes de IA e testes. |

## 5. Escopo

### 5.1 Dentro do escopo (MVP)

- Cadastro de conta, login e logout com sessão de tempo limitado.
- Alteração da senha mestra sem perda de dados; exclusão de conta.
- CRUD de credenciais cifradas, com listagem paginada e busca.
- Gerador de senhas configurável e avaliador de força.
- Relatório de saúde do cofre (senhas fracas e reutilizadas) — prioridade *Could*.
- API documentada via OpenAPI, ambiente em Docker, suíte de testes automatizados.

### 5.2 Fora do escopo

| Item | Motivo |
|------|--------|
| Interface gráfica (web/desktop/mobile) | Mantém o escopo enxuto; a Swagger UI cobre a interação no MVP. |
| Criptografia no cliente (*zero-knowledge* real) | Exige um cliente próprio; ver riscos aceitos em [04-seguranca.md](04-seguranca.md). |
| Recuperação de senha mestra | Incompatível com o modelo de chaves: sem a senha mestra os dados são irrecuperáveis (RN-03). |
| Compartilhamento de credenciais entre usuários | Complexidade criptográfica alta para o objetivo do projeto. |
| 2FA/TOTP, verificação de vazamentos (HIBP), importação/exportação, extensão de navegador | Evoluções futuras possíveis. |
| TLS/HTTPS dentro da aplicação | Responsabilidade de um proxy reverso na implantação. |
| Alta disponibilidade / múltiplas instâncias | SQLite e instância única são suficientes para o objetivo. |

## 6. Premissas e restrições

- **Projeto individual**, desenvolvido com apoio do **Claude Code** como único agente de IA ([ADR-0003](adr/0003-claude-code-como-agente-unico.md)).
- **Processo SDD com GitHub Spec Kit** ([ADR-0004](adr/0004-sdd-com-github-spec-kit.md)).
- **Python 3.13 + FastAPI** ([ADR-0006](adr/0006-python-fastapi-uv.md)); persistência em **SQLite** ([ADR-0007](adr/0007-sqlite-com-sqlalchemy.md)).
- Desenvolvimento **incremental e sem datas fixas**: o avanço é medido por incrementos concluídos ([09-roadmap.md](09-roadmap.md)).
- Documentação em **português (pt-BR)**; identificadores de código em inglês ([ADR-0002](adr/0002-idioma-da-documentacao-e-do-codigo.md)).

## 7. Critérios de sucesso do produto

| ID | Critério | Como verificar |
|----|----------|----------------|
| CS-01 | 100% dos requisitos *Must* implementados. | Matriz de rastreabilidade em [02-requisitos.md](02-requisitos.md) sem lacunas. |
| CS-02 | Nenhum dado de credencial ou senha mestra em texto claro no banco. | Teste automatizado de segurança que inspeciona o arquivo SQLite. |
| CS-03 | Cobertura de testes ≥ 85% das linhas do pacote `cofre`. | Gate de cobertura no CI. |
| CS-04 | Ambiente sobe com um único comando. | `docker compose up` em máquina limpa. |
| CS-05 | Todo comportamento implementado tem origem em uma spec aprovada. | Revisão de PR + marcadores `req` nos testes. |
