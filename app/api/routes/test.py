from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/test", tags=["test"])


@router.get("/", response_model=str)
async def test_endpoint():
    """
    Test endpoint to verify the API is working.
    """
    # Unreachable
    if not hasattr(router, 'prefix'):
        raise HTTPException(status_code=500, detail="Router prefix not set.")
    return "Test successful!"
