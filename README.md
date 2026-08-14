# 🛡️ ToolVision — Plateforme de Surveillance Industrielle par IA

**Détection prédictive de l'usure des outils de coupe CNC, par vision par ordinateur.**

ToolVision surveille une vidéo d'une machine CNC, classifie l'état d'usure
de l'outil de coupe image par image (**Sharp / Used / Dulled**) grâce à un
modèle **EfficientNetV2B0** entraîné spécifiquement pour cette tâche, et
déclenche automatiquement une alerte email dès qu'un outil est confirmé
usé sur plusieurs détections consécutives — avec historique complet et
tableau de bord temps réel.

> 📌 **À propos de la vidéo** : aucune caméra physique n'est branchée à ce
> projet. La surveillance se fait sur des fichiers `.mp4` pré-enregistrés
> (déposés dans `backend/videos/`) qui simulent un flux de caméra
> industrielle. Cette simulation est un choix assumé : la couche
> d'acquisition vidéo est volontairement découplée du reste du pipeline pour
> qu'un vrai flux caméra/RTSP puisse être branché plus tard sans toucher à
> l'IA, à la logique de décision, au stockage ni aux alertes.

---

## 📖 Sommaire

- [Aperçu](#-aperçu)
- [Dataset](#-dataset)
- [Modèle IA entraîné](#-modèle-ia-entraîné)
- [Fonctionnalités](#-fonctionnalités)
- [Stack technique](#-stack-technique)
- [Architecture du système](#-architecture-du-système)
- [Structure du projet](#-structure-du-projet)
- [Installation](#-installation)
- [Variables d'environnement](#-variables-denvironnement)
- [Lancer le projet](#-lancer-le-projet)
- [Utilisation](#-utilisation)
- [Documentation complète](#-documentation-complète)
- [Limites connues](#-limites-connues)
- [Améliorations futures](#-améliorations-futures)
- [Licence](#-licence)

---

## 📋 Aperçu

Ce projet part d'un modèle de classification d'images entraîné pour
distinguer trois états d'usure d'un outil de coupe CNC, et le transforme en
une **plateforme complète de surveillance industrielle** : backend FastAPI
qui fait tourner le modèle sur des frames vidéo échantillonnées, moteur de
décision qui filtre le bruit avant d'alerter, base PostgreSQL pour
l'historique, et tableau de bord React pour l'opérateur.

## 🧠 Dataset

Le modèle a été entraîné sur un jeu de données d'images d'outils de coupe
CNC, réparties en **3 classes** :

| Classe | Signification |
|---|---|
| `Sharp` | Outil en bon état, aucune usure visible |
| `Used` | Usure modérée, outil encore utilisable |
| `Dulled` | Outil usé, à remplacer |

**Caractéristiques du dataset** :
- Environ **2 500 images** réparties sur les 3 classes.
- Images redimensionnées en **224×224×3** avant entraînement (format
  d'entrée standard d'EfficientNetV2B0).
- Split entraînement/validation réalisé lors de la phase de préparation des
  données, avant l'entraînement du modèle.
- L'analyse exploratoire (distribution des classes, vérification de la
  qualité des images, détection de doublons/images corrompues) et la
  préparation (redimensionnement, encodage des labels) ont été faites dans
  des notebooks Jupyter dédiés (`01_dataset_analysis.ipynb`,
  `02_data_preparation.ipynb`), conservés comme trace du travail de
  data science en amont du développement de la plateforme.

## 🎯 Modèle IA entraîné

**Architecture** : `EfficientNetV2B0`, utilisé en **transfer learning**
(poids pré-entraînés réutilisés puis affinés sur le dataset ci-dessus), avec
une tête de classification adaptée aux 3 classes du projet. Le modèle final
est sauvegardé au format `.keras` (`final_model.keras`) et chargé tel quel
par le backend — aucune reconstruction d'architecture au runtime, le fichier
contient le modèle entraîné complet.

**Entraînement** : réalisé dans `03_model_training.ipynb`, avec le
prétraitement suivant appliqué à chaque image avant passage dans le réseau :
redimensionnement 224×224, normalisation gérée en interne par la couche de
rescaling d'EfficientNet (voir point ci-dessous).

**Un bug réel rencontré et corrigé pendant le développement** : une
double normalisation (`/255` manuelle appliquée *en plus* de la
normalisation déjà intégrée à la première couche du modèle) a fait chuter
l'accuracy de validation d'environ **89 % à ~34 %** sans qu'aucune erreur ne
soit levée — le modèle continuait de tourner, juste avec des prédictions
dégradées. Le correctif a consisté à supprimer la normalisation manuelle
redondante et à laisser le modèle gérer son propre prétraitement, ce qui a
restauré les performances d'origine. C'est un exemple concret de bug
"silencieux" en ML (le pipeline s'exécute sans erreur, mais les résultats
sont faux) — gardé en mémoire dans le code (`ai_model.py`) pour éviter de le
réintroduire par erreur.

**Test-Time Augmentation (TTA)** : pour stabiliser les prédictions sur des
frames vidéo (angle, luminosité, flou de mouvement variables), chaque frame
est en réalité passée **6 fois** dans le modèle — une fois telle quelle, puis
5 fois avec une légère augmentation aléatoire (`RandomFlip` horizontal,
`RandomRotation` ±5°, `RandomZoom` ±5%) — et les 6 sorties softmax sont
moyennées avant de prendre la classe finale. Ce choix ajoute un peu de
latence (6 passes au lieu d'1) contre des prédictions plus stables frame à
frame.

**Explicabilité (Grad-CAM)** : bien que non exposé dans les 5 pages actuelles
du tableau de bord (voir plus bas), le backend expose un endpoint
`GET /predictions/{id}/gradcam` qui calcule une vraie heatmap Grad-CAM
(gradients réels sur la dernière couche convolutive, pas une simulation) pour
visualiser quelles zones de l'image ont influencé la prédiction.

## ✨ Fonctionnalités

Le tableau de bord actuel (React) expose **5 pages** :

| Page | Rôle |
|---|---|
| **Login** | Authentification JWT |
| **Dashboard** | KPIs du jour, dernière détection, courbe d'évolution de l'usure, répartition des classes, dernières alertes |
| **Live Monitoring** | Lecture de la vidéo sélectionnée + déclenchement automatique et répété de l'analyse IA sur cette vidéo, overlay de détection en direct |
| **Alerts** | Liste filtrable des alertes (toutes / critiques / warnings), résolution, statut d'envoi email |
| **History** | Historique complet des inspections, filtre par date/classe, export CSV |

**Machine et outil uniques** : la plateforme est volontairement simplifiée à
**une seule machine** (`CAM-01`) et **un seul outil** (`TOOL-01`),
provisionnés automatiquement au démarrage du backend — aucune création
manuelle requise via Swagger.

**Sous le capot, le backend expose aussi** (accessible via Swagger
`/docs`, non branché à une page dédiée dans l'UI actuelle) : génération de
rapports PDF (daily/weekly/monthly), Grad-CAM à la demande, gestion complète
multi-machines/outils (CRUD), et configuration des seuils du moteur de
décision — des fondations gardées pour une évolution future du frontend sans
retravailler le backend.

**Moteur de décision** : une alerte n'est créée que si **toutes** ces
conditions sont réunies — prédiction `Dulled`, confiance ≥ seuil configurable
(défaut 75%), **N détections consécutives** au-dessus du seuil (défaut 3), et
aucune alerte déjà active pour cet outil. Ce filtrage évite le bruit d'une
seule frame mal classée.

## 🛠 Stack technique

**Backend** : FastAPI · SQLAlchemy · PostgreSQL · Pydantic · python-jose (JWT)
· passlib/bcrypt · TensorFlow/Keras · OpenCV · ReportLab · Matplotlib · Uvicorn

**Frontend** : React 18 · Vite · Tailwind CSS · React Router · Axios ·
Recharts · react-icons

**IA** : EfficientNetV2B0 (transfer learning) · Test-Time Augmentation ·
Grad-CAM

**Infra** : Docker · Docker Compose · Nginx

## 🏗 Architecture du système

```
Vidéo simulée (.mp4, backend/videos/)
        │
        ▼
OpenCV — extraction de frames échantillonnées
        │
        ▼
Prétraitement (resize 224×224)
        │
        ▼
EfficientNetV2B0 + TTA (6 passes moyennées)
        │
        ▼
Prédiction { Sharp | Used | Dulled, confiance }
        │
        ├──────────────► PostgreSQL (historique — chaque frame est enregistrée)
        │
        ▼
Moteur de décision (seuil + détections consécutives)
        │
        ├─── conditions non réunies ──► fin (juste stocké)
        │
        └─── conditions réunies ──► Alert créée ──► Email SMTP
        │
        ▼
Dashboard React (lecture des données stockées, pas de logique métier côté frontend)
```

Diagramme détaillé, diagrammes UML (cas d'usage, classes, séquence,
activité, composants, déploiement, paquetages) : voir
[`docs/`](docs/).

## 📁 Structure du projet

```
tool-wear-detection/
├── .env.example
├── .gitignore
├── .venv/
├── ai/
│   ├── notebooks/
│   └── scripts/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── static/
│   │       ├── frames/
│   │       └── gradcam/
│   ├── models/
│   ├── reports/
│   └── videos/
├── dataset/
├── docker-compose.yml
├── frontend/
│   └── src/
│       ├── api/
│       ├── assets/
│       ├── components/
│       │   ├── layout/
│       │   └── ui/
│       ├── context/
│       ├── pages/
│       └── utils/
├── models/
├── README.md
└── requirements.txt

## ⚙️ Installation

```bash
git clone <url-du-repo>
cd agatronic-platform
```

Prérequis avant de démarrer :
- Ton modèle entraîné → `backend/models/final_model.keras`
- Au moins une vidéo de simulation → `backend/videos/`

## 🔑 Variables d'environnement

```bash
cp .env.example .env
```

Principales variables (voir `.env.example` pour la liste complète) :

| Variable | Rôle |
|---|---|
| `DATABASE_URL` | Connexion PostgreSQL |
| `JWT_SECRET_KEY` | Clé de signature des tokens — à changer avant tout déploiement réel |
| `MODEL_PATH` | Chemin vers `final_model.keras` |
| `VIDEO_FOLDER` | Dossier des vidéos de simulation |
| `DEFAULT_CONFIDENCE_THRESHOLD` / `DEFAULT_CONSECUTIVE_DETECTIONS` | Réglages du moteur de décision |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` / `ALERT_EMAIL_TO` | Envoi des emails d'alerte |

## 🐳 Lancer le projet

**Avec Docker (recommandé)** :
```bash
docker compose up --build -d
```
- Frontend → http://localhost:3000
- Backend / Swagger → http://localhost:8000/docs

**Sans Docker (développement)** :
```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r ../requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (autre terminal)
cd frontend
npm install
npm run dev
```

### Premier compte

Aucun utilisateur n'existe par défaut. Créer le premier admin :
```bash
docker compose exec backend python -c "
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password
db = SessionLocal()
db.add(User(username='admin', email='admin@toolguard.ai',
             hashed_password=hash_password('ChangeMe123!'), role=UserRole.admin))
db.commit()
"
```

## 🚀 Utilisation

1. Se connecter sur `/login`.
2. Aller sur **Live Monitoring** : la vidéo déposée dans `backend/videos/`
   apparaît dans le sélecteur de source, se lit automatiquement, et
   l'analyse IA se relance en boucle sur cette vidéo toutes les ~8 secondes.
3. Consulter **Dashboard** pour la vue d'ensemble du jour.
4. Consulter **Alerts** pour voir/résoudre les alertes déclenchées.
5. Consulter **History** pour l'historique complet et l'export CSV.

## 📚 Documentation complète

Le dossier [`docs/`](docs/) contient une documentation détaillée pensée
aussi bien pour un usage technique que pour un rapport de stage :

- `docs/API.md` — chaque endpoint, requête/réponse
- `docs/DATABASE.md` — les 8 tables, colonnes, relations
- `docs/AI_PIPELINE.md` — dataset, modèle, TTA, moteur de décision, Grad-CAM
- `docs/WORKFLOW.md` — flux complet d'une requête `process-video`
- `docs/REPORTS.md` — contenu exact des rapports PDF
- `docs/DEPLOYMENT.md` — Docker, volumes, variables, limites de prod
- `docs/uml/*.puml` — 7 diagrammes UML (source PlantUML)
- `docs/assets/` — diagrammes rendus (PNG/SVG)

## ⚠️ Limites connues

- **Traitement vidéo synchrone** : `process-video` bloque le temps de tout
  traiter — pas de file d'attente en arrière-plan pour l'instant.
- **Pas de vraie caméra** : uniquement des fichiers `.mp4` pré-enregistrés,
  par design (voir note en haut de ce README).
- **Fichiers statiques non authentifiés** : les images de frames/Grad-CAM
  servies sous `/static/` ne sont pas protégées par JWT.
- **Pas de migrations Alembic** : le schéma est créé une fois via
  `create_all()`, sans gestion de migration incrémentale.
- **Frontend limité à 5 pages** : Reports, Explainable AI (Grad-CAM),
  gestion multi-machines et réglages avancés existent côté backend mais
  n'ont pas (encore) d'interface dédiée dans le tableau de bord actuel.

## 🔮 Améliorations futures

- Interface dédiée pour les rapports PDF et le Grad-CAM (déjà fonctionnels côté API)
- Ingestion caméra live (RTSP/webcam) en complément des vidéos simulées
- File d'attente asynchrone pour le traitement vidéo
- Migrations Alembic
- URLs signées/authentifiées pour les fichiers statiques


formelle choisie pour l'instant — à ajouter (MIT, Apache-2.0, ou la licence
préférée de ton établissement) avant toute utilisation publique ou
commerciale.
