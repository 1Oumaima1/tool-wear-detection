# ToolVision — AI-Based Tool Wear Detection

**Détection intelligente de l'usure des outils industriels par Intelligence Artificielle et Vision par Ordinateur.**

ToolVision est une plateforme de surveillance industrielle basée sur l'**Intelligence Artificielle** qui analyse une vidéo simulant le flux d'une caméra installée sur une machine CNC.

Le système extrait des images de la vidéo **à intervalles réguliers** et utilise un modèle **EfficientNetV2B0** entraîné par **Transfer Learning** pour classifier l'état de l'outil de coupe en trois catégories :

**Sharp · Used · Dulled**

Lorsqu'une usure importante est détectée de manière suffisamment fiable et répétée, le système déclenche automatiquement une **alerte** (avec notification par e-mail), tout en conservant l'historique des prédictions et en fournissant une interface de supervision.

>  **Simulation vidéo**
> Dans cette version, une vidéo `.mp4` pré-enregistrée est utilisée pour simuler le flux provenant d'une caméra industrielle. Cette approche permet de développer et tester toute la chaîne IA sans nécessiter de caméra physique.

**Résultat principal : 89,7 % de précision sur le jeu de test** (avec Test-Time Augmentation).

---

## Objectif du projet

L'objectif de ToolVision est d'utiliser la **Vision par Ordinateur** pour automatiser la surveillance de l'état des outils de coupe utilisés dans les machines CNC.

Le système suit le principe :

```text
Vidéo de la machine
        ↓
Extraction des frames
        ↓
Prétraitement
        ↓
Modèle Deep Learning
        ↓
Classification de l'usure
        ↓
Filtrage des prédictions
        ↓
Détection d'une usure confirmée
        ↓
Alerte + Historique
```

---

## Dataset

Le modèle a été entraîné à partir de la **version augmentée du dataset Mudestreda (Multimodal Device State Recognition Dataset)**, disponible sur Zenodo.

** Dataset utilisé — Mudestreda / dataset_aug :**
https://zenodo.org/records/8238653?preview_file=dataset_aug.zip

Le projet utilise les images d'outils de coupe afin de construire un modèle de classification en **3 classes**.

### Classes

| Classe   | Signification       | Niveau dans l'application |
| -------- | ------------------- | ------------------------- |
| `sharp`  | Outil en bon état   | NORMAL                    |
| `used`   | Usure modérée       | WARNING                   |
| `dulled` | Outil fortement usé | CRITIQUE                  |

### Données utilisées

* **Dataset :** Mudestreda
* **Version :** augmented dataset (`dataset_aug`)
* **Classes :** 3
* **Images exploitables :** 2 532 (toutes valides, sans valeur manquante ni doublon)
* **Taille d'entrée :** 224 × 224 × 3

### Répartition des données

Le dataset est fourni avec un découpage initial (2 424 images d'entraînement, 52 de validation, 56 de test). Les ensembles de validation et de test étant trop petits pour une évaluation fiable, **une nouvelle répartition stratifiée** (par classe, `random_state=42`) a été réalisée :

| Ensemble        | Proportion | Rôle                                  |
| --------------- | ---------- | ------------------------------------- |
| Entraînement    | ≈ 70 %     | Apprentissage des poids du modèle     |
| Validation      | ≈ 15 %     | Suivi et réglage des hyperparamètres  |
| Test            | ≈ 15 %     | Évaluation finale et impartiale       |

### Préparation des données

```text
Images
  ↓
Analyse de la distribution des classes
  ↓
Vérification de la qualité (valeurs manquantes, images valides, doublons)
  ↓
Nouveau découpage stratifié 70 / 15 / 15
  ↓
Redimensionnement 224 × 224 + encodage des étiquettes
  ↓
Entraînement
```

Les notebooks d'analyse et de préparation sont disponibles dans :

```text
ai/notebooks/
├── 01_dataset_analysis.ipynb
├── 02_data_preparation.ipynb
├── 03_model_training.ipynb
└── predict.ipynb
```

---

## Modèle IA

### EfficientNetV2B0

Le modèle utilisé est **EfficientNetV2B0**, appliqué en **Transfer Learning** à partir de poids pré-entraînés sur ImageNet.

L'approche consiste à utiliser un réseau pré-entraîné comme base, puis à l'adapter à la tâche spécifique de classification de l'usure des outils.

```text
Image 224 × 224 × 3
        ↓
EfficientNetV2B0 (pré-entraîné ImageNet)
        ↓
GlobalAveragePooling2D
        ↓
Dropout (0.3) → Dense (128, ReLU) → Dropout (0.2)
        ↓
Dense (3) + Softmax
        ↓
┌────────┬────────┬─────────┐
│ Sharp  │  Used  │ Dulled  │
└────────┴────────┴─────────┘
```

Le modèle entraîné est sauvegardé sous :

```text
backend/models/final_model.keras
```

Le fichier `.keras` n'est pas inclus dans GitHub et doit être placé localement avant le lancement du backend.

---

## Entraînement et résultats

### Stratégie d'entraînement

* **Data augmentation** (train uniquement) : flip horizontal, rotation, zoom, contraste, luminosité.
* **Poids de classes** (`class_weight`) pour compenser le léger déséquilibre entre classes.
* **Callbacks** : `ModelCheckpoint`, `EarlyStopping`, `ReduceLROnPlateau`.
* **Entraînement en deux phases** :

| Phase | Description | Learning rate | Époques max |
| ----- | ----------- | ------------- | ----------- |
| 1     | Entraînement de la tête de classification (base gelée) | 1e-3 | 25 |
| 2     | Fine-tuning des 60 dernières couches d'EfficientNetV2B0 | 5e-5 | 30 |

### Résultats sur le jeu de test

| Configuration                          | Accuracy  |
| -------------------------------------- | --------- |
| Prédiction simple (sans TTA)           | 85,79 %   |
| Prédiction avec TTA (5 augmentations)  | ≈ 89,7 %  |

---

## Pipeline IA

ToolVision ne travaille pas directement sur toute la vidéo. Chaque vidéo est transformée en une succession d'images analysées par le modèle.

### 1. Extraction des frames

OpenCV extrait des frames à intervalles réguliers à partir de la vidéo :

```text
video.mp4
   ↓
OpenCV
   ↓
Frame 1
Frame 2
Frame 3
...
```

### 2. Prétraitement

Chaque image est redimensionnée en :

```text
224 × 224 × 3
```

avant son passage dans EfficientNetV2B0.

### 3. Classification

Le modèle produit une distribution de probabilités :

```text
Sharp   → 0.05
Used    → 0.12
Dulled  → 0.83
```

La classe ayant la probabilité la plus élevée devient la prédiction finale.

### 4. Test-Time Augmentation

Pour rendre les prédictions plus robustes sur les frames vidéo, ToolVision utilise le **Test-Time Augmentation (TTA)**.

Une frame est analysée plusieurs fois avec de légères transformations (retournement horizontal, rotation, zoom) :

```text
                 ┌── Original
                 ├── Version augmentée 1
Frame ───────────┼── Version augmentée 2
                 ├── ...
                 └── Version augmentée 5
                       ↓
                EfficientNetV2B0
                       ↓
               Moyenne des probabilités
                       ↓
                 Classe finale
```

Dans la configuration actuelle, une frame est évaluée **6 fois** (1 originale + 5 augmentées) puis les probabilités sont moyennées.

---

## Decision Engine

Une seule prédiction `dulled` ne déclenche pas immédiatement une alerte.

Le système utilise un **moteur de décision** afin d'éviter les fausses alertes provoquées par une mauvaise classification ponctuelle.

Une alerte est déclenchée lorsque les conditions suivantes sont réunies :

```text
Prediction = DULLED
        +
Confidence ≥ 75 %
        +
3 détections consécutives
        +
Aucune alerte active pour cet outil
        ↓
      ALERTE
```

La classe `used` ne déclenche pas d'alerte critique à elle seule. Cette logique permet de prendre une décision à partir d'une **séquence de prédictions** plutôt que d'une seule image.

---

## Fonctionnalités

### Dashboard

* KPIs du jour
* Dernière détection
* Évolution de l'état d'usure
* Répartition des classes
* Dernières alertes

### Live Monitoring

* Sélection d'une vidéo `.mp4`
* Lecture de la vidéo
* Analyse IA automatique et répétée
* Affichage de la classe prédite et du niveau de confiance
* Suivi de l'évolution des prédictions

La vidéo joue ici le rôle d'une **caméra industrielle simulée**.

### Alerts

* Consultation des alertes
* Filtrage par niveau
* Distinction des niveaux de sévérité
* Statut d'envoi email
* Résolution des alertes

### History

* Historique des inspections
* Classes détectées
* Niveaux de confiance
* Dates d'inspection
* Export CSV

### Authentication

L'application utilise une authentification basée sur **JWT** pour sécuriser l'accès au dashboard.

---

## Architecture

```text
                    ┌─────────────────────┐
                    │    Vidéo .mp4       │
                    │  Caméra simulée      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       OpenCV        │
                    │ Extraction Frames   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Prétraitement     │
                    │    224 × 224        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   EfficientNetV2B0  │
                    │       + TTA         │
                    └──────────┬──────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │ Sharp / Used / Dulled    │
                  │ + Confidence             │
                  └────────────┬─────────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
        ┌─────────────────┐        ┌──────────────────┐
        │   PostgreSQL    │        │ Decision Engine  │
        │   Historique    │        │ Seuil + séquence │
        └─────────────────┘        └────────┬─────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │     Alert       │
                                   │   Email SMTP    │
                                   └─────────────────┘

                         ┌─────────────────────┐
                         │   React Dashboard   │
                         │ Dashboard / Monitor │
                         │ Alerts / History    │
                         └─────────────────────┘
```

---

## Stack technique

### Intelligence Artificielle

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white" alt="TensorFlow">
  <img src="https://img.shields.io/badge/Keras-D00000?style=for-the-badge&logo=keras&logoColor=white" alt="Keras">
  <img src="https://img.shields.io/badge/EfficientNetV2B0-8E44AD?style=for-the-badge" alt="EfficientNetV2B0">
  <img src="https://img.shields.io/badge/Transfer_Learning-6C5CE7?style=for-the-badge" alt="Transfer Learning">
  <img src="https://img.shields.io/badge/TTA-9B59B6?style=for-the-badge" alt="Test-Time Augmentation">
  <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white" alt="scikit-learn">
</p>

Technologies utilisées pour l'analyse des images, l'entraînement du modèle de classification et son évaluation.

### Backend

<p>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge" alt="Pydantic">
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" alt="JWT">
  <img src="https://img.shields.io/badge/SMTP-4A90E2?style=for-the-badge&logo=gmail&logoColor=white" alt="SMTP">
</p>

Le backend assure l'API, l'authentification, la persistance des données, le traitement vidéo et la gestion des alertes.

### Frontend

<p>
  <img src="https://img.shields.io/badge/React_18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React 18">
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS">
  <img src="https://img.shields.io/badge/React_Router-CA4245?style=for-the-badge&logo=reactrouter&logoColor=white" alt="React Router">
  <img src="https://img.shields.io/badge/Axios-5A29E4?style=for-the-badge&logo=axios&logoColor=white" alt="Axios">
  <img src="https://img.shields.io/badge/Recharts-22A699?style=for-the-badge" alt="Recharts">
</p>

Interface web de supervision permettant de visualiser les détections, les alertes, l'historique et le monitoring vidéo.

---

## Structure du projet

```text
tool-wear-detection/
│
├── ai/
│   └── notebooks/
│       ├── 01_dataset_analysis.ipynb
│       ├── 02_data_preparation.ipynb
│       ├── 03_model_training.ipynb
│       └── predict.ipynb
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── static/
│   │
│   ├── models/
│   │   └── final_model.keras
│   │
│   └── videos/
│       └── *.mp4
│
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       ├── context/
│       ├── pages/
│       └── utils/
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Installation

```bash
git clone https://github.com/1Oumaima1/tool-wear-detection.git
cd tool-wear-detection
```

### Prérequis

Avant de lancer l'application :

```text
backend/models/final_model.keras
backend/videos/*.mp4
```

Le modèle entraîné doit être placé dans `backend/models/`.

Une vidéo `.mp4` doit être placée dans `backend/videos/`.

---

## Variables d'environnement

### Backend

```bash
cd backend
cp .env.example .env
```

Principales variables :

| Variable                         | Description                      |
| -------------------------------- | -------------------------------- |
| `DATABASE_URL`                   | Connexion PostgreSQL             |
| `JWT_SECRET_KEY`                 | Clé de signature JWT             |
| `MODEL_PATH`                     | Chemin du modèle IA              |
| `VIDEO_FOLDER`                   | Dossier contenant les vidéos     |
| `DEFAULT_CONFIDENCE_THRESHOLD`   | Seuil de confiance               |
| `DEFAULT_CONSECUTIVE_DETECTIONS` | Nombre de détections nécessaires |
| `SMTP_HOST`                      | Serveur SMTP                     |
| `SMTP_USER`                      | Compte SMTP                      |
| `SMTP_PASSWORD`                  | Mot de passe SMTP                |
| `ALERT_EMAIL_TO`                 | Adresse de réception des alertes |
| `VITE_API_BASE_URL`              | URL de l'API backend             |

---

## Lancement avec Docker

```bash
docker compose up --build -d
```

Services :

```text
Frontend
http://localhost:3000

Backend / Swagger
http://localhost:8000/docs
```

---

## Utilisation

### 1. Connexion

Se connecter à l'application avec un compte administrateur.

### 2. Live Monitoring

Accéder à **Live Monitoring** et sélectionner une vidéo disponible.

Le système exécute automatiquement :

```text
Vidéo
  ↓
Frames
  ↓
Prétraitement
  ↓
EfficientNetV2B0 + TTA
  ↓
Prédiction
  ↓
Decision Engine
  ↓
Alerte éventuelle
```

### 3. Dashboard

Consulter les indicateurs et l'évolution des détections.

### 4. Alerts

Consulter les alertes générées par le système.

### 5. History

Consulter l'historique des inspections et exporter les données en CSV.

---

## Limites actuelles

* La caméra industrielle est actuellement **simulée par des vidéos `.mp4`**.
* Le traitement vidéo est actuellement effectué de manière synchrone.
* Le système actuel est configuré autour d'une machine et d'un outil par défaut.
* Les migrations de base de données avec Alembic ne sont pas encore mises en place.
* La classe `used` (usure intermédiaire) est parfois confondue avec `dulled`, ce qui constitue la principale source d'erreurs du modèle.



## Amlou Oumaima
