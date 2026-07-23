from fastapi import FastAPI

app = FastAPI(
    title="SATCO Platform API",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "SATCO Platform API is running",
        "status": "ok"
    }