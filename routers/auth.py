from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from core.config import TEMPLATES
from services.auth import auth_service

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return TEMPLATES.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return TEMPLATES.TemplateResponse("register.html", {"request": request})

@router.post("/api/auth/register")
async def api_register(request: Request):
    data = await request.json()
    
    # Validation
    required = ['email', 'password', 'company_name', 'contact_person']
    for field in required:
        if not data.get(field):
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")
            
    try:
        result = auth_service.register_vendor(data)
        if not result:
             raise HTTPException(status_code=500, detail="Registration failed")
             
        return {
            "success": True,
            "token": result["token"],
            "name": result.get("name"),
            "role": result.get("role"),
            "user": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Registration Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/api/auth/login")
async def api_login(request: Request):
    data = await request.json()
    email = data.get("email", "")
    password = data.get("password", "")
    
    result = auth_service.authenticate(email, password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Return user data at top level for frontend localStorage
    return {
        "success": True, 
        "token": result["token"],
        "name": result.get("name"),
        "role": result.get("role"),
        "user": result
    }

@router.post("/api/auth/logout")
async def api_logout(request: Request):
    token = request.headers.get("Authorization")
    if token:
        auth_service.logout(token)
    return {"success": True}
