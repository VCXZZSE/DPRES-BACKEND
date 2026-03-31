from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.email import send_sos_acknowledgement_email
from app.database import get_db
from app.models import SOSEvent, User, UserRole
from app.routes.auth import get_current_user
from app.schemas import SOSTriggerRequest, SOSTriggerResponse

router = APIRouter(prefix='/api/sos', tags=['sos'])

SOS_COOLDOWN_SECONDS = 60


@router.post('/trigger', response_model=SOSTriggerResponse, status_code=status.HTTP_201_CREATED)
def trigger_sos(
    payload: SOSTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SOSTriggerResponse:
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Student access required')

    now = datetime.now(timezone.utc)
    cooldown_at = now - timedelta(seconds=SOS_COOLDOWN_SECONDS)

    recent_active_event = db.scalar(
        select(SOSEvent)
        .where(
            and_(
                SOSEvent.user_id == current_user.id,
                SOSEvent.status == 'active',
                SOSEvent.created_at > cooldown_at,
            )
        )
        .order_by(SOSEvent.created_at.desc())
    )
    if recent_active_event:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail='SOS already sent recently. Please wait a moment before retrying.',
        )

    event = SOSEvent(
        user_id=current_user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_text=payload.location_text,
        accuracy_meters=payload.accuracy_meters,
        status='active',
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    background_tasks.add_task(
        send_sos_acknowledgement_email,
        to_email=current_user.email,
        user_name=current_user.full_name,
        event_id=event.id,
        location_text=payload.location_text,
        created_at_utc=event.created_at,
    )

    return SOSTriggerResponse(
        message='SOS sent successfully. Help is on the way.',
        event_id=event.id,
        created_at=event.created_at,
    )
