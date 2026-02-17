from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uuid, qrcode, os
from collections import defaultdict

app = FastAPI()

# ---- folders (absolute paths, Windows-safe) ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)

# ---- mount static ----
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

rooms = defaultdict(list)

# ---- PC page ----
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    token = str(uuid.uuid4())[:6]

    # IMPORTANT: use LAN IP later for phone testing
    url = f"http://127.0.0.1:8000/{token}"

    img = qrcode.make(url)

    file_path = os.path.join(STATIC_DIR, f"{token}.png")
    img.save(file_path)

    return templates.TemplateResponse(
        "pc.html",
        {
            "request": request,
            "token": token,
            "qr": f"/static/{token}.png"
        }
    )

# ---- phone page ----
@app.get("/{token}", response_class=HTMLResponse)
async def join(request: Request, token: str):
    return templates.TemplateResponse(
        "phone.html",
        {"request": request, "token": token}
    )

# ---- websocket ----
@app.websocket("/ws/{token}")
async def ws(ws: WebSocket, token: str):
    await ws.accept()
    rooms[token].append(ws)
    try:
        while True:
            data = await ws.receive_text()
            for client in rooms[token]:
                if client != ws:
                    await client.send_text(data)
    except:
        rooms[token].remove(ws)
