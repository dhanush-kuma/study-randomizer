"""Shared limits for CSV file uploads."""

from fastapi import HTTPException, UploadFile

MAX_CSV_BYTES = 1_048_576  # 1 MB


def ensure_csv_size(content: bytes) -> None:
    if len(content) > MAX_CSV_BYTES:
        max_kb = MAX_CSV_BYTES // 1024
        raise ValueError(f"CSV file exceeds the maximum size of {max_kb} KB.")


async def read_csv_upload_limited(file: UploadFile) -> bytes:
    """Read an uploaded CSV, rejecting files larger than MAX_CSV_BYTES."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(65536)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_CSV_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"CSV file exceeds the maximum size of {MAX_CSV_BYTES // 1024} KB.",
            )
        chunks.append(chunk)
    return b"".join(chunks)
