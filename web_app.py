from fastapi import FastAPI
from fastapi.responses import HTMLResponse

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
                max-width: 800px; 
                margin: 50px auto; 
                padding: 20px; 
                text-align: center;
            }
            button {
                background-color: #007bff; 
                color: white; 
                border: none; 
                padding: 15px 30px; 
                margin: 10px;
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 16px;
            }
            button:hover { background-color: #0056b3; }
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
        <h1>Troubleshooting Agent - Version 1</h1>
        <p>Interface de test basique</p>
        
        <button onclick="testConnection()">Test de connexion</button>
        
        <div id="result" class="result" style="display: none;">
            Résultat apparaîtra ici...
        </div>

        <script>
            async function testConnection() {
                document.getElementById('result').style.display = 'block';
                document.getElementById('result').textContent = 'Test en cours...';
                
                try {
                    const response = await fetch('/test');
                    const data = await response.json();
                    
                    document.getElementById('result').textContent = 
                        'Connexion réussie! Message: ' + data.message;
                        
                } catch (error) {
                    document.getElementById('result').textContent = 
                        'Erreur: ' + error.message;
                }
            }
        </script>
    </body>
    </html>
    """

@app.get("/test")
async def test():
    return {"message": "Interface web opérationnelle!", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    print("Démarrage interface V1...")
    print("http://localhost:8000")
    uvicorn.run("web_app:app", host="0.0.0.0", port=8000, reload=True)