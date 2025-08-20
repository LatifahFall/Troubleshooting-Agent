import os
import json
from datetime import datetime
import uuid
import re


class ReportManager:
    """
    Gestionnaire pour la sauvegarde des rapports de l'agent de troubleshooting.
    Chaque application a son propre dossier identifié par un ID unique.
    """
    
    def __init__(self, reports_base_dir: str = "reports"):
        """
        Initialise le gestionnaire de rapports.
        
        Args:
            reports_base_dir: Répertoire de base pour stocker tous les rapports
        """
        self.reports_base_dir = reports_base_dir
        self._ensure_reports_directory()
    
    def _ensure_reports_directory(self):
        """Crée le répertoire de base des rapports s'il n'existe pas"""
        if not os.path.exists(self.reports_base_dir):
            os.makedirs(self.reports_base_dir)
    
    def _ensure_app_directory(self, app_id: str) -> str:
        """
        Crée le répertoire pour une application spécifique s'il n'existe pas.
        
        Args:
            app_id: Identifiant unique de l'application
            
        Returns:
            Chemin vers le répertoire de l'application
        """
        app_dir = os.path.join(self.reports_base_dir, app_id)
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        return app_dir
    
    def generate_app_id(self, app_path: str = None) -> str:
        """
        Génère un ID pour l'application basé sur le nom du répertoire.
        
        Args:
            app_path: Chemin de l'application (optionnel)
            
        Returns:
            ID de l'application (nom du répertoire)
        """
        if app_path:
            # Utilise le nom du répertoire comme ID
            return os.path.basename(os.path.abspath(app_path))
        else:
            # Génère un UUID si pas de chemin fourni
            return str(uuid.uuid4())[:8]
    
    def create_report_filename(self) -> str:
        """
        Crée le nom de fichier pour le rapport avec timestamp.
        
        Returns:
            Nom de fichier du rapport
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"Troubleshooting report - {timestamp}.md"
    
    def _html_to_text(self, html_content: str) -> str:
        """
        Convertit le contenu HTML en texte brut pour les rapports sauvegardés.
        
        Args:
            html_content: Contenu avec des balises HTML
            
        Returns:
            Contenu en texte brut avec mise en forme simple
        """
        content = html_content
        
        # Nettoyer les retours à la ligne et espaces autour des balises
        content = re.sub(r'\s*\n\s*', ' ', content)  # Remplacer les sauts de ligne par des espaces
        content = re.sub(r'>\s+<', '><', content)  # Supprimer les espaces entre balises
        
        # Remplacer les balises de titre
        content = re.sub(r'<h2>(.*?)</h2>', r'\n\n## \1\n\n', content)
        content = re.sub(r'<h3>(.*?)</h3>', r'\n\n### \1\n\n', content)
        
        # Remplacer les paragraphes
        content = re.sub(r'<p>(.*?)</p>', r'\1\n\n', content)
        
        # Traitement des listes ordonnées AVANT les listes non ordonnées
        def process_ordered_list(match):
            ol_content = match.group(1)
            lines = []
            counter = 1
            
            # Extraire tous les éléments <li>
            li_items = re.findall(r'<li>(.*?)</li>', ol_content)
            for item in li_items:
                # Nettoyer le contenu de chaque élément
                clean_item = re.sub(r'<strong>(.*?)</strong>', r'**\1**', item)
                clean_item = re.sub(r'<code>(.*?)</code>', r'`\1`', clean_item)
                clean_item = re.sub(r'<[^>]+>', '', clean_item)  # Supprimer les autres balises
                lines.append(f"{counter}. {clean_item}")
                counter += 1
            
            return '\n\n' + '\n'.join(lines) + '\n\n'
        
        # Appliquer le traitement des listes ordonnées
        content = re.sub(r'<ol>(.*?)</ol>', process_ordered_list, content)
        
        # Traitement des listes non ordonnées
        def process_unordered_list(match):
            ul_content = match.group(1)
            lines = []
            
            # Extraire tous les éléments <li>
            li_items = re.findall(r'<li>(.*?)</li>', ul_content)
            for item in li_items:
                # Nettoyer le contenu de chaque élément
                clean_item = re.sub(r'<strong>(.*?)</strong>', r'**\1**', item)
                clean_item = re.sub(r'<code>(.*?)</code>', r'`\1`', clean_item)
                clean_item = re.sub(r'<[^>]+>', '', clean_item)  # Supprimer les autres balises
                lines.append(f"• {clean_item}")
            
            return '\n\n' + '\n'.join(lines) + '\n\n'
        
        # Appliquer le traitement des listes non ordonnées
        content = re.sub(r'<ul>(.*?)</ul>', process_unordered_list, content)
        
        # Remplacer les balises de mise en forme restantes
        content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', content)
        content = re.sub(r'<code>(.*?)</code>', r'`\1`', content)
        
        # Nettoyer toutes les balises HTML restantes
        content = re.sub(r'<[^>]+>', '', content)
        
        # Normaliser les espaces et sauts de ligne
        content = re.sub(r'[ \t]+', ' ', content)  # Remplacer les espaces multiples par un seul
        content = re.sub(r'\n{3,}', '\n\n', content)  # Limiter à 2 sauts de ligne consécutifs max
        content = re.sub(r'^\s+|\s+$', '', content)  # Supprimer les espaces en début/fin
        
        return content.strip()
    
    def save_report(self, app_id: str, message: str) -> str:
        """
        Sauvegarde un rapport pour une application.
        
        Args:
            app_id: Identifiant unique de l'application
            message: Message complet de l'agent (diagnostic + étapes de résolution)
            
        Returns:
            Chemin vers le fichier de rapport créé
        """
        # Assure que le répertoire de l'application existe
        app_dir = self._ensure_app_directory(app_id)
        
        # Crée le nom de fichier
        filename = self.create_report_filename()
        filepath = os.path.join(app_dir, filename)
        
        # Convertir le contenu HTML en texte brut pour le rapport sauvegardé
        clean_message = self._html_to_text(message)
        
        # Formate le contenu
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"""# Rapport de Troubleshooting

**Date et heure:** {timestamp}

## Rapport de l'agent

{clean_message}

---
*Rapport généré automatiquement par l'agent de troubleshooting*
"""
        
        # Sauvegarde le fichier
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def list_reports(self, app_id: str) -> list:
        """
        Liste tous les rapports pour une application donnée.
        
        Args:
            app_id: Identifiant unique de l'application
            
        Returns:
            Liste des fichiers de rapport pour cette application
        """
        app_dir = os.path.join(self.reports_base_dir, app_id)
        if not os.path.exists(app_dir):
            return []
        
        reports = []
        for filename in os.listdir(app_dir):
            if filename.startswith("Troubleshooting report") and filename.endswith(".md"):
                filepath = os.path.join(app_dir, filename)
                reports.append({
                    'filename': filename,
                    'filepath': filepath,
                    'created': os.path.getctime(filepath)
                })
        
        # Trie par date de création (plus récent en premier)
        reports.sort(key=lambda x: x['created'], reverse=True)
        return reports
    
    def list_all_apps(self) -> list:
        """
        Liste toutes les applications qui ont des rapports.
        
        Returns:
            Liste des IDs d'application qui ont des rapports
        """
        if not os.path.exists(self.reports_base_dir):
            return []
        
        apps = []
        for item in os.listdir(self.reports_base_dir):
            item_path = os.path.join(self.reports_base_dir, item)
            if os.path.isdir(item_path):
                apps.append(item)
        
        return sorted(apps)