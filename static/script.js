// Variables globales
var currentPath = "C:/Users/latif/OneDrive/Desktop";
var selectedPath = null;
var logsInterval = null;

// Charger au démarrage
window.onload = function() {
    loadDirectory(currentPath);
};

// Navigation dans les dossiers
function loadDirectory(path) {
    console.log('Chargement du dossier:', path);
    
    fetch('/browse?path=' + encodeURIComponent(path))
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.error) {
                alert('Erreur: ' + data.error);
                return;
            }
            
            currentPath = data.current_path;
            document.getElementById('currentPath').textContent = currentPath;
            
            var browser = document.getElementById('fileBrowser');
            browser.innerHTML = '';
            
            // Ajouter les dossiers
            for (var i = 0; i < data.directories.length; i++) {
                var dir = data.directories[i];
                var item = document.createElement('div');
                item.className = 'dir-item';
                item.textContent = '[DIR] ' + dir;
                item.setAttribute('data-dir', dir);
                item.onclick = function() {
                    var separator = currentPath.endsWith('/') ? '' : '/';
                    var newPath = currentPath + separator + this.getAttribute('data-dir');
                    loadDirectory(newPath);
                };
                browser.appendChild(item);
            }
            
            // Ajouter les fichiers
            for (var j = 0; j < data.files.length; j++) {
                var file = data.files[j];
                var item = document.createElement('div');
                item.className = 'file-item';
                item.textContent = '[FILE] ' + file;
                browser.appendChild(item);
            }
            
            // Si vide
            if (data.directories.length === 0 && data.files.length === 0) {
                browser.innerHTML = '<p style="color: #666;">Dossier vide</p>';
            }
        })
        .catch(function(error) {
            console.error('Erreur:', error);
            alert('Erreur de navigation: ' + error.message);
        });
}

// Remonter d'un niveau
function goUp() {
    console.log('Remontee depuis:', currentPath);
    
    var lastSlash = Math.max(currentPath.lastIndexOf('/'), currentPath.lastIndexOf('\\\\'));
    if (lastSlash > 0) {
        var parentPath = currentPath.substring(0, lastSlash);
        console.log('Nouveau chemin:', parentPath);
        loadDirectory(parentPath);
    } else {
        alert('Deja a la racine du systeme');
    }
}

// Actualiser le navigateur
function refreshBrowser() {
    loadDirectory(currentPath);
}

// Sélectionner le dossier actuel
function selectCurrentFolder() {
    selectedPath = currentPath;
    document.getElementById('selectedPath').textContent = selectedPath;
    // Cacher le status
    document.getElementById('status').style.display = 'none';
}

// Démarrer le diagnostic
function startDiagnostic() {
    if (!selectedPath) {
        alert('Veuillez selectionner un dossier avant de lancer le diagnostic');
        return;
    }
    
    var startBtn = document.getElementById('startBtn');
    startBtn.disabled = true;
    startBtn.textContent = 'Diagnostic en cours...';
    
    document.getElementById('logs').textContent = 'Demarrage du diagnostic...';
    
    fetch('/start-diagnostic', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({app_path: selectedPath})
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.error) {
            alert('Erreur: ' + data.error);
            resetDiagnosticButton();
            return;
        }
        
        // Démarrer la récupération des logs
        if (logsInterval) {
            clearInterval(logsInterval);
        }
        
        // Appeler updateLogs immédiatement puis toutes les 2 secondes
        updateLogs();
        logsInterval = setInterval(updateLogs, 2000);
    })
    .catch(function(error) {
        console.error('Erreur:', error);
        alert('Erreur lors du demarrage: ' + error.message);
        resetDiagnosticButton();
    });
}

// Mettre à jour les logs
function updateLogs() {
    fetch('/logs')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            var logsDiv = document.getElementById('logs');
            // Vérifier s'il y a de nouveaux messages de chat
            checkForChatMessages(data.logs);
            
            logsDiv.innerHTML = data.logs.join('<br>');
            
            // Auto-scroll vers le bas
            logsDiv.scrollTop = logsDiv.scrollHeight;
            
            // Si le diagnostic est terminé
            if (!data.running) {
                resetDiagnosticButton();
                if (logsInterval) {
                    clearInterval(logsInterval);
                    logsInterval = null;
                }
            }
        })
        .catch(function(error) {
            console.error('Erreur lors de la récupération des logs:', error);
        });
}

// Réinitialiser le bouton de diagnostic
function resetDiagnosticButton() {
    var startBtn = document.getElementById('startBtn');
    startBtn.disabled = false;
    startBtn.textContent = 'Lancer le diagnostic';
}

// ===== FONCTIONS CHAT =====

// Variables globales pour le chat
let chatMessages = [];
let waitingForResponse = false;
let lastDetectedQuestion = null;

// Ajouter un message au chat
function addChatMessage(sender, message) {
    chatMessages.push({sender: sender, message: message, timestamp: new Date()});
    
    const chatContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = sender === 'agent' ? 'agent-message' : 'user-message';
    
    const timestamp = new Date().toLocaleTimeString();
    messageDiv.innerHTML = `<strong>${sender === 'agent' ? 'Agent' : 'Vous'}:</strong> ${message} <small>(${timestamp})</small>`;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Ne pas activer automatiquement ici, c'est géré dans checkForChatMessages
}

// Activer l'input du chat
function enableChatInput() {
    console.log('ENABLING CHAT INPUT'); // Debug
    waitingForResponse = true;
    document.getElementById('chatInput').disabled = false;
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('chatInput').focus();
    console.log('Chat input enabled, waiting for response:', waitingForResponse); // Debug
}

// FONCTION DE TEST DU CHAT
function testChat() {
    alert('Test chat clicked!'); 
    
    alert('Step 1 - About to check chatMessages');
    
    const chatContainer = document.getElementById('chatMessages');
    
    alert('Step 2 - Found chatMessages: ' + (chatContainer ? 'YES' : 'NO'));
    
    if (chatContainer) {
        chatContainer.innerHTML = '<div class="agent-message"><strong>Agent:</strong> Test message direct</div>';
        alert('Step 3 - Content added to chat area');
    } else {
        alert('ERROR: chatMessages not found!');
    }
}

// Désactiver l'input du chat
function disableChatInput() {
    waitingForResponse = false;
    document.getElementById('chatInput').disabled = true;
    document.getElementById('sendBtn').disabled = true;
    document.getElementById('chatInput').value = '';
}

// Envoyer un message dans le chat
function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (message === '') return;
    
    // Ajouter le message de l'utilisateur
    addChatMessage('user', message);
    
    // Envoyer au backend
    fetch('/chat-response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({message: message})
    })
    .then(response => response.json())
    .then(data => {
        console.log('Réponse envoyée au backend:', data);
        disableChatInput();
    })
    .catch(error => {
        console.error('Erreur envoi réponse:', error);
        addChatMessage('system', 'Erreur lors de l\'envoi de la réponse');
    });
}

// Permettre l'envoi avec Enter
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }
});

// Fonction pour vérifier les nouveaux messages du chat (à appeler depuis updateLogs)
function checkForChatMessages(logs) {
    console.log('=== CHECKING CHAT MESSAGES ==='); // Debug
    console.log('Number of logs:', logs.length); // Debug
    
    for (let i = 0; i < logs.length; i++) {
        const log = logs[i];
        console.log(`Log ${i}:`, log); // Debug
        
        // Chercher CHAT_QUESTION:
        if (log.includes('CHAT_QUESTION:')) {
            console.log('FOUND CHAT_QUESTION!'); // Debug
            const questionMatch = log.match(/CHAT_QUESTION:\s*(.+)/);
            if (questionMatch && questionMatch[1]) {
                const question = questionMatch[1].trim();
                console.log('Extracted question:', question); // Debug
                
                // Ajouter au chat si pas déjà présent
                if (!chatMessages.find(msg => msg.message === question)) {
                    console.log('Adding question to chat'); // Debug
                    addChatMessage('agent', question);
                    enableChatInput(); // Activer immédiatement
                } else {
                    console.log('Question already in chat'); // Debug
                }
            }
        }
        
        // Chercher ATTENTE REPONSE WEB:
        if (log.includes('ATTENTE REPONSE WEB:')) {
            console.log('FOUND ATTENTE REPONSE WEB!'); // Debug
            if (!waitingForResponse) {
                console.log('Enabling chat input'); // Debug
                enableChatInput();
            }
        }
        // Ancien pattern pour compatibilité
        else if (log.includes('AskForClarification') || log.includes('ProvideFurtherAssistance')) {
            // Extraire la question si possible
            try {
                const parsed = JSON.parse(log.substring(log.indexOf('{')));
                if (parsed.action && parsed.action.parameters && parsed.action.parameters.question) {
                    if (!chatMessages.find(msg => msg.message === parsed.action.parameters.question)) {
                        addChatMessage('agent', parsed.action.parameters.question);
                    }
                }
            } catch (e) {
                // Si on ne peut pas parser, chercher des patterns simples
                if (log.includes('?')) {
                    const questionMatch = log.match(/[^{]*\?[^}]*/);
                    if (questionMatch) {
                        const question = questionMatch[0].trim();
                        if (!chatMessages.find(msg => msg.message === question)) {
                            addChatMessage('agent', question);
                        }
                    }
                }
            }
        }
    }
}
