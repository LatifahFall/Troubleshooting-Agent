// Variables globales
var currentPath = 'C:/Users';
var selectedPath = '';
var logsInterval = null;
var chatMessages = [];
var waitingForResponse = false;
var firstDiagnosticShown = false;
var currentTab = 'setup';

// Charger répertoire initial
window.onload = function() {
    loadDirectory(currentPath);
    loadAppsForFilter();
    typewriterEffect('TETRA', 'tetraTitle');
    initMatrixRain();
};

// =========== MATRIX RAIN EFFECT =========== 
// 
function initMatrixRain() {
    var canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '-3';
    canvas.style.opacity = '0.08';
    document.body.appendChild(canvas);
    
    var ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    var matrix = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789@#$%^&*()*&^%+-/~{[|`]}";
    matrix = matrix.split("");
    
    var font_size = 20;
    var columns = canvas.width / font_size;
    
    var drops = [];
    for (var x = 0; x < columns; x++) {
        drops[x] = 1;
    }
    
    function draw() {
        ctx.fillStyle = 'rgba(10, 10, 10, 0.15)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#2563eb';
        ctx.font = font_size + 'px monospace';
        
        for (var i = 0; i < drops.length; i++) {
            var text = matrix[Math.floor(Math.random() * matrix.length)];
            ctx.fillText(text, i * font_size, drops[i] * font_size);
            
            if (drops[i] * font_size > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }
            drops[i]++;
        }
    }
    
    setInterval(draw, 40);
    
    window.addEventListener('resize', function() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        columns = canvas.width / font_size;
        drops = [];
        for (var x = 0; x < columns; x++) {
            drops[x] = 1;
        }
    });
}

// =========== TYPEWRITER EFFECT =========== 
function typewriterEffect(text, elementId) {
    var element = document.getElementById(elementId);
    element.innerHTML = '';
    var i = 0;
    var speed = 200; // vitesse de frappe en ms
    
    function typeChar() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(typeChar, speed);
        }
    }
    
    // Petit délai avant de commencer
    setTimeout(typeChar, 800);
}

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

// Fonction supprimée - maintenant dans la section HISTORIQUE

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
        var chatTab = document.getElementById('tab-chat');
        chatTab.classList.add('glow');
        // Son désactivé pour un environnement professionnel
        // playNotificationSound();
        setTimeout(function() {
            chatTab.classList.remove('glow');
        }, 3000);
    }
}

// =========== CYBER SOUND EFFECTS =========== 
function playNotificationSound() {
    // Créer un son synthétique de notification cyber
    try {
        var audioContext = new (window.AudioContext || window.webkitAudioContext)();
        var oscillator = audioContext.createOscillator();
        var gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(1200, audioContext.currentTime + 0.1);
        oscillator.frequency.exponentialRampToValueAtTime(600, audioContext.currentTime + 0.2);
        
        gainNode.gain.setValueAtTime(0, audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(0.1, audioContext.currentTime + 0.01);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.2);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.2);
    } catch (e) {
        // Ignore si l'audio n'est pas supporté
    }
}

// ===== GESTION DE L'HISTORIQUE =====

// Charger les applications pour le filtre
function loadAppsForFilter() {
    fetch('/apps')
        .then(response => response.json())
        .then(data => {
            var select = document.getElementById('appFilter');
            
            // Vider le select
            select.innerHTML = '<option value="">Toutes les applications</option>';
            
            // Ajouter les applications
            if (data.apps) {
                data.apps.forEach(function(app) {
                    var option = document.createElement('option');
                    option.value = app;
                    option.textContent = app;
                    select.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Erreur chargement apps:', error);
        });
}

// Charger l'historique des diagnostics
function loadHistory() {
    var appFilter = document.getElementById('appFilter').value;
    var url = '/history';
    
    if (appFilter) {
        url += '?app_name=' + encodeURIComponent(appFilter);
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            displayHistory(data.history || []);
        })
        .catch(error => {
            console.error('Erreur chargement historique:', error);
            document.getElementById('historyList').innerHTML = 
                '<div class="history-empty">Erreur lors du chargement de l\'historique</div>';
        });
}

// Afficher l'historique
function displayHistory(history) {
    var container = document.getElementById('historyList');
    
    if (history.length === 0) {
        container.innerHTML = '<div class="history-empty">Aucun diagnostic trouvé</div>';
        return;
    }
    
    var html = '';
    history.forEach(function(item) {
        var statusClass = item.has_final_response ? 'completed' : 'partial';
        var statusText = item.has_final_response ? 'Complet' : 'Partiel';
        
        html += '<div class="history-item" onclick="viewHistoryDetails(\'' + item.id + '\')">';
        html += '  <div class="history-header">';
        html += '    <span class="history-app-name">' + item.app_name + '</span>';
        html += '    <div>';
        html += '      <span class="history-date">' + item.started_at + '</span>';
        html += '      <span class="history-status ' + statusClass + '">' + statusText + '</span>';
        html += '    </div>';
        html += '  </div>';
        html += '</div>';
    });
    
    container.innerHTML = html;
}

// Voir les détails d'un diagnostic
function viewHistoryDetails(sessionId) {
    console.log('Viewing details for session:', sessionId);
    openDiagnosticModal(sessionId);
}

// Ouvrir la modal avec les détails du diagnostic
function openDiagnosticModal(sessionId) {
    var modal = document.getElementById('diagnosticModal');
    var modalBody = document.getElementById('modalBody');
    var modalTitle = document.getElementById('modalTitle');
    
    // Afficher la modal
    modal.style.display = 'block';
    
    // Réinitialiser le contenu
    modalBody.innerHTML = '<div class="loading">Chargement des détails...</div>';
    modalTitle.textContent = 'Détails du diagnostic';
    
    // Charger les détails
    fetch('/history/' + sessionId)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                modalBody.innerHTML = '<div class="error-message">Erreur: ' + data.error + '</div>';
                return;
            }
            
            displayDiagnosticDetails(data.details);
        })
        .catch(error => {
            console.error('Erreur chargement détails:', error);
            modalBody.innerHTML = '<div class="error-message">Erreur lors du chargement des détails</div>';
        });
}

// Afficher les détails du diagnostic dans la modal
function displayDiagnosticDetails(details) {
    var modalBody = document.getElementById('modalBody');
    var modalTitle = document.getElementById('modalTitle');
    
    // Mettre à jour le titre
    modalTitle.textContent = 'Rapport - ' + details.app_name;
    
    var html = '<div class="report-content">';
    
    // En-tête du rapport
    html += '<div class="report-header">';
    html += '  <h1>Rapport de Troubleshooting</h1>';
    html += '  <div class="meta">';
    html += '    <strong>Application:</strong> ' + details.app_name + '<br>';
    html += '    <strong>Date:</strong> ' + details.started_at + '<br>';
    html += '    <strong>Session:</strong> ' + details.id;
    html += '  </div>';
    html += '</div>';
    
    // Contenu du diagnostic (le rapport principal)
    if (details.diagnostic_message) {
        html += '<div class="report-section">';
        html += '  <h3 class="report-section-title">Analyse et Diagnostic</h3>';
        html += '  <div class="report-section-content">';
        html += '    ' + details.diagnostic_message;
        html += '  </div>';
        html += '</div>';
    }
    
    // Message final si présent
    if (details.final_response && details.final_response.message) {
        html += '<div class="report-section">';
        html += '  <h3 class="report-section-title">Conclusion</h3>';
        html += '  <div class="report-section-content">';
        html += '    ' + details.final_response.message;
        html += '  </div>';
        html += '</div>';
    }
    
    // Pied de page
    html += '<div class="report-footer">';
    html += '  Rapport généré automatiquement par l\'Agent de Troubleshooting<br>';
    html += '  Session ID: ' + details.id;
    html += '</div>';
    
    html += '</div>';
    
    modalBody.innerHTML = html;
}

// Fermer la modal
function closeDiagnosticModal() {
    var modal = document.getElementById('diagnosticModal');
    modal.style.display = 'none';
}

// Fermer la modal en cliquant à l'extérieur
window.onclick = function(event) {
    var modal = document.getElementById('diagnosticModal');
    if (event.target === modal) {
        closeDiagnosticModal();
    }
}

// Charger l'historique quand on arrive sur l'onglet
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
    
    // Si on va sur History, charger les données
    if (tabName === 'history') {
        loadHistory();
    }
    
    console.log('Switched to tab:', tabName);
}
