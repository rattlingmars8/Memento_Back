from enum import Enum


class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    VERIFY = "verify"
    FORGOT = "forgot"
