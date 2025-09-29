from pydantic import BaseModel

class TokenResponse(BaseModel):
    access_token: str

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    token: str = None