from fastapi import FastAPI

from app.routers import group, group_type, site

app = FastAPI(title="Python technical test")

app.include_router(site.router)
app.include_router(group.router)
app.include_router(group_type.router)
