from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.auth import router as auth_router
from app.routes.sos import admin_router as admin_sos_router
from app.routes.sos import router as sos_router


app = FastAPI(title='DPRES Backend', version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r'^https://.*\.vercel\.app$',
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/')
def root() -> dict[str, str]:
    return {'message': 'Welcome to the DPRES Backend! We are live.'}


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


app.include_router(auth_router)
app.include_router(sos_router)
app.include_router(admin_sos_router)
