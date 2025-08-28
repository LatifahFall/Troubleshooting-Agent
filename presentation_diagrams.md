# Diagrammes Mermaid pour la Présentation

## 1. Architecture Globale du Système (Annexe 1)

```mermaid
graph TB
    subgraph "Frontend"
        A[Interface Web<br/>HTML/CSS/JS]
        B[Navigation Fichiers]
        C[Chat Interactif]
        D[Suivi Temps Réel]
    end
    
    subgraph "Backend API"
        E[FastAPI Server]
        F[Gestionnaire de Sessions]
        G[API Endpoints]
    end
    
    subgraph "Intelligence Artificielle"
        H[OpenAI GPT-4]
        I[Système de Prompts<br/>Jinja2 Templates]
        J[Interpréteur d'Actions]
    end
    
    subgraph "Outils de Diagnostic"
        K[ReadFile<br/>Lecture de logs]
        L[SystemCheck<br/>Monitoring système]
        M[ConnectivityCheck<br/>Tests réseau]
        N[ListDirectory<br/>Navigation]
        O[AskForClarification<br/>Interaction]
        P[ProvideFurtherAssistance<br/>Aide]
        Q[DoneForNow<br/>Finalisation]
    end
    
    subgraph "Persistance & Rapports"
        R[PostgreSQL<br/>Base de données]
        S[Report Manager<br/>Génération rapports]
        T[Fichiers Markdown<br/>Rapports]
    end
    
    subgraph "Intégrations"
        U[Microsoft Teams<br/>Notifications]
        V[Webhooks<br/>API externes]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    E --> H
    H --> I
    I --> J
    J --> K
    J --> L
    J --> M
    J --> N
    J --> O
    J --> P
    J --> Q
    E --> R
    E --> S
    S --> T
    E --> U
    E --> V
    
    style A fill:#e1f5fe
    style E fill:#f3e5f5
    style H fill:#fff3e0
    style K fill:#e8f5e8
    style R fill:#fce4ec
    style U fill:#f1f8e9
```

## 2. Flux de Travail du Diagnostic

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant W as Interface Web
    participant API as FastAPI Backend
    participant AI as Agent IA
    participant T as Outils
    participant DB as Base de Données
    participant R as Rapport Manager
    participant TE as Teams

    U->>W: Sélectionne dossier application
    W->>API: POST /start-diagnostic
    API->>AI: Lance diagnostic
    
    loop Analyse des logs
        AI->>T: ReadFile(log_file)
        T->>AI: Contenu du fichier
        AI->>T: SystemCheck()
        T->>AI: État système
        AI->>T: ConnectivityCheck()
        T->>AI: État réseau
    end
    
    AI->>API: Résultats diagnostic
    API->>DB: Sauvegarde session
    API->>R: Génération rapport
    R->>API: Rapport Markdown
    API->>TE: Notification (optionnel)
    API->>W: Mise à jour interface
    W->>U: Affichage résultats
    
    Note over U,TE: L'utilisateur peut interagir<br/>avec l'agent via le chat
```

## 2.1. Diagramme de Séquence Détaillé - Processus Complet (annexe 2)

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant W as Interface Web
    participant API as FastAPI Backend
    participant AI as Agent IA
    participant TF as ToolFactory
    participant T as Outils
    participant DB as DatabaseManager
    participant RM as ReportManager
    participant TE as Teams

    Note over U,TE: Phase 1: Initialisation
    U->>W: Accède à l'interface web
    W->>API: GET / (page principale)
    API->>W: Retourne index.html
    W->>U: Affiche interface

    Note over U,TE: Phase 2: Navigation et sélection
    U->>W: Navigue dans les dossiers
    W->>API: GET /browse?path=...
    API->>W: Liste des fichiers/dossiers
    W->>U: Affiche navigation
    U->>W: Sélectionne dossier application
    W->>API: POST /start-diagnostic
    API->>AI: Lance diagnostic avec chemin

    Note over U,TE: Phase 3: Configuration de l'agent IA
    AI->>TF: create_function_mappings()
    TF->>AI: Mapping des outils disponibles
    AI->>AI: Charge prompt système (Jinja2)

    Note over U,TE: Phase 4: Analyse automatique
    loop Analyse intelligente
        AI->>T: ReadFile(path)
        T->>AI: Contenu du fichier
        AI->>AI: Analyse du contenu
        alt Erreurs détectées
            AI->>T: SystemCheck()
            T->>AI: État système
            AI->>T: ConnectivityCheck()
            T->>AI: État réseau
        end
    end

    Note over U,TE: Phase 5: Interaction utilisateur (optionnel)
    alt Clarification nécessaire
        AI->>API: Demande clarification
        API->>W: Affiche question dans chat
        W->>U: Question affichée
        U->>W: Réponse utilisateur
        W->>API: POST /chat-response
        API->>AI: Réponse utilisateur
        AI->>AI: Continue analyse
    end

    Note over U,TE: Phase 6: Finalisation et rapport
    AI->>API: Résultats finaux
    API->>DB: save_session()
    DB->>API: Session sauvegardée
    API->>RM: generate_report()
    RM->>API: Rapport Markdown
    API->>TE: send_teams_message()
    API->>W: Mise à jour interface
    W->>U: Affichage résultats finaux

    Note over U,TE: Phase 7: Consultation des rapports
    U->>W: Consulte rapport généré
    W->>API: GET /reports
    API->>DB: get_all_sessions()
    DB->>API: Historique des sessions
    API->>W: Liste des rapports
    W->>U: Affiche rapports disponibles
```

## 2.2. Diagramme de Séquence - Communication Temps Réel (annexe 3)

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant W as Interface Web
    participant API as FastAPI Backend
    participant AI as Agent IA
    participant F as Fichiers Temporaires

    Note over U,F: Communication bidirectionnelle temps réel

    Note over U,F: Phase 1: L'agent pose une question
    AI->>F: Écrit question dans web_chat_question.txt
    API->>W: Polling détecte nouveau fichier
    W->>U: Affiche question dans chat
    U->>W: Saisit réponse
    W->>API: POST /chat-response
    API->>F: Écrit réponse dans web_chat_response.txt
    AI->>F: Lit réponse utilisateur
    AI->>AI: Continue analyse avec contexte

    Note over U,F: Phase 2: Mise à jour en temps réel
    loop Mise à jour continue
        AI->>F: Écrit logs dans diagnostic_logs.txt
        API->>W: Polling détecte nouveaux logs
        W->>U: Affiche progression en temps réel
    end

    Note over U,F: Phase 3: Finalisation
    AI->>F: Écrit résultats finaux
    API->>W: Dernière mise à jour
    W->>U: Affichage résultats complets
```

## 3. Flux de Communication Web

```mermaid
graph LR
    subgraph "Interface Web"
        A[HTML/CSS Interface]
        B[JavaScript Client]
        C[WebSocket/Polling]
    end
    
    subgraph "Backend"
        D[FastAPI Server]
        E[Background Tasks]
        F[File Communication]
    end
    
    subgraph "Agent IA"
        G[OpenAI Client]
        H[Prompt Processing]
        I[Tool Execution]
    end
    
    subgraph "Communication Files"
        J[web_chat_question.txt]
        K[web_chat_response.txt]
        L[diagnostic_logs.txt]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> F
    F --> J
    F --> K
    F --> L
    L --> D
    D --> C
    C --> B
    B --> A
    
    style A fill:#e3f2fd
    style D fill:#f3e5f5
    style G fill:#fff3e0
    style J fill:#e8f5e8
```

## 5. Structure de la Base de Données

```mermaid
erDiagram
    TROUBLESHOOTING_SESSION {
        string id PK
        string app_name
        datetime started_at
        text diagnostic_message
        json final_response
    }
    
    Note over TROUBLESHOOTING_SESSION: Structure simple et efficace
    Note over TROUBLESHOOTING_SESSION: Stockage JSON pour flexibilité
    Note over TROUBLESHOOTING_SESSION: Traçabilité complète des sessions
```

## 6. Processus de Diagnostic Intelligent

```mermaid
flowchart TD
    A[Début Diagnostic] --> B[Analyse du contexte]
    B --> C{Logs disponibles?}
    C -->|Oui| D[Lecture des logs]
    C -->|Non| E[Vérification système]
    
    D --> F[Détection d'erreurs]
    E --> G[Monitoring ressources]
    
    F --> H{Erreurs trouvées?}
    G --> I[Tests connectivité]
    
    H -->|Oui| J[Analyse détaillée]
    H -->|Non| K[Vérifications préventives]
    
    I --> L{Problèmes réseau?}
    J --> M[Génération recommandations]
    K --> N[Rapport préventif]
    
    L -->|Oui| O[Diagnostic réseau]
    L -->|Non| P[Vérifications finales]
    
    M --> Q[Génération rapport]
    N --> Q
    O --> Q
    P --> Q
    
    Q --> R[Notification Teams]
    R --> S[Fin Diagnostic]
    
    style A fill:#e8f5e8
    style Q fill:#fff3e0
    style S fill:#fce4ec
```

## 7. Stack Technologique Détaillé

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[HTML5]
        B[CSS3 + Modern UI]
        C[Vanilla JavaScript]
        D[Real-time Updates]
    end
    
    subgraph "API Layer"
        E[FastAPI Framework]
        F[Pydantic v2 Models]
        G[Background Tasks]
        H[Static File Serving]
    end
    
    subgraph "AI Layer"
        I[OpenAI GPT-4 API]
        J[Jinja2 Templates]
        K[Function Calling]
        L[Prompt Engineering]
    end
    
    subgraph "Data Layer"
        M[PostgreSQL Database]
        N[SQLAlchemy ORM]
        O[Session Management]
        P[Data Validation]
    end
    
    subgraph "System Layer"
        Q[psutil Monitoring]
        R[File System Operations]
        S[Network Connectivity]
        T[Process Management]
        U[telnetlib]
        V[socket]
    end
    
    subgraph "Integration Layer"
        W[Microsoft Teams Webhook]
        X[HTTP Requests]
        Y[JSON Processing]
        Z[Error Handling]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    E --> I
    E --> M
    E --> Q
    E --> W
    I --> J
    I --> K
    I --> L
    M --> N
    M --> O
    M --> P
    Q --> R
    Q --> T
    S --> U
    S --> V
    W --> X
    X --> Y
    Y --> Z
    
    style A fill:#e1f5fe
    style E fill:#f3e5f5
    style I fill:#fff3e0
    style M fill:#fce4ec
    style Q fill:#e8f5e8
    style U fill:#fff8e1
    style V fill:#fff8e1
    style W fill:#f1f8e9
```
