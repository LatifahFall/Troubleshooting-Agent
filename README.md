# Troubleshooting Agent

Un agent intelligent de diagnostic et de résolution de problèmes pour applications web utilisant l'IA générative.

## Description

Cet agent automatise le processus de troubleshooting en analysant les logs d'applications, effectuant des vérifications système et fournissant des diagnostics détaillés avec des recommandations de résolution.

## Fonctionnalités

- **Analyse automatique des logs** : Lecture et interprétation intelligente des fichiers de logs
- **Vérifications système** : Monitoring des ressources (CPU, mémoire, disque)
- **Tests de connectivité** : Vérification des connexions réseau
- **Rapports de diagnostic** : Génération automatique de rapports détaillés
- **Intégration Teams** : Notifications automatiques sur Microsoft Teams
- **Base de données** : Sauvegarde des sessions de troubleshooting
- **Interface interactive** : Possibilité de demander des clarifications à l'utilisateur

## Prérequis

- Python 3.8+
- OpenAI API key
- PostgreSQL
- Microsoft Teams webhook

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

Lancer l'agent :
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

- `main.py` : Point d'entrée principal de l'agent
- `tools.py` : Outils de diagnostic (lecture fichiers, vérifications système, etc.)
- `database.py` : Gestionnaire de base de données
- `report_manager.py` : Gestionnaire de rapports
- `system_prompt.j2` : Template du prompt système pour l'IA
- `reports/` : Répertoire des rapports générés

## Outils disponibles

- **ReadFile** : Lecture de fichiers logs
- **SystemCheck** : Vérification des ressources système
- **ConnectivityCheck** : Test de connectivité réseau
- **ListDirectory** : Exploration de répertoires
- **AskForClarification** : Interaction avec l'utilisateur
- **ProvideFurtherAssistance** : Assistance supplémentaire

## Rapports

Les rapports sont automatiquement générés au format Markdown dans le dossier `reports/` avec :
- Horodatage de l'analyse
- Diagnostic complet
- Recommandations de résolution
- Historique des actions effectuées

## Technologies utilisées

- **OpenAI GPT-4** : IA générative pour l'analyse
- **Pydantic** : Validation et sérialisation des données
- **SQLAlchemy** : ORM pour la base de données
- **Jinja2** : Templates pour les prompts
- **psutil** : Monitoring système
- **requests** : Intégration Teams

## Configuration avancée

L'agent utilise un système de prompts dynamiques configurables via le fichier `system_prompt.j2` pour adapter le comportement selon les besoins.

---

*Développé pour automatiser le troubleshooting d'applications et améliorer la réactivité en cas de problèmes.*
