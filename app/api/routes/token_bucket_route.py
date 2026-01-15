import socket

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.routes.dependencies.token_bucket_dependency import enforce_token_bucket_rate_limit

router = APIRouter(tags=["rate-limited"])


@router.get("/token-bucket", dependencies=[Depends(enforce_token_bucket_rate_limit)])
async def rate_limited_endpoint():
    return JSONResponse(
        content={
            "message": "Request successful",
            "handled_by": socket.gethostname()
        }
    )
