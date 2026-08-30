from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"csp_nonce": getattr(request.state, "csp_nonce", "")},
    )


@router.get("/result", response_class=HTMLResponse)
async def result(request: Request, username: str = ""):
    if not username:
        return HTMLResponse("<h2>Error: No username provided. <a href='/'>Go Back</a></h2>", status_code=400)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "username": username,
            "csp_nonce": getattr(request.state, "csp_nonce", ""),
        },
    )
