# ADR-0008 — Criptografia em envelope com Argon2id e AES-256-GCM

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** Claude Code, por delegação de @GuidaGaita
- **Relacionados:** [04-seguranca.md](../04-seguranca.md), RNF-01, RNF-02, RN-03, RF-06

## Contexto

Credenciais precisam continuar protegidas mesmo que o banco vaze (ameaça A1). O usuário deve poder trocar a senha mestra sem perder dados e sem recifrar todo o cofre. O servidor precisa decifrar as credenciais durante as requisições autenticadas ([ADR-0005](0005-api-rest-multiusuario-sem-frontend.md)).

## Decisão

Adotar **criptografia em envelope**, com uma chave de dados por usuário:

1. No cadastro, gera-se uma **DEK** aleatória de 256 bits.
2. Da senha mestra deriva-se a **KEK** com **Argon2id** (salt próprio `kdf_salt`, parâmetros mínimos OWASP: m = 19 MiB, t = 2, p = 1).
3. Armazena-se apenas `wrapped_dek = AES-256-GCM(KEK, DEK)`. KEK e DEK nunca são persistidas em claro.
4. Cada credencial é cifrada com a DEK usando **AES-256-GCM**, com nonce aleatório por operação e **AAD** vinculando o texto cifrado ao `user_id` e ao `credential_id`.
5. A verificação de login usa um **hash Argon2id separado**, com salt diferente do usado na derivação da KEK.
6. Na troca de senha mestra, deriva-se uma nova KEK e apenas a DEK é **re-embrulhada**; as credenciais não mudam.

Detalhes de parâmetros e AAD estão em [04-seguranca.md §3](../04-seguranca.md#3-arquitetura-criptográfica).

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| Uma chave única do servidor (variável de ambiente) | Se banco e ambiente vazarem juntos, todos os cofres ficam expostos, e quem administra o servidor lê tudo. |
| Cifrar as credenciais diretamente com a chave derivada da senha mestra | Trocar a senha mestra exigiria recifrar todas as credenciais. |
| Criptografia no cliente (*zero-knowledge*) | Exige um cliente próprio, fora do escopo. |
| Fernet (AES-CBC + HMAC) | Seguro, mas não oferece AAD para vincular o texto cifrado ao registro. |

## Consequências

**Positivas**

- Um vazamento do banco, sozinho, não expõe credenciais; a força bruta offline fica cara por causa do Argon2id.
- A troca de senha mestra custa uma única operação.
- A AAD detecta adulteração e troca de textos cifrados entre linhas.

**Negativas / riscos**

- **Senha mestra esquecida significa dados irrecuperáveis** (RN-03).
- O servidor em execução tem acesso aos dados em claro durante as requisições.
- Cada cadastro, login ou troca de senha custa o tempo do Argon2id (RNF-12).
