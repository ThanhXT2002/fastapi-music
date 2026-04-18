"""Schema response chung cho toan bo API.

Dinh nghia cau truc response chuan de dam bao nhat quan
giua tat ca endpoint (song, auth, ytmusic, v.v.).

Tuong duong voi ApiResponse<T> tren Frontend (Angular + React Native).
"""

# ── Standard library imports ──────────────────────────────
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

# ── Third-party imports ───────────────────────────────────
from pydantic import BaseModel, Field, model_serializer

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Response chuan cho tat ca API endpoint.

    Format nhat quan voi mobile (React Native) va web (Angular):
    {
        "status": true,
        "code": 200,
        "data": {...},
        "message": "...",
        "errors": null,
        "timestamp": "2024-01-01T00:00:00Z"
    }

    Attributes:
        status: True = thanh cong, False = that bai.
        code: HTTP-like status code (200, 400, 401, 404, 500...).
        data: Du lieu tra ve (nullable khi that bai).
        message: Thong bao mo ta ket qua.
        errors: Chi tiet loi validation (nullable, dung khi 422).
        timestamp: Thoi diem xu ly request (ISO 8601 UTC).
    """

    status: bool
    code: int
    data: T | None = None
    message: str | None = None
    errors: Any | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def ok(
        cls,
        data: Any = None,
        message: str = "Thành công",
        code: int = 200,
    ) -> "ApiResponse":
        """Tao response thanh cong nhanh.

        Args:
            data: Du lieu tra ve.
            message: Thong bao thanh cong.
            code: HTTP status code (mac dinh 200).

        Returns:
            ApiResponse voi status=True.

        Example:
            return ApiResponse.ok(data=song_data, message="Lay thong tin thanh cong")
        """
        return cls(status=True, code=code, data=data, message=message)

    @classmethod
    def fail(
        cls,
        message: str = "Đã xảy ra lỗi",
        code: int = 400,
        errors: Any = None,
    ) -> "ApiResponse":
        """Tao response that bai nhanh.

        Args:
            message: Thong bao loi.
            code: HTTP status code (mac dinh 400).
            errors: Chi tiet loi (validation errors, v.v.).

        Returns:
            ApiResponse voi status=False.

        Example:
            return ApiResponse.fail(message="Khong tim thay bai hat", code=404)
        """
        return cls(status=False, code=code, data=None, message=message, errors=errors)
