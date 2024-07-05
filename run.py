from app.main import app
import uvicorn
from dotenv import load_dotenv
import os

load_dotenv()

host = os.getenv("HOST")

port = int(os.getenv("PORT"))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=host, port=port, reload=True)
