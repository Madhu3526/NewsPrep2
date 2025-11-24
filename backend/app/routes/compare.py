from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Model comparison placeholder")
def compare_root():
    return {"ok": True, "message": "Model compare endpoint placeholder"}
