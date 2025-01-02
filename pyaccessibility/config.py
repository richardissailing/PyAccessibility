from typing import Optional
import os


class Config:
    SMTP_HOST: Optional[str] = os.getenv("PYACCESSIBILITY_SMTP_HOST")
    SMTP_PORT: Optional[int] = (
        int(os.getenv("PYACCESSIBILITY_SMTP_PORT", "0")) or None
    )
    SMTP_USER: Optional[str] = os.getenv("PYACCESSIBILITY_SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("PYACCESSIBILITY_SMTP_PASSWORD")
