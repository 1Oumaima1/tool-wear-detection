import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine, SessionLocal
from sqlalchemy.exc import SQLAlchemyError
from app.models.machine import Machine, MachineStatus
from app.models.tool import Tool

from app import models  # noqa: F401  (nécessaire pour que Base connaisse toutes les tables)
from app.services.ai_model import ai_model_service

from app.api.routes import auth, machines, predictions, alerts, settings_routes, dashboard
from app.api.routes import monitoring  # Phase 2 : vidéo + inférence + decision engine


logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("main")

def _ensure_default_machine() -> None:
    db = SessionLocal()
    try:
        machine = db.query(Machine).filter(Machine.name == "CAM-01").first()

        if machine is None:
            machine = Machine(
                name="CAM-01",
                camera_id="CAM-01",
                status=MachineStatus.online
            )
            db.add(machine)
            db.commit()
            db.refresh(machine)
            logger.info("Machine par défaut créée : CAM-01 (id=%s)", machine.id)
        else:
            logger.info("Machine CAM-01 déjà existante (id=%s)", machine.id)

        tool = (
            db.query(Tool)
            .filter(
                Tool.machine_id == machine.id,
                Tool.tool_identifier == "TOOL-01"
            )
            .first()
        )

        if tool is None:
            tool = Tool(
                machine_id=machine.id,
                tool_identifier="TOOL-01"
            )
            db.add(tool)
            db.commit()
            logger.info(
                "Tool par défaut créé : TOOL-01 (machine_id=%s)",
                machine.id
            )
        else:
            logger.info("Tool TOOL-01 déjà existant pour CAM-01")

    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Échec de la création automatique de la machine/outil par défaut"
        )
        raise
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Démarrage de %s (env=%s)", settings.APP_NAME, settings.ENV)

    # Crée les tables si elles n'existent pas encore.
    
    Base.metadata.create_all(bind=engine)
    logger.info("Tables PostgreSQL vérifiées/créées.")
    _ensure_default_machine()
    ai_model_service.load_model()

    yield
    # --- Shutdown ---
    logger.info("Arrêt de l'application.")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Plateforme industrielle de surveillance prédictive des outils de coupe CNC "
        "(EfficientNetV2B0 : Sharp / Used / Dulled)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(machines.router, prefix=API_PREFIX)
app.include_router(predictions.router, prefix=API_PREFIX)
app.include_router(alerts.router, prefix=API_PREFIX)
app.include_router(settings_routes.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(monitoring.router, prefix=API_PREFIX)


# Sert les frames originales et heatmaps Grad-CAM (Phase 5) + futurs PDF statiques
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Sert les vidéos de simulation caméra (Phase 2)
VIDEOS_DIR = Path(__file__).resolve().parent.parent / "videos"
VIDEOS_DIR.mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory=str(VIDEOS_DIR)), name="media")


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "model_loaded": ai_model_service.model_loaded,
    }
