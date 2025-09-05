# Lembrete Rápido

Uma extensão simples para Google Chrome que permite salvar e acessar rapidamente um lembrete diretamente do navegador.

## Funcionalidades

- Salve uma nota rápida para não esquecer tarefas importantes.
- Acesse e edite seu lembrete a qualquer momento pelo popup da extensão.
- Sincronização local usando o armazenamento do Chrome.
- Mensagem de status ao salvar o lembrete.
- Verificação periódica do lembrete em segundo plano.

## Instalação

1. Clone ou baixe este repositório em seu computador.
2. No Chrome, acesse `chrome://extensions/`.
3. Ative o **Modo de desenvolvedor** no canto superior direito.
4. Clique em **Carregar sem compactação** e selecione a pasta deste projeto.
5. A extensão aparecerá na barra de ferramentas do Chrome.

## Como usar

1. Clique no ícone da extensão "Lembrete Rápido" na barra do Chrome.
2. Digite seu lembrete na caixa de texto.
3. Clique em **Salvar** para guardar sua nota.
4. Sua nota ficará disponível sempre que abrir o popup da extensão.

## Estrutura do Projeto

```
bootcamp/
├── icons/
│   └── icon16.png, icon32.png, icon48.png, icon128.png
├── src/
│   ├── background/
│   │   └── service-worker.js
│   └── popup/
│       ├── popup.html
│       ├── popup.js
│       └── popup.css
├── manifest.json
└── README.md
```

## Permissões

- **storage**: Para salvar e recuperar o lembrete.
- **alarms**: Para executar verificações periódicas em segundo plano.

## Créditos

Desenvolvido para trabalho da faculdade.

## GitHub Pages

Este projeto possui uma página informativa publicada via [GitHub Pages](docs/index.md).  
Para visualizar, acesse a aba "Pages" nas configurações do repositório após o primeiro push.

---
