from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, patients

app = FastAPI(title="Intussusception Detection Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
