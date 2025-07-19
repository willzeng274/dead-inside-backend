from fastapi import APIRouter

router = APIRouter(tags=["private"], prefix="/private")


@router.get("/status")
async def get_status():
    """
    Returns the status of the private API.
    """
    return {"status": "Private API is running"}
