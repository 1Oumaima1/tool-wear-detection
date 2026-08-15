# Agatronic Industrial AI Monitoring Platform — Backend

Backend FastAPI pour la surveillance prédictive des outils de coupe CNC
(EfficientNetV2B0 : Sharp / Used / Dulled), construit à partir du socle IA du
projet `tool-wear-detection`.

## Phases livrées

- ✅ **Phase 1** — API FastAPI, PostgreSQL (8 tables), JWT auth, service IA (inférence + TTA)
- ✅ **Phase 2** — Pipeline vidéo : `videos/` → extraction de frames (OpenCV) → inférence → Decision Engine → Alertes email
- ✅ **Phase 5** — Explainable AI : Grad-CAM réel (gradients TensorFlow sur la dernière couche conv), généré à la demande et mis en cache sur disque
- ✅ **Phase 6** — Rapports PDF (ReportLab + Matplotlib) : daily/weekly/monthly, avec graphiques réels et recommandations
- ✅ **Phase 7** — Dockerfile + docker-compose (voir `../docker-compose.yml` à la racine)
- ⬜ Phase 3/4 — voir `../frontend/README.md` et note "Live Monitoring" du README racine (pas de caméra réelle dans ce projet)

## Installation

```bash
cd agatronic-backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r ../requirements.txt   # unique requirements.txt, à la racine du repo

cp .env.example .env
# -> édite .env : DATABASE_URL, JWT_SECRET_KEY, SMTP_*, etc.
```

### Base de données
Crée la base PostgreSQL (les tables sont créées automatiquement au démarrage) :
```bash
createdb agatronic_monitoring
```

### Modèle IA
Dépose ton fichier entraîné ici (celui qui est gitignored dans le repo original) :
```
models/final_model.keras
```
Si absent, l'API démarre normalement mais les endpoints d'inférence/monitoring
renvoient une erreur claire tant que le fichier n'est pas présent.

### Vidéos (Phase 2)
Dépose tes `.mp4` dans `videos/` — voir `videos/README.md` pour le détail.

## Lancer l'API

```bash
uvicorn app.main:app --reload --port 8000
```

Documentation interactive (Swagger) : http://localhost:8000/docs

## Premier compte admin

Aucun utilisateur n'existe au premier démarrage. Crée le premier admin
directement en base (ou via un script `create_admin.py` à ajouter), car
`/auth/register` exige déjà un token admin. Exemple rapide en Python :

```python
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

db = SessionLocal()
db.add(User(
    username="admin",
    email="admin@agatronic.com",
    hashed_password=hash_password("ChangeMe123!"),
    role=UserRole.admin,
))
db.commit()
```

## Tester le pipeline complet (Phase 1 + 2)

1. `POST /api/v1/auth/login` → récupère le token JWT
2. `POST /api/v1/machines/` → crée une machine
3. `POST /api/v1/machines/{id}/tools` → crée un outil
4. Dépose une vidéo dans `videos/`
5. `POST /api/v1/monitoring/process-video` avec `machine_id` / `tool_id` / `video_filename`
6. `GET /api/v1/predictions/` → vérifie l'historique enregistré
7. `GET /api/v1/alerts/` → vérifie si une alerte + email ont été déclenchés
   (nécessite `confidence_threshold` atteint sur `consecutive_detections_required`
   frames consécutives — configurable via `PUT /api/v1/settings/`)

## Nouveaux endpoints (Phases 5 & 6)

| Endpoint | Description |
|---|---|
| `GET /predictions/{id}/gradcam` | Génère (ou retourne en cache) l'image originale + la heatmap Grad-CAM pour une prédiction |
| `POST /reports/generate` | Génère un rapport PDF réel (`report_type`: daily/weekly/monthly) |
| `GET /reports/` | Liste les rapports déjà générés |
| `GET /reports/{id}/download` | Télécharge le PDF |

Les images (frames originales + Grad-CAM) sont servies statiquement sous
`/static/frames/` et `/static/gradcam/` (voir `app.mount` dans `main.py`).

## Déploiement Docker

Voir le `README.md` à la racine du repo (`../README.md`) et `../docker-compose.yml`.
Ce dossier contient son propre `Dockerfile` utilisable indépendamment :

Ce dossier contient son propre `Dockerfile`, mais **le contexte de build doit
être la racine du repo** (pas `backend/`), car l'image installe l'unique
`requirements.txt` du projet, situé à la racine :

```bash
cd ..   # se placer à la racine du repo (agatronic-platform/)
docker build -f backend/Dockerfile -t agatronic-backend .
docker run -p 8000:8000 --env-file backend/.env agatronic-backend
```

## Structure

```
app/
├── main.py                 # point d'entrée FastAPI
├── config.py               # settings (.env)
├── database.py             # engine SQLAlchemy + session
├── models/                 # 8 tables : User, Machine, Tool, Prediction,
│                              Alert, Report, PlatformSettings, Log
├── schemas/                 # validation Pydantic (entrée/sortie API)
├── core/security.py        # JWT + hashing
├── api/
│   ├── deps.py              # get_current_user, require_admin
│   └── routes/
│       ├── auth.py
│       ├── machines.py       # + sous-routes tools
│       ├── predictions.py    # historique + test manuel d'image
│       ├── alerts.py
│       ├── settings_routes.py
│       ├── dashboard.py      # résumé pour la page Dashboard
│       ├── monitoring.py     # Phase 2 : pipeline vidéo complet
│       └── reports.py        # Phase 6 : génération/liste/téléchargement PDF
└── services/
    ├── ai_model.py           # chargement modèle + prédiction + TTA
    ├── video_processor.py    # extraction de frames OpenCV
    ├── decision_engine.py    # seuil + détections consécutives -> Alert
    ├── email_service.py      # envoi SMTP
    ├── gradcam.py            # Phase 5 : heatmap Grad-CAM réelle
    └── reports_service.py    # Phase 6 : construction PDF (ReportLab + Matplotlib)
```
