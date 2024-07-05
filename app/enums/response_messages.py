from enum import Enum


class EResponseMessages(Enum):
    # User messagess
    USER_CREATED = "User created successfully"
    USER_LOGIN = "User logged in successfully"
    USER_IDENTIFIED = "User identified"
    USER_UPDATED = "User updated"
    USER_VERIFIED = "User verified"
    PROFILE_FETCHED = "Profile fetched"
    PROFILE_UPDATED = "Profile updated"
    USER_STATUS_UPDATED = "User status updated"
    IMAGE_UPDATED = "Image updated"
    USERS_FETCHED = "Users fetched"
    PASSWORD_RESET = "Password reset successfully"

    # Password messages
    PASSWORD_UPDATED = "Password updated"
    PASSWORD_RESET_EMAIL = "Password reset email sent"

    # OTP messages
    OTP_VERIFIED = "OTP verified"
    OTP_RESEND = "OTP resend request submitted"

    # Email
    VERIFY_EMAIL_SUBJECT = "Verify your email"
    FORGOT_PASSWORD_EMAIL_SUBJECT = "Reset your password"
