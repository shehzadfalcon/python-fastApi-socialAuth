from enum import Enum


class Steps(Enum):
    USER_REGISTER = "USER_REGISTER"
    VERIFY_EMAIL = "VERIFY_EMAIL"
    SET_PASSWORD = "SET_PASSWORD"
    SETUP_PASSWORD = "setup_password"
    ACCOUNT_LINKING = "ACCOUNT_LINKING"
