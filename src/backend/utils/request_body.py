"""Read a file sent as the raw request body, so uploads don't need a multipart dependency."""

from fastapi import HTTPException


async def read_limited_body(request, max_bytes, too_large_detail, empty_detail):
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > max_bytes:
            raise HTTPException(status_code=413, detail=too_large_detail)
        body.extend(chunk)
    if not body:
        raise HTTPException(status_code=422, detail=empty_detail)
    return bytes(body)
