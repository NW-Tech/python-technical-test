from fastapi import FastAPI
from infrastructure.routes import groups, sites

app = FastAPI(title="Python technical test")

app.include_router(sites.router)
app.include_router(groups.router)
