from fastapi import FastAPI

app = FastAPI(title="Lenny Growth Assistant Backend")


@app.get("/health")
def health_check():
    return {"status": "ok"}
