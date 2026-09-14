# ADR-0005 — API REST multiusuário sem frontend

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** Claude Code, por delegação de @GuidaGaita
- **Relacionados:** [01-visao-geral.md](../01-visao-geral.md), [03-arquitetura.md](../03-arquitetura.md), [Sessão grill-me Q5](../sessoes/2026-09-13-grill-me-definicao-inicial.md)

## Contexto

O sistema deve permitir que **usuários** gerenciem suas credenciais com segurança e se manter **simples**. A entrega valoriza componentes e APIs isolados, contratos de entrada e saída explícitos e empacotamento em Docker. O mantenedor delegou a escolha do formato do produto.

## Decisão

O Cofre será uma **API REST multiusuário**, somente backend:

- contas com e-mail e senha mestra, cada uma com seu cofre isolado;
- contratos publicados em OpenAPI, com a **Swagger UI** (`/docs`) como interface de uso no MVP;
- **nenhum frontend** no MVP. Clientes web, CLI ou mobile ficam como evolução futura.

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| CLI local com um usuário e arquivo cifrado | A mais simples e naturalmente *zero-knowledge*, mas atende apenas um usuário por máquina, tem contratos pouco expressivos e torna o Docker artificial. |
| API REST + frontend web | Praticamente dobra o escopo (UI, estado, testes de interface) sem reforçar os objetivos de SDD. |
| Aplicação desktop ou TUI | Empacotamento e testes mais difíceis; sem ganho para os objetivos. |

## Consequências

**Positivas**

- Cada endpoint é uma unidade testável com contrato explícito.
- `docker compose` e o CI fazem sentido naturalmente.
- Base pronta para qualquer cliente futuro.

**Negativas / riscos**

- O servidor processa dados em claro durante as requisições, o que impede um modelo *zero-knowledge* (risco aceito em [04-seguranca.md](../04-seguranca.md#6-riscos-aceitos)).
- Autenticação e sessões entram no escopo ([ADR-0009](0009-sessoes-com-token-opaco.md)).
