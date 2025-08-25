# Troubleshooting Agent Tetra

Un agent intelligent de diagnostic et de résolution de problèmes pour applications web utilisant l'IA générative avec interface web.

## Description

Cet agent automatise le processus de troubleshooting en analysant les logs d'applications, effectuant des vérifications système et fournissant des diagnostics détaillés avec des recommandations de résolution. Il dispose d'une interface web interactive pour une expérience utilisateur optimale.

## Fonctionnalités

- **Analyse automatique des logs** : Lecture et interprétation intelligente des fichiers de logs
- **Vérifications système** : Monitoring des ressources (CPU, mémoire, disque)
- **Tests de connectivité** : Vérification des connexions réseau
- **Rapports de diagnostic** : Génération automatique de rapports détaillés
- **Interface web** : Interface FastAPI avec navigation de fichiers et chat interactif
- **Intégration Teams** : Notifications automatiques sur Microsoft Teams
- **Base de données PostgreSQL** : Sauvegarde des sessions de troubleshooting
- **Interaction en temps réel** : Chat interactif avec l'agent pour clarifications
- **Navigation de fichiers** : Interface pour explorer les répertoires et sélectionner le dossier application

## Prérequis

- Python 3.8+
- OpenAI API key
- PostgreSQL
- Microsoft Teams webhook(optionnel)

## Installation

1. Cloner le projet
2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurer les variables d'environnement dans un fichier `.env` :
```env
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/troubleshooting
HOST=your_host
PORT=your_port
```

## Utilisation

### Mode Web (Recommandé)

Lancer l'interface web :
```bash
python web_app.py
```

Puis ouvrir votre navigateur sur `http://localhost:8000`

L'interface web permet de :
- Naviguer dans les répertoires pour sélectionner les logs à analyser
- Lancer des diagnostics en temps réel
- Interagir avec l'agent via un chat
- Suivre l'avancement des analyses
- Consulter les rapports générés

### Mode Console

Lancer l'agent en mode console :
```bash
python main.py
```

L'agent va automatiquement :
1. Analyser les logs disponibles dans le répertoire
2. Effectuer des vérifications système
3. Fournir un diagnostic complet
4. Générer un rapport de troubleshooting
5. Envoyer les résultats sur Teams (si configuré)

## Structure du projet

- `main.py` : Point d'entrée principal de l'agent (mode console)
- `web_app.py` : Interface web FastAPI
- `tools.py` : Outils de diagnostic (lecture fichiers, vérifications système, etc.)
- `database.py` : Gestionnaire de base de données PostgreSQL
- `report_manager.py` : Gestionnaire de rapports
- `system_prompt.j2` : Template du prompt système pour l'IA
- `static/` : Fichiers statiques de l'interface web
  - `index.html` : Interface principale
  - `script_new.js` : Logique JavaScript
  - `styles.css` : Styles CSS
- `reports/` : Répertoire des rapports générés
- `chemin/` : Répertoire d'exemple avec logs de test

## Outils disponibles

- **ReadFile** : Lecture de fichiers logs
- **SystemCheck** : Vérification des ressources système
- **ConnectivityCheck** : Test de connectivité réseau
- **ListDirectory** : Exploration de répertoires
- **AskForClarification** : Interaction avec l'utilisateur
- **ProvideFurtherAssistance** : Assistance supplémentaire
- **DoneForNow** : Finalisation de session

## Rapports

Les rapports sont automatiquement générés au format Markdown dans le dossier `reports/` avec :
- Horodatage de l'analyse
- Diagnostic complet
- Recommandations de résolution
- Historique des actions effectuées
- Métadonnées de session

## Technologies utilisées

- **OpenAI GPT-4** : IA générative pour l'analyse
- **FastAPI** : Framework web moderne pour l'interface
- **Pydantic v2** : Validation et sérialisation des données
- **SQLAlchemy** : ORM pour la base de données PostgreSQL
- **Jinja2** : Templates pour les prompts
- **psutil** : Monitoring système
- **requests** : Intégration Teams
- **Uvicorn** : Serveur ASGI pour FastAPI

## Configuration

L'agent utilise un système de prompts dynamiques configurables via le fichier `system_prompt.j2` pour adapter le comportement selon les besoins.

### Variables d'environnement

- `OPENAI_API_KEY` : Clé API OpenAI (requise)
- `DATABASE_URL` : URL de connexion PostgreSQL
- `HOST` : Hôte pour le serveur web (défaut: localhost)
- `PORT` : Port pour le serveur web (défaut: 8000)
- `WEB_MODE` : Mode web activé (true/false)

## API Endpoints

- `GET /` : Interface principale
- `GET /browse` : Navigation dans les répertoires
- `POST /start-diagnostic` : Démarrer un diagnostic
- `GET /logs` : Récupérer les logs en temps réel
- `POST /chat-response` : Envoyer une réponse au chat
- `GET /reports` : Lister les rapports disponibles

---

*Développé pour automatiser le troubleshooting d'applications et améliorer la réactivité en cas de problèmes avec une interface moderne et intuitive.*
