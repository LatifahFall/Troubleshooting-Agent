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
