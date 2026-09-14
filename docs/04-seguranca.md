# 04 — Segurança e Modelo de Ameaças

> **Status:** Aprovado · **Versão:** 1.0.0 · **Última revisão:** 2026-09-13
> Este documento é **normativo**: specs, planos e código não podem contradizê-lo sem antes alterá-lo (com ADR, quando a mudança for arquitetural).

## 1. Ativos protegidos

| Ativo | Sensibilidade | Onde existe |
|-------|---------------|-------------|
| Dados das credenciais (senha, usuário, URL, título, notas) | Crítica | Cifrados no banco; em claro apenas em memória durante a requisição e na resposta de RF-11. |
| Senha mestra | Crítica | Apenas em memória, durante cadastro, login, alteração de senha e exclusão de conta. Nunca persistida. |
| DEK (chave de dados do usuário) | Crítica | Cifrada no banco (pela KEK e pela chave de sessão); em claro apenas em memória. |
| Token de sessão | Alta | Com o cliente; no servidor apenas o hash SHA-256. |
| E-mail do usuário | Média | Em claro no banco (necessário para login). |

## 2. Modelo de ameaças

| ID | Ameaça | Cenário | Mitigação | Requisitos |
|----|--------|---------|-----------|------------|
| A1 | Vazamento do banco | Atacante obtém cópia do arquivo SQLite. | Todos os campos de credencial cifrados; DEK só pode ser liberada com a senha mestra (via Argon2id, caro para força bruta offline) ou com um token de sessão válido, que não está no banco. | RNF-01, RNF-02, RNF-06 |
| A2 | Força bruta online | Tentativas repetidas de login. | Bloqueio após 5 falhas por 15 min; custo do Argon2id por tentativa. | RNF-07, RN-14 |
| A3 | Enumeração de contas pelo login | Descobrir e-mails cadastrados pela resposta ou pelo tempo do login. | Mensagem genérica; quando o e-mail não existe, executa-se uma verificação Argon2id contra um hash fictício para igualar o tempo de resposta. | RN-04 |
| A4 | Acesso indevido (IDOR) | Usuário troca o ID da credencial na URL. | Toda consulta filtra por `user_id` da sessão; recurso alheio retorna 404; a AAD da cifragem inclui o `user_id`. | RNF-03 |
| A5 | Roubo de token | Token interceptado ou vazado no cliente. | Expiração absoluta de 30 min; logout; revogação de todas as sessões ao alterar a senha mestra; TLS no proxy reverso. | RNF-06, RN-05 |
| A6 | Adulteração de dados cifrados | Alterar ou trocar `ciphertext` entre linhas do banco. | AES-GCM (cifragem autenticada) com AAD vinculada ao usuário e ao ID da credencial: qualquer troca ou alteração falha na decifragem. | RNF-01 |
| A7 | Vazamento por logs ou erros | Stack trace ou payload registrado em log. | Handler de erro genérico; logs nunca incluem corpo de requisição/resposta nem cabeçalho `Authorization`; teste automatizado captura logs e procura segredos. | RNF-04 |
| A8 | Aleatoriedade previsível | Uso de `random` para tokens ou senhas. | Uso exclusivo de `secrets`/`os.urandom`; regra `S311` do `ruff` habilitada. | RNF-05 |
| A9 | Cache de respostas sensíveis | Proxy ou navegador armazena resposta com senha. | `Cache-Control: no-store` em todo `/api/v1`. | RNF-04 |
| A10 | Dependência vulnerável | CVE em biblioteca usada. | Dependências travadas em `uv.lock`; auditoria com `pip-audit` no CI (*Could*). | — |

## 3. Arquitetura criptográfica

O Cofre usa **criptografia em envelope** ([ADR-0008](adr/0008-criptografia-em-envelope.md)) e **sessões com token opaco** ([ADR-0009](adr/0009-sessoes-com-token-opaco.md)).

```mermaid
flowchart TB
  MP["Senha mestra<br/>(somente em memória)"]
  MP -- "Argon2id (salt próprio do hash)" --> PH["password_hash<br/>tabela users"]
  MP -- "Argon2id + kdf_salt" --> KEK["KEK 256 bits<br/>(nunca armazenada)"]
  DEK["DEK 256 bits aleatórios<br/>(uma por usuário)"]
  KEK -- "AES-256-GCM" --> WD["wrapped_dek<br/>tabela users"]
  DEK -.-> WD
  TK["Token de sessão 256 bits<br/>(somente com o cliente)"]
  TK -- "SHA-256" --> TH["token_hash<br/>tabela sessions"]
  TK -- "HKDF-SHA256" --> SK["Chave de sessão<br/>(nunca armazenada)"]
  SK -- "AES-256-GCM" --> SWD["session_wrapped_dek<br/>tabela sessions"]
  DEK -.-> SWD
  DEK -- "AES-256-GCM + AAD" --> CT["ciphertext das credenciais<br/>tabela credentials"]
```

### 3.1 Algoritmos e parâmetros

| Uso | Algoritmo | Parâmetros | Biblioteca |
|-----|-----------|------------|------------|
| Hash da senha mestra (verificação) | Argon2id | m = 19.456 KiB, t = 2, p = 1, salt 16 bytes, saída 32 bytes (mínimo OWASP) | `argon2-cffi` (`PasswordHasher`) |
| Derivação da KEK | Argon2id (raw) | mesmos custos, **salt independente** (`kdf_salt`, 16 bytes), saída 32 bytes | `argon2-cffi` (`hash_secret_raw`) |
| Cifragem de credenciais e embrulho de chaves | AES-256-GCM | nonce 12 bytes aleatório **por operação**, tag 16 bytes | `cryptography` (`AESGCM`) |
| Token de sessão | CSPRNG | 32 bytes, codificado em base64url | `secrets.token_urlsafe(32)` |
| Localização da sessão | SHA-256 | sobre o token | `hashlib` |
| Chave de sessão | HKDF-SHA256 | `info = b"cofre/session-key/v1"`, 32 bytes | `cryptography` |
| Comparações de segredos | tempo constante | — | `hmac.compare_digest` |

### 3.2 Dados autenticados adicionais (AAD)

| Objeto cifrado | AAD |
|----------------|-----|
| Credencial | `cofre:credential:v{enc_version}:{user_id}:{credential_id}` |
| DEK embrulhada pela KEK | `cofre:dek:v1:{user_id}` |
| DEK embrulhada pela chave de sessão | `cofre:session-dek:v1:{session_id}` |

O texto claro de uma credencial é o JSON UTF-8 `{"title", "username", "password", "url", "notes"}`. O campo `enc_version` permite evoluir o formato sem migrar tudo de uma vez.

## 4. Ciclo de vida das chaves

| Evento | O que acontece |
|--------|----------------|
| **Cadastro** (RF-02) | Valida RN-01/RN-02 → gera `password_hash` → gera `kdf_salt` → deriva KEK → gera DEK aleatória → `wrapped_dek = AES-GCM(KEK, DEK)` → persiste. KEK e DEK descartadas. |
| **Login** (RF-03) | Verifica bloqueio → verifica hash (ou hash fictício, se o e-mail não existe) → em falha incrementa contador → em sucesso zera contador, deriva KEK, decifra DEK, gera token, deriva chave de sessão, persiste `token_hash` + `session_wrapped_dek` + `expires_at`, remove sessões expiradas do usuário. |
| **Requisição autenticada** | Localiza sessão por `SHA-256(token)` → rejeita se expirada → deriva chave de sessão → decifra DEK → usa DEK apenas durante a requisição. |
| **Logout** (RF-04) | Remove a linha da sessão; o token deixa de funcionar imediatamente. |
| **Alteração de senha mestra** (RF-06) | Verifica senha atual → valida RN-02 para a nova → novo `password_hash` → novo `kdf_salt` → nova KEK → **re-embrulha a mesma DEK** → remove **todas** as sessões. As credenciais não são recifradas. |
| **Exclusão de conta** (RF-07) | Verifica senha mestra → remove usuário, sessões e credenciais em cascata. |

## 5. Regras obrigatórias de implementação

1. **Nunca** usar o módulo `random` para qualquer valor de segurança.
2. **Nunca** registrar em log: corpo de requisição/resposta, cabeçalho `Authorization`, senha, senha mestra, token, KEK, DEK, `ciphertext`.
3. **Nunca** incluir segredos em mensagens de exceção ou em `repr` de objetos (usar `SecretStr` do Pydantic para campos sensíveis).
4. Toda consulta a sessões e credenciais **filtra por `user_id`** na camada de repositório.
5. Nonces **nunca** se repetem para a mesma chave: sempre gerar 12 bytes novos por cifragem.
6. Parâmetros do Argon2id vêm da configuração. A aplicação **recusa iniciar** com valores abaixo do mínimo OWASP, exceto quando `COFRE_ENV=test`, que permite parâmetros reduzidos para acelerar a suíte.
7. Não implementar primitivas criptográficas próprias: usar apenas `cryptography` e `argon2-cffi`.
8. Mudanças neste documento exigem PR próprio e, se alterarem algoritmos ou o fluxo de chaves, um ADR.

## 6. Riscos aceitos

| Risco | Justificativa |
|-------|---------------|
| O servidor decifra os dados; um servidor **em execução** comprometido pode observar senha mestra e DEK em memória. Não é *zero-knowledge*. | Criptografia no cliente exigiria um cliente próprio, fora do escopo ([01-visao-geral.md](01-visao-geral.md#52-fora-do-escopo)). |
| O cadastro revela se um e-mail já está registrado (409). | Trade-off de usabilidade aceito; o login permanece sem enumeração. |
| Um atacante pode provocar bloqueio temporário (15 min) da conta de outra pessoa. | Preferível a permitir força bruta; o impacto é limitado e temporário. |
| A aplicação não termina TLS. | Responsabilidade do proxy reverso em uma implantação real. |
| Python não garante apagar segredos da memória (strings são imutáveis). | Limitação da linguagem; mitigada pela vida curta dos objetos. |
