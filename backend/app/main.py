import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.api import auth, parent, learning, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(title="英単語学習アプリ API")

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
origins = [o.strip() for o in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(parent.router)
app.include_router(learning.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"message": "英単語学習アプリ API"}
