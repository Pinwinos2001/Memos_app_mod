from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()

# Minimal redirects to decoupled frontend locations
@router.get("/")
def home():
    return RedirectResponse(url="/portal/index.html")

@router.get("/form")
def form():
    return RedirectResponse(url="/portal/index.html")

@router.get("/edit/{id}")
def edit_page(id: str):
    return RedirectResponse(url=f"/edit/index.html?id={id}")

@router.get("/dashboard")
def dashboard():
    return RedirectResponse(url="/dashboard/index.html")

@router.get("/legal_review")
def legal_review(id: str):
    return RedirectResponse(url=f"/legal/review.html?id={id}")

@router.get("/review")
def rrhh_review(id: str):
    return RedirectResponse(url=f"/rrhh/review.html?id={id}")
