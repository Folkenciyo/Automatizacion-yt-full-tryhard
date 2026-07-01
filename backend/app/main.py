from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import audio_assets, channels, clips, health, niches, oauth, research, storyboards, video_projects

app = FastAPI(title="Automatización YT")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(niches.router)
app.include_router(channels.router)
app.include_router(research.router)
app.include_router(video_projects.router)
app.include_router(oauth.router)
app.include_router(clips.router)
app.include_router(audio_assets.router)
app.include_router(storyboards.router)
