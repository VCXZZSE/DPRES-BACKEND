from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.email import send_sos_acknowledgement_email
from app.database import get_db
from app.models import SOSEvent, User, UserRole
from app.routes.auth import get_current_sdma_admin, get_current_user
from app.schemas import (
    SOSActiveEventOut,
    SOSActiveEventsResponse,
    SOSResolveCaseResponse,
    SOSResolvedEventsResponse,
    SOSActiveStudentDetails,
    SOSTriggerRequest,
    SOSTriggerResponse,
)

router = APIRouter(prefix='/api/sos', tags=['sos'])
admin_router = APIRouter(prefix='/api/admin', tags=['admin-sos'])

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

    normalized_location_text = payload.location_text.strip() if payload.location_text else None

    event = SOSEvent(
        user_id=current_user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_text=normalized_location_text,
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
        location_text=normalized_location_text,
        created_at_utc=event.created_at,
    )

    return SOSTriggerResponse(
        message='SOS sent successfully. Help is on the way.',
        event_id=event.id,
        created_at=event.created_at,
    )


@admin_router.get('/sos/active', response_model=SOSActiveEventsResponse)
def get_active_sos_events(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_sdma_admin),
) -> SOSActiveEventsResponse:
    rows = db.execute(
        select(SOSEvent, User)
        .join(User, User.id == SOSEvent.user_id)
        .where(SOSEvent.status == 'active')
        .order_by(SOSEvent.created_at.desc())
    ).all()

    events = [
        SOSActiveEventOut(
            event_id=event.id,
            status=event.status,
            latitude=event.latitude,
            longitude=event.longitude,
            location_text=event.location_text,
            accuracy_meters=event.accuracy_meters,
            created_at=event.created_at,
            resolved_at=event.resolved_at,
            student=SOSActiveStudentDetails(
                user_id=student.id,
                full_name=student.full_name,
                email=student.email,
                id_card_number=student.id_card_number,
            ),
        )
        for event, student in rows
    ]

    return SOSActiveEventsResponse(events=events)


@admin_router.get('/sos/resolved', response_model=SOSResolvedEventsResponse)
def get_resolved_sos_events(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_sdma_admin),
) -> SOSResolvedEventsResponse:
    rows = db.execute(
        select(SOSEvent, User)
        .join(User, User.id == SOSEvent.user_id)
        .where(SOSEvent.status == 'resolved')
        .order_by(SOSEvent.resolved_at.desc(), SOSEvent.created_at.desc())
        .limit(100)
    ).all()

    events = [
        SOSActiveEventOut(
            event_id=event.id,
            status=event.status,
            latitude=event.latitude,
            longitude=event.longitude,
            location_text=event.location_text,
            accuracy_meters=event.accuracy_meters,
            created_at=event.created_at,
            resolved_at=event.resolved_at,
            student=SOSActiveStudentDetails(
                user_id=student.id,
                full_name=student.full_name,
                email=student.email,
                id_card_number=student.id_card_number,
            ),
        )
        for event, student in rows
    ]

    return SOSResolvedEventsResponse(events=events)


@admin_router.post('/sos/{event_id}/resolve', response_model=SOSResolveCaseResponse)
def resolve_sos_event(
    event_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_sdma_admin),
) -> SOSResolveCaseResponse:
    row = db.execute(
        select(SOSEvent, User)
        .join(User, User.id == SOSEvent.user_id)
        .where(SOSEvent.id == event_id)
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='SOS event not found')

    event, student = row
    if event.status == 'resolved':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='SOS event already resolved')

    event.status = 'resolved'
    event.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(event)

    response_event = SOSActiveEventOut(
        event_id=event.id,
        status=event.status,
        latitude=event.latitude,
        longitude=event.longitude,
        location_text=event.location_text,
        accuracy_meters=event.accuracy_meters,
        created_at=event.created_at,
        resolved_at=event.resolved_at,
        student=SOSActiveStudentDetails(
            user_id=student.id,
            full_name=student.full_name,
            email=student.email,
            id_card_number=student.id_card_number,
        ),
    )

    return SOSResolveCaseResponse(message='SOS case resolved successfully', event=response_event)
