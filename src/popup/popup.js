const noteArea = document.getElementById('note-area');
const saveButton = document.getElementById('save-button');
const statusMessage = document.getElementById('status-message');

// Carrega a nota salva quando o popup abre
document.addEventListener('DOMContentLoaded', () => {
  // Pede ao Chrome para buscar o valor salvo com a chave 'quickNote'
  chrome.storage.local.get(['quickNote'], (result) => {
    if (result.quickNote) {
      noteArea.value = result.quickNote;
    }
  });
});

// Salva a nota quando o botão é clicado
saveButton.addEventListener('click', () => {
  const noteText = noteArea.value;
  // Pede ao Chrome para salvar o texto com a chave 'quickNote'
  chrome.storage.local.set({ quickNote: noteText }, () => {
    statusMessage.textContent = 'Lembrete salvo!';
    // Limpa a mensagem de status após 2 segundos
    setTimeout(() => {
      statusMessage.textContent = '';
    }, 2000);
  });
});