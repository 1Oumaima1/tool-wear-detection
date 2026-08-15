"""
Decision Engine (Phase 2).

Règle demandée :
    SI predicted_class == "dulled"
    ET confidence >= seuil configurable
    ET détecté sur N frames CONSÉCUTIVES pour le même outil
    ALORS créer une Alert, la sauvegarder, envoyer un email
    SINON continuer la surveillance sans rien faire.

Pour ne jamais spammer, une fois une alerte non résolue créée pour un outil,
on n'en recrée pas une nouvelle tant que l'opérateur ne l'a pas marquée comme
résolue (endpoint PATCH /alerts/{id}/resolve) — les nouvelles détections
"dulled" continuent d'être enregistrées dans Predictions, juste sans nouvel email.
"""
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.models.alert import Alert, AlertSeverity
from app.models.tool import Tool
from app.models.machine import Machine
from app.models.settings import PlatformSettings
from app.services.email_service import send_alert_email

logger = logging.getLogger("decision_engine")

RECOMMENDATIONS = {
    "dulled": "Remplacer l'outil de coupe immédiatement avant la prochaine pièce.",
    "used": "Surveiller l'outil : usure modérée, planifier un remplacement prochain.",
    "sharp": "Aucune action requise, outil en bon état.",
}


def _get_or_create_settings(db: Session) -> PlatformSettings:
    row = db.query(PlatformSettings).filter(PlatformSettings.id == 1).first()
    if not row:
        row = PlatformSettings(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


class DecisionEngine:
    def evaluate(self, db: Session, prediction: Prediction) -> Alert | None:
        """
        Appelé après chaque nouvelle Prediction sauvegardée.
        Retourne l'Alert créée si les conditions sont réunies, sinon None.
        """
        cfg = _get_or_create_settings(db)

        if prediction.predicted_class != "dulled":
            return None
        if prediction.confidence < cfg.confidence_threshold:
            logger.debug(
                "Dulled détecté mais confiance %.2f < seuil %.2f — pas d'alerte",
                prediction.confidence, cfg.confidence_threshold,
            )
            return None

        required = cfg.consecutive_detections_required

        # Ne pas re-notifier si une alerte est déjà active (non résolue) pour cet outil
        existing_open_alert = (
            db.query(Alert)
            .filter(Alert.tool_id == prediction.tool_id, Alert.resolved.is_(False))
            .first()
        )
        if existing_open_alert:
            logger.debug("Alerte déjà active pour tool_id=%s — pas de doublon", prediction.tool_id)
            return None

        # Vérifie les N dernières prédictions pour cet outil : toutes "dulled" + seuil respecté
        recent = (
            db.query(Prediction)
            .filter(Prediction.tool_id == prediction.tool_id)
            .order_by(Prediction.created_at.desc())
            .limit(required)
            .all()
        )
        if len(recent) < required:
            logger.debug(
                "Seulement %d/%d détections consécutives pour tool_id=%s",
                len(recent), required, prediction.tool_id,
            )
            return None

        all_consecutive_dulled = all(
            p.predicted_class == "dulled" and p.confidence >= cfg.confidence_threshold
            for p in recent
        )
        if not all_consecutive_dulled:
            return None

        # --- Conditions réunies : créer l'alerte ---
        tool = db.query(Tool).get(prediction.tool_id)
        machine = db.query(Machine).get(prediction.machine_id)

        alert = Alert(
            machine_id=prediction.machine_id,
            tool_id=prediction.tool_id,
            prediction_id=prediction.id,
            severity=AlertSeverity.critical,
            message=(
                f"Outil {tool.tool_identifier if tool else prediction.tool_id} détecté DULLED "
                f"sur {required} détections consécutives (confiance {prediction.confidence*100:.1f}%)."
            ),
            confidence=prediction.confidence,
        )
        db.add(alert)

        # Met aussi à jour le dernier statut connu de l'outil
        if tool:
            tool.last_status = "dulled"
            tool.last_inspection_at = datetime.utcnow()

        db.commit()
        db.refresh(alert)

        email_data = {
            "machine_id": prediction.machine_id,
            "machine_name": machine.name if machine else "N/A",
            "tool_id": prediction.tool_id,
            "tool_identifier": tool.tool_identifier if tool else str(prediction.tool_id),
            "predicted_class": prediction.predicted_class,
            "confidence": prediction.confidence,
            "date": prediction.created_at.strftime("%Y-%m-%d"),
            "time": prediction.created_at.strftime("%H:%M:%S"),
            "recommendation": RECOMMENDATIONS["dulled"],
        }
        sent = send_alert_email(email_data, cfg)
        alert.email_sent = sent
        db.commit()
        db.refresh(alert)

        logger.info(
            "ALERTE créée (id=%s) pour outil %s — email_sent=%s",
            alert.id, email_data["tool_identifier"], sent,
        )
        return alert


decision_engine = DecisionEngine()
