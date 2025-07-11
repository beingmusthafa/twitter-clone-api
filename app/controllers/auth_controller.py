from fastapi import APIRouter, HTTPException, Response, Request, Depends
from pydantic import ValidationError
from schemas.auth_schemas import UserRegistrationRequest, UserRegistrationResponse, UserLoginRequest, UserLoginResponse
from schemas.user_schemas import UserResponse
from services.auth_service import AuthService
from utils.auth_middleware import get_current_user
from utils.token_utils import verify_token, generate_tokens

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserRegistrationResponse)
async def register_user(request: Request, response: Response):
    try:
        body = await request.json()
        user_data = UserRegistrationRequest(**body)
        
        # Call service layer
        user_response, tokens = await AuthService.register_user(user_data)
        
        # Set secure cookies
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=30 * 60  # 30 minutes
        )
        
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return user_response
        
    except ValidationError as e:
        errors = {}
        for error in e.errors():
            field_name = error['loc'][-1] if error['loc'] else 'unknown'
            errors[field_name] = error['msg']
        raise HTTPException(status_code=400, detail={"errors": errors})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login", response_model=UserLoginResponse)
async def login_user(request: Request, response: Response):
    try:
        body = await request.json()
        user_data = UserLoginRequest(**body)
        
        # Call service layer
        user_response, tokens = await AuthService.login_user(user_data)
        
        # Set secure cookies
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=30 * 60  # 30 minutes
        )
        
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return user_response
        
    except ValidationError as e:
        errors = {}
        for error in e.errors():
            field_name = error['loc'][-1] if error['loc'] else 'unknown'
            errors[field_name] = error['msg']
        raise HTTPException(status_code=400, detail={"errors": errors})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/logout")
async def logout_user(request: Request, response: Response):
    try:
        # Get refresh token from cookies
        refresh_token = request.cookies.get("refresh_token")
        
        if refresh_token:
            # Blacklist the refresh token
            await AuthService.logout_user(refresh_token)
        
        # Clear cookies
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        # Still clear cookies even if blacklisting fails
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user=Depends(get_current_user)):
    try:
        return current_user
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/refresh")
async def refresh_token(request: Request, response: Response):
    try:
        # Get refresh token from cookies
        refresh_token = request.cookies.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token not found")
        
        # Verify the refresh token
        payload = await verify_token(refresh_token)
        
        # Check if it's a refresh token
        if payload["type"] != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Generate new tokens
        user_id = payload["user_id"]
        tokens = generate_tokens(user_id)
        
        # Set new cookies
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=30 * 60  # 30 minutes
        )
        
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return {"message": "Token refreshed successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")