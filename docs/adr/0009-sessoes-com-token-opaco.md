# ADR-0009 — Sessões com token opaco em vez de JWT

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** Claude Code, por delegação de @GuidaGaita
- **Relacionados:** [04-seguranca.md](../04-seguranca.md#4-ciclo-de-vida-das-chaves), RNF-06, RN-05, RF-03, RF-04, RF-06

## Contexto

Pelo [ADR-0008](0008-criptografia-em-envelope.md), a DEK só pode ser liberada com a senha mestra, que o usuário informa **apenas no login**. Mesmo assim, toda requisição autenticada precisa da DEK. Além disso, logout e troca de senha mestra precisam **revogar sessões imediatamente**.

## Decisão

Usar **sessões armazenadas no servidor, identificadas por um token opaco**:

1. No login, gera-se um **token** de 256 bits (`secrets.token_urlsafe(32)`), que é devolvido ao cliente.
2. O banco guarda, na tabela `sessions`:
   - `token_hash = SHA-256(token)`, usado para localizar a sessão;
   - `session_wrapped_dek = AES-256-GCM(HKDF-SHA256(token), DEK)`;
   - `expires_at`, com expiração absoluta de 30 min por padrão.
3. Em cada requisição, a sessão é localizada pelo hash, a chave de sessão é derivada do token e a DEK é decifrada.
4. O logout remove a sessão. A troca de senha mestra remove **todas** as sessões do usuário.

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| JWT sem estado | Revogação exige lista de bloqueio, o que elimina a vantagem de não ter estado. Transportar a DEK no token exigiria JWE com uma chave do servidor, e o vazamento dessa chave junto com os tokens exporia os cofres. |
| DEK em cache na memória do servidor | Perdida a cada reinício; não funciona com múltiplos *workers*. |
| Exigir a senha mestra em toda requisição | Péssima usabilidade e custo de Argon2id por requisição. |

## Consequências

**Positivas**

- Revogação imediata e simples.
- Um vazamento do banco não revela nem tokens nem DEKs de sessão, porque ambos exigem o token, que só o cliente tem.
- Sessões sobrevivem a reinícios do servidor.

**Negativas / riscos**

- Uma consulta ao banco por requisição autenticada (custo baixo no SQLite local).
- Sessões expiradas se acumulam e precisam de limpeza, feita de forma oportunista no login.
- Quem obtiver um token válido acessa o cofre até a expiração. Mitigações: TTL curto, logout e TLS no proxy.
