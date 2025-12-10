# admin/admin_app.py
# Простая админ-панель на FastAPI с просмотром последних сообщений и ошибок и с возможностью изменить deltas.
# Для production совет: поставить HTTP Basic auth / TLS / nginx.

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import config
from app import db
import base64
from typing import Optional

app = FastAPI()
templates = Jinja2Templates(directory="admin/templates")

# Простейшая Basic Auth (не безопасно для интернета — используйте TLS)
def check_auth(request: Request):
    auth = request.headers.get("Authorization")
    expected = "Basic " + base64.b64encode(f"{config.ADMIN_BASIC_USERNAME}:{config.ADMIN_BASIC_PASSWORD}".encode()).decode()
    if auth != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, auth: Optional[str] = Depends(check_auth)):
    msgs = await db.get_recent_messages(50)
    errors = await db.get_recent_errors(50)
    setting_pro = await db.get_setting("price_pro_delta", config.PRICE_PRO_DELTA)
    setting_default = await db.get_setting("price_default_delta", config.PRICE_DEFAULT_DELTA)
    return templates.TemplateResponse("index.html", {"request": request, "messages": msgs, "errors": errors, "price_pro": setting_pro, "price_default": setting_default})

@app.post("/update_deltas")
async def update_deltas(request: Request, price_pro: str = Form(...), price_default: str = Form(...), auth: Optional[str] = Depends(check_auth)):
    await db.set_setting("price_pro_delta", price_pro)
    await db.set_setting("price_default_delta", price_default)
    return RedirectResponse(url="/", status_code=303)

def run_admin():
    uvicorn.run("admin.admin_app:app", host=config.ADMIN_BIND_HOST, port=config.ADMIN_BIND_PORT, reload=False)

if __name__ == "__main__":
    run_admin()
