"""Recently added tools — redirects to /explore?sort=newest."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/new")
async def new_tools(request: Request):
    return RedirectResponse(url="/explore?sort=newest", status_code=302)
