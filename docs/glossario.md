# Glossário

| Termo | Definição |
|-------|-----------|
| **AAD** (*Additional Authenticated Data*) | Dados que não são cifrados, mas entram na verificação de integridade do AES-GCM. No Cofre, vinculam cada texto cifrado ao seu usuário e registro, impedindo trocas entre linhas do banco. |
| **ADR** (*Architecture Decision Record*) | Registro curto de uma decisão arquitetural: contexto, decisão, alternativas e consequências. Ver [adr/](adr/README.md). |
| **AES-256-GCM** | Algoritmo de cifragem autenticada: garante confidencialidade e detecta qualquer alteração no texto cifrado. |
| **Argon2id** | Função de derivação de chave e hash de senhas resistente a ataques com GPU. Usada para verificar a senha mestra e derivar a KEK. |
| **Bloqueio de login** (*throttling*) | Suspensão temporária de tentativas de autenticação após falhas consecutivas para um mesmo e-mail (RN-14, RN-16). |
| **Caso de borda** (*edge case*) | Situação nos limites do comportamento esperado (valores mínimos e máximos, entradas vazias, estados inválidos). |
| **Cofre** | Nome do produto e também o conjunto de credenciais de um usuário. |
| **Constituição** | Documento do Spec Kit com os princípios inegociáveis do projeto (`.specify/memory/constitution.md`). |
| **Credencial** | Registro guardado pelo usuário: título, usuário, senha, URL e notas. |
| **Criptografia em envelope** | Técnica em que os dados são cifrados por uma chave de dados (DEK), e essa chave é cifrada por outra chave (KEK). |
| **DEK** (*Data Encryption Key*) | Chave aleatória de 256 bits, uma por usuário, que cifra as credenciais. |
| **DoD / DoR** | *Definition of Done* (critérios para considerar uma unidade concluída) e *Definition of Ready* (critérios para uma spec estar pronta para implementação). |
| **Fase A / Fase B** | Especificação e implementação de uma unidade; cada fase tem seu próprio PR. |
| **Harness de testes** | Infraestrutura que executa e apoia os testes: fixtures, relógio controlável, configuração de teste, marcadores e relatórios. |
| **HKDF** | Função de derivação de chave a partir de material de alta entropia. Deriva a chave de sessão a partir do token. |
| **IDOR** (*Insecure Direct Object Reference*) | Falha em que um usuário acessa um recurso alheio trocando o identificador na requisição. |
| **Incremento** | Etapa do roadmap que entrega valor verificável e corresponde a um milestone e a uma versão. |
| **KEK** (*Key Encryption Key*) | Chave derivada da senha mestra que cifra a DEK. Nunca é armazenada. |
| **MoSCoW** | Priorização em *Must*, *Should*, *Could* e *Won't*. |
| **NFKC** | Forma de normalização Unicode que unifica representações equivalentes de um mesmo texto (ex.: "é" pré-composto e "e" seguido de acento combinante). Aplicada à senha mestra (RN-02). |
| **Nonce** | Valor aleatório único por operação de cifragem. Nunca se repete para a mesma chave. |
| **Refinamento** | Alteração registrada na especificação motivada por testes, revisões ou implementação. |
| **SDD** (*Specification-Driven Development*) | Desenvolvimento em que a especificação é a fonte da verdade e o código deriva dela. |
| **Senha mestra** | Senha do usuário que protege o cofre. Nunca é armazenada e não pode ser recuperada. |
| **Sessão** | Período autenticado iniciado no login e identificado por um token opaco, com expiração. |
| **Spec** | Especificação de uma unidade (`specs/NNN-*/spec.md`): histórias, cenários de aceitação, requisitos e casos de borda. |
| **Spec Kit** | Kit do GitHub para SDD: CLI `specify`, templates e comandos/skills para agentes de IA. |
| **Token opaco** | Valor aleatório sem significado próprio, usado como credencial de sessão e validado consultando o servidor. |
| **Unidade** | Fatia vertical e independente do sistema, especificada por uma spec e entregue em um incremento. |
