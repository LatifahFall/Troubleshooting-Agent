// SCRIPT SIMPLIFIÉ POUR TROUBLESHOOTING AGENT

// Variables globales
var currentPath = 'C:/Users/latif/OneDrive/Desktop';
var selectedPath = '';
var logsInterval = null;
var chatMessages = [];
var waitingForResponse = false;
var firstDiagnosticShown = false;
var currentTab = 'setup';

// Charger répertoire initial
window.onload = function() {
    loadDirectory(currentPath);
};

// Charger un répertoire
function loadDirectory(path) {
    fetch('/browse?path=' + encodeURIComponent(path))
        .then(response => response.json())
        .then(data => {
            currentPath = data.current_path.replace(/\\/g, '/');
            document.getElementById('currentPath').textContent = currentPath;
            
            var html = '';
            data.directories.forEach(dir => {
                html += '<div class="file-item directory" onclick="loadDirectory(\'' + 
                        currentPath + '/' + dir + '\')">' + dir + '/</div>';
            });
            data.files.forEach(file => {
                html += '<div class="file-item file">' + file + '</div>';
            });
            
            document.getElementById('fileBrowser').innerHTML = html;
        })
        .catch(error => {
            console.error('Erreur:', error);
            document.getElementById('fileBrowser').innerHTML = 'Erreur de chargement';
        });
}

// Naviguer vers le dossier parent
function goUp() {
    var lastSlash = Math.max(currentPath.lastIndexOf('/'), currentPath.lastIndexOf('\\'));
    if (lastSlash > 0) {
        var parentPath = currentPath.substring(0, lastSlash);
        loadDirectory(parentPath);
    }
}

// Actualiser le navigateur
function refreshBrowser() {
    loadDirectory(currentPath);
}

// Sélectionner le dossier courant
function selectCurrentFolder() {
    selectedPath = currentPath;
    document.getElementById('selectedPath').textContent = selectedPath;
    document.getElementById('status').style.display = 'none';
}

// Démarrer le diagnostic
function startDiagnostic() {
    if (!selectedPath) {
        alert('Veuillez sélectionner un dossier');
        return;
    }
    
    // Nettoyer le chat pour un nouveau diagnostic
    chatMessages = [];
    document.getElementById('chatMessages').innerHTML = 'Diagnostic en cours...';
    document.getElementById('chatInput').disabled = true;
    document.getElementById('sendBtn').disabled = true;
    waitingForResponse = false;
    firstDiagnosticShown = false;
    
    var startBtn = document.getElementById('startBtn');
    startBtn.disabled = true;
    startBtn.textContent = 'Diagnostic en cours...';
    
    document.getElementById('logs').textContent = 'Demarrage du diagnostic...';
    
    fetch('/start-diagnostic', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({app_path: selectedPath})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Erreur: ' + data.error);
            resetDiagnosticButton();
            return;
        }
        
        // Démarrer la récupération des logs
        if (logsInterval) clearInterval(logsInterval);
        updateLogs();
        logsInterval = setInterval(updateLogs, 2000);
    })
    .catch(error => {
        console.error('Erreur:', error);
        alert('Erreur lors du demarrage: ' + error.message);
        resetDiagnosticButton();
    });
}

// Mettre à jour les logs
function updateLogs() {
    fetch('/logs')
        .then(response => response.json())
        .then(data => {
            var logsDiv = document.getElementById('logs');
            
            // Vérifier les nouvelles questions dans le chat
            checkForChatMessages(data.logs);
            
            logsDiv.innerHTML = data.logs.join('<br>');
            logsDiv.scrollTop = logsDiv.scrollHeight;
            
            if (!data.running) {
                resetDiagnosticButton();
                if (logsInterval) {
                    clearInterval(logsInterval);
                    logsInterval = null;
                }
            }
        })
        .catch(error => {
            console.error('Erreur logs:', error);
        });
}

// Réinitialiser le bouton
function resetDiagnosticButton() {
    var startBtn = document.getElementById('startBtn');
    startBtn.disabled = false;
    startBtn.textContent = 'Lancer le diagnostic';
}

// FONCTIONS CHAT SIMPLIFIÉES

// Ajouter message au chat
function addChatMessage(sender, message) {
    var chatContainer = document.getElementById('chatMessages');
    var messageDiv = document.createElement('div');
    messageDiv.className = sender === 'agent' ? 'agent-message' : 'user-message';
    
    if (sender === 'agent') {
        // Pour l'agent, rendre le HTML directement
        messageDiv.innerHTML = '<strong>Agent:</strong><br>' + message;
    } else {
        // Pour l'utilisateur, texte simple
        messageDiv.innerHTML = '<strong>Vous:</strong> ' + message;
    }
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Détecter questions dans les logs
function checkForChatMessages(logs) {
    for (var i = 0; i < logs.length; i++) {
        var log = logs[i];
        
        // Chercher CHAT_QUESTION: pour extraire le contenu
        if (log.includes('CHAT_QUESTION:') && !waitingForResponse) {
            // Extraire tout le contenu après CHAT_QUESTION:
            var questionStart = log.indexOf('CHAT_QUESTION:') + 'CHAT_QUESTION:'.length;
            var messageContent = log.substring(questionStart).trim();
            
            // Continuer à récupérer les lignes suivantes jusqu'à ce qu'on trouve ATTENTE REPONSE WEB
            for (var j = i + 1; j < logs.length; j++) {
                var nextLog = logs[j];
                
                // Arrêter si on arrive à ATTENTE REPONSE WEB
                if (nextLog.includes('ATTENTE REPONSE WEB')) {
                    break;
                }
                
                // Nettoyer la ligne (enlever timestamp) et ajouter au contenu
                var cleanLine = nextLog.replace(/^\[\d{2}:\d{2}:\d{2}\]\s*/, '').trim();
                if (cleanLine && !cleanLine.includes('**********')) {
                    messageContent += '\n' + cleanLine;
                }
            }
            
            // Vérifier si c'est un nouveau message (pas déjà affiché)
            var isNewMessage = true;
            for (var k = 0; k < chatMessages.length; k++) {
                if (chatMessages[k].message === messageContent) {
                    isNewMessage = false;
                    break;
                }
            }
            
            // Afficher seulement si c'est un nouveau message
            if (messageContent && isNewMessage) {
                chatMessages.push({sender: 'agent', message: messageContent});
                addChatMessage('agent', messageContent);
                enableChatInput();
                notifyChatMessage(); // Notification glow
            }
        }
        
        // Chercher les messages finaux (done_for_now ou messages directs)
        if (log.includes('done_for_now') && log.includes('message')) {
            try {
                var jsonMatch = log.match(/\{.*\}/);
                if (jsonMatch) {
                    var parsed = JSON.parse(jsonMatch[0]);
                    if (parsed.action && parsed.action.parameters && parsed.action.parameters.message) {
                        var finalMessage = parsed.action.parameters.message;
                        var found = false;
                        for (var j = 0; j < chatMessages.length; j++) {
                            if (chatMessages[j].message === finalMessage) {
                                found = true;
                                break;
                            }
                        }
                        if (!found) {
                            chatMessages.push({sender: 'agent', message: finalMessage});
                            addChatMessage('agent', finalMessage);
                            notifyChatMessage(); // Notification glow
                        }
                    }
                }
            } catch (e) {
                // Ignore JSON parsing errors
            }
        }
        
    }
    
    // Après avoir traité tous les logs, vérifier si le diagnostic est terminé
    var diagnosticEnded = false;
    for (var i = 0; i < logs.length; i++) {
        if (logs[i].includes('ANALYSIS COMPLETE') || logs[i].includes('diagnostic_running = False')) {
            diagnosticEnded = true;
            break;
        }
    }
    
    // Si le diagnostic est terminé, chercher le dernier message significatif
    if (diagnosticEnded) {
        var lastMessage = '';
        // Parcourir les logs en sens inverse pour trouver le dernier message de l'agent
        for (var i = logs.length - 1; i >= 0; i--) {
            var log = logs[i];
            if (!log.includes('ATTENTE REPONSE WEB') && 
                !log.includes('ANALYSIS COMPLETE') && 
                !log.includes('diagnostic_running') &&
                !log.includes('**********') &&
                !log.includes('Diagnostic terminé') && // Ignorer les messages du serveur
                !log.includes('CHAT:') && // Ignorer les logs du chat
                !log.includes('STDERR:') && // Ignorer les erreurs
                !log.includes('Session saved') && // Ignorer les messages de sauvegarde
                !log.includes('---') && // Ignorer les lignes de séparation
                !log.includes('Processus') && // Ignorer les messages de processus
                !log.includes('Iteration')) { // Ignorer les messages d'itération
                
                var cleanLine = log.replace(/^\[\d{2}:\d{2}:\d{2}\]\s*/, '').trim();
                if (cleanLine && cleanLine.length > 10 && !cleanLine.startsWith('REPONSE RECUE')) {
                    lastMessage = cleanLine;
                    break;
                }
            }
        }
        
        // Afficher le dernier message s'il n'est pas déjà dans le chat
        if (lastMessage) {
            var found = false;
            for (var k = 0; k < chatMessages.length; k++) {
                if (chatMessages[k].message === lastMessage) {
                    found = true;
                    break;
                }
            }
            if (!found) {
                chatMessages.push({sender: 'agent', message: lastMessage});
                addChatMessage('agent', lastMessage);
                notifyChatMessage(); // Notification glow
            }
        }
    }
}

// Activer input chat
function enableChatInput() {
    waitingForResponse = true;
    document.getElementById('chatInput').disabled = false;
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('chatInput').focus();
}

// Envoyer message chat
function sendChatMessage() {
    var input = document.getElementById('chatInput');
    var message = input.value.trim();
    
    if (message === '') return;
    
    addChatMessage('user', message);
    
    console.log('Envoi de la réponse:', message); // Debug
    
    fetch('/chat-response', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: message})
    })
    .then(response => response.json())
    .then(data => {
        console.log('Réponse du serveur:', data); // Debug
        input.value = '';
        document.getElementById('chatInput').disabled = true;
        document.getElementById('sendBtn').disabled = true;
        waitingForResponse = false;
    })
    .catch(error => {
        console.error('Erreur envoi:', error);
        alert('Erreur lors de l\'envoi de la réponse!');
    });
}

// ===== GESTION DES ONGLETS =====

// Changer d'onglet
function switchTab(tabName) {
    // Retirer l'active de tous les onglets
    var allTabs = document.querySelectorAll('.tab-btn');
    var allPanes = document.querySelectorAll('.tab-pane');
    
    allTabs.forEach(function(tab) {
        tab.classList.remove('active');
    });
    
    allPanes.forEach(function(pane) {
        pane.classList.remove('active');
    });
    
    // Activer l'onglet sélectionné
    document.getElementById('tab-' + tabName).classList.add('active');
    document.getElementById('pane-' + tabName).classList.add('active');
    
    // Mettre à jour la variable globale
    currentTab = tabName;
    
    // Si on va sur Chat, retirer le glow et reset les notifications
    if (tabName === 'chat') {
        document.getElementById('tab-chat').classList.remove('glow');
    }
    
    console.log('Switched to tab:', tabName);
}

// Nouvelle fonction pour lancer diagnostic ET basculer sur Chat
function startDiagnosticAndSwitchToChat() {
    if (!selectedPath) {
        alert('Veuillez sélectionner un dossier');
        return;
    }
    
    // Lancer le diagnostic (fonction existante)
    startDiagnostic();
    
    // Basculer automatiquement sur l'onglet Chat
    switchTab('chat');
}

// Fonction pour notifier un nouveau message dans le chat
function notifyChatMessage() {
    // Si on n'est pas sur l'onglet chat, ajouter le glow
    if (currentTab !== 'chat') {
        document.getElementById('tab-chat').classList.add('glow');
    }
}

// TEST CHAT (à supprimer plus tard)
function testChat() {
    addChatMessage('agent', 'Test: Avez-vous besoin d\'aide ?');
    enableChatInput();
    notifyChatMessage(); // Test de la notification
}
