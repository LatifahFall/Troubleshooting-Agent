from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import os

app = FastAPI(title="Troubleshooting Agent")

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Troubleshooting Agent</title>
        <meta charset="utf-8">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 1000px; 
                margin: 20px auto; 
                padding: 20px; 
            }
            .container {
                display: grid;
                grid-template-columns: 350px 1fr;
                gap: 20px;
            }
            .sidebar {
                border-right: 1px solid #ccc;
                padding-right: 20px;
            }
            .main-content {
                text-align: center;
            }
            button {
                background-color: #007bff; 
                color: white; 
                border: none; 
                padding: 10px 15px; 
                margin: 5px;
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 14px;
                width: 100%;
            }
            button:hover { background-color: #0056b3; }
            button.secondary { background-color: #6c757d; }
            button.secondary:hover { background-color: #545b62; }
            
            .current-path {
                background-color: #e9ecef;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                font-family: monospace;
                font-size: 12px;
                word-break: break-all;
            }
            
            .file-browser {
                background-color: #f8f9fa;
                border: 1px solid #ccc;
                padding: 10px;
                border-radius: 5px;
                height: 400px;
                overflow-y: auto;
            }
            
            .dir-item, .file-item {
                padding: 8px;
                margin: 2px 0;
                cursor: pointer;
                border-radius: 3px;
                border: 1px solid transparent;
            }
            .dir-item:hover, .file-item:hover {
                background-color: #e9ecef;
            }
            .dir-item {
                font-weight: bold;
                color: #007bff;
            }
            .selected {
                background-color: #007bff;
                color: white;
            }
            
            .result {
                margin: 20px 0;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <h1>Troubleshooting Agent - Version 2</h1>
        
        <div class="container">
            <!-- Sidebar avec explorateur -->
            <div class="sidebar">
                <h3>Explorateur de fichiers</h3>
                
                <div class="current-path" id="currentPath">
                    Chargement...
                </div>
                
                <button onclick="goUp()" class="secondary">Dossier parent</button>
                <button onclick="refreshBrowser()" class="secondary">Actualiser</button>
                
                <div class="file-browser" id="fileBrowser">
                    Chargement des dossiers...
                </div>
                
                <h3>Actions</h3>
                <button onclick="selectCurrentFolder()">Sélectionner ce dossier</button>
                <button onclick="testConnection()">Test de connexion</button>
            </div>
            
            <!-- Zone principale -->
            <div class="main-content">
                <h2>Dossier sélectionné</h2>
                <div id="selectedPath" class="current-path">
                    Aucun dossier sélectionné
                </div>
                
                <div id="result" class="result" style="display: none;">
                    Résultat apparaîtra ici...
                </div>
            </div>
        </div>

        <script>
            let currentPath = "C:\\\\Users\\\\latif\\\\OneDrive\\\\Desktop";
            let selectedPath = null;
            
            // Charger au démarrage
            window.onload = function() {
                loadDirectory(currentPath);
            };
            
            // Navigation dans les dossiers
            async function loadDirectory(path) {
                try {
                    const response = await fetch(`/browse?path=${encodeURIComponent(path)}`);
                    const data = await response.json();
                    
                    if (data.error) {
                        alert('Erreur: ' + data.error);
                        return;
                    }
                    
                    currentPath = data.current_path;
                    document.getElementById('currentPath').textContent = currentPath;
                    
                    const browser = document.getElementById('fileBrowser');
                    browser.innerHTML = '';
                    
                    // Ajouter les dossiers
                    data.directories.forEach(dir => {
                        const item = document.createElement('div');
                        item.className = 'dir-item';
                        item.textContent = '[DIR] ' + dir;
                        item.onclick = () => {
                            const separator = currentPath.endsWith('\\\\') ? '' : '\\\\';
                            const newPath = currentPath + separator + dir;
                            loadDirectory(newPath);
                        };
                        browser.appendChild(item);
                    });
                    
                    // Ajouter les fichiers (juste pour affichage)
                    data.files.forEach(file => {
                        const item = document.createElement('div');
                        item.className = 'file-item';
                        item.textContent = '[FILE] ' + file;
                        browser.appendChild(item);
                    });
                    
                    if (data.directories.length === 0 && data.files.length === 0) {
                        browser.innerHTML = '<p style="color: #666;">Dossier vide</p>';
                    }
                    
                } catch (error) {
                    console.error('Erreur:', error);
                    alert('Erreur de navigation: ' + error.message);
                }
            }
            
            function goUp() {
                const parts = currentPath.split(/[\\\\/]/);
                if (parts.length > 1) {
                    const parentPath = parts.slice(0, -1).join('\\\\');
                    if (parentPath) {
                        loadDirectory(parentPath);
                    }
                }
            }
            
            function refreshBrowser() {
                loadDirectory(currentPath);
            }
            
            function selectCurrentFolder() {
                selectedPath = currentPath;
                document.getElementById('selectedPath').textContent = selectedPath;
                
                // Visual feedback
                document.getElementById('result').style.display = 'block';
                document.getElementById('result').textContent = 
                    'Dossier sélectionné: ' + selectedPath;
            }
            
            async function testConnection() {
                document.getElementById('result').style.display = 'block';
                document.getElementById('result').textContent = 'Test en cours...';
                
                try {
                    const response = await fetch('/test');
                    const data = await response.json();
                    
                    document.getElementById('result').textContent = 
                        'Connexion réussie! Message: ' + data.message +
                        (selectedPath ? '\\nDossier sélectionné: ' + selectedPath : '');
                        
                } catch (error) {
                    document.getElementById('result').textContent = 
                        'Erreur: ' + error.message;
                }
            }
        </script>
    </body>
    </html>
    """

@app.get("/browse")
async def browse_directory(path: str = "."):
    """API pour naviguer dans les dossiers"""
    try:
        path = os.path.abspath(path)
        
        if not os.path.exists(path):
            return JSONResponse({"error": "Chemin inexistant"}, status_code=400)
        
        if not os.path.isdir(path):
            return JSONResponse({"error": "Ce n'est pas un dossier"}, status_code=400)
        
        items = os.listdir(path)
        directories = []
        files = []
        
        for item in sorted(items):
            item_path = os.path.join(path, item)
            try:
                if os.path.isdir(item_path):
                    directories.append(item)
                else:
                    files.append(item)
            except PermissionError:
                # Ignorer les fichiers sans permission
                continue
        
        return {
            "current_path": path,
            "directories": directories,
            "files": files[:10]  # Limiter à 10 fichiers pour pas surcharger
        }
        
    except PermissionError:
        return JSONResponse({"error": "Permissions insuffisantes"}, status_code=403)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/test")
async def test():
    return {"message": "Interface web opérationnelle!", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    print("Démarrage interface V2 avec explorateur...")
    print("http://localhost:8000")
    uvicorn.run("web_app:app", host="0.0.0.0", port=8000, reload=True)