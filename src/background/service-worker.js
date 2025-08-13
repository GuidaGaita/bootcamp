// Este evento é disparado uma única vez: quando a extensão é instalada ou atualizada.
chrome.runtime.onInstalled.addListener(() => {
  // Uma boa prática é imprimir uma mensagem no console para saber que tudo começou bem.
  console.log('Extensão "Lembrete Rápido" foi instalada.');

  // Aqui, definimos um valor inicial no storage para dar as boas-vindas ao usuário.
  // Isso evita que a caixa de texto comece vazia na primeira vez.
  chrome.storage.local.set({ quickNote: 'Bem-vindo! Escreva seu primeiro lembrete aqui.' });
});

// --- Exemplo de uma tarefa em segundo plano usando a API de Alarmes ---

// Primeiro, criamos um alarme chamado 'checkNote' que vai disparar a cada 30 segundos.
chrome.alarms.create('checkNote', {
  periodInMinutes: 0.5
});

// Agora, dizemos ao Chrome o que fazer quando o alarme 'checkNote' disparar.
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'checkNote') {
    // A cada 5 minutos, este código vai rodar em segundo plano.
    // Ele pega a nota salva e a exibe no console de background da extensão.
    chrome.storage.local.get(['quickNote'], (result) => {
      console.log('Verificação periódica (a cada 30 seg). Nota atual:', result.quickNote || 'Nenhuma nota definida.');
    });
  }
});