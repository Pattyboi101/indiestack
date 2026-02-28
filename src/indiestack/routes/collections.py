"""Collections — merged into Stacks. These routes provide 301 redirects."""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/collections")
async def collections_redirect():
    return RedirectResponse(url="/stacks", status_code=301)


@router.get("/collection/{slug}")
async def collection_detail_redirect(slug: str):
    return RedirectResponse(url="/stacks", status_code=301)
