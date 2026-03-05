import uvicorn
from app.main import app

if __name__ == "__main__":
    #uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ssl_keyfile="private.key",      # путь к твоему ключу
        ssl_certfile="cert_manager_VGLTU.crt"  # путь к сертификату
    )