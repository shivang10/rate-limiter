import socket
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.routes.dependencies.token_bucket_dependency import token_bucket_rate_limit_dependency

router = APIRouter(tags=["rate-limited"])


@router.get("/token-bucket", dependencies=[Depends(token_bucket_rate_limit_dependency)])
async def token_bucket_endpoint():
    return JSONResponse(
        content={
            "message": "Request successful",
            "handled_by": socket.gethostname()
        }
    )
