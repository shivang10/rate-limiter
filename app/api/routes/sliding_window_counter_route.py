import socket

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.routes.dependencies.sliding_window_counter_dependency import enforce_sliding_window_counter_rate_limit

router = APIRouter(tags=["rate-limited"])


@router.get("/sliding-window-counter", dependencies=[Depends(enforce_sliding_window_counter_rate_limit)])
async def rate_limited_endpoint():
    return JSONResponse(
        content={
            "message": "Request successful",
            "handled_by": socket.gethostname()
        }
    )
