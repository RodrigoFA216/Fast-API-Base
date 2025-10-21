from fastapi import FastAPI
from app.router import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(router)
app.title = "API REST Segmentation endoscope application"
app.version = "1.0.0"

origins = [
    "http://127.0.0.1:8000/",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    status_code=200,
    response_description="Petición válida",
    tags=["Get", "Tests"],
)
def helloWorld():
    return {"message": "Hello"}