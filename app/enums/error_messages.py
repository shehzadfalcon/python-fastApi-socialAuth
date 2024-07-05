from enum import Enum


class EErrorMessages(Enum):
    ACCOUNT_LINKING = "Account linking required"

    # User errors
    ACCOUNT_EXISTS = "An account with this email already exists"
    USER_NOT_EXISTS = "User not found"
    USER_NOT_VERIFIED = "Email is not verified yet. Please check your email."
    USER_ALREADY_EXISTS = "User already exists"
    INVALID_EMAIL = "Invalid email address"
    EMAIL_NOT_VERIFIED = "Email not verified"

    # Chat
    CONVERSATION_ID_NOT_EXISTS = "Conversation ID not found"

    # OTP errors
    INVALID_OTP = "Invalid OTP"
    OTP_EXPIRED = "OTP has expired"
    REUSE_OTP = "OTP has already been used"

    # Password errors
    INVALID_PASSWORD = "Invalid password"
    INVALID_OLD_PASSWORD = "Invalid old password"

    # Token errors
    INVALID_TOKEN = "Invalid token"
    UNAUTHORIZED_USER = "Unauthorized user"
    UNAUTHORIZED_ACCESS = "Unauthorized access"
    TOKEN_EXPIRED = "Token has expired"

    # System error
    SYSTEM_ERROR = "System error"
