import sys
import asyncio
from typing import List
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
from typing import List, Optional
# Local imports
import models
from database import engine
from scraper import scrape_all
from schemas import UserCreate, UserResponse, Token
from auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Windows fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="SaaS Price Tracker API")

# Create tables
models.Base.metadata.create_all(bind=engine)

# CORS (Required for Blazor/MAUI to talk to FastAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- REQUEST MODELS --------
  # Added so users can set a target price when saving
class BulkSaveItem(BaseModel):
    product_id: int
    target_price: Optional[float] = None
class BulkSaveRequest(BaseModel):
    items: List[BulkSaveItem]
# -------- AUTHENTICATION ROUTES --------

@app.post("/signup", response_model=UserResponse)
def create_user(user: UserCreate):
    if not user.email.lower().endswith("@gmail.com"):
        raise HTTPException(status_code=400, detail="Please use a valid @gmail.com address for deal alerts.")
    
    with Session(engine) as session:
        # 1. Check if email is already taken
        db_user = session.query(models.User).filter(models.User.email == user.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # 2. Hash the password and save
        hashed_pw = get_password_hash(user.password)
        new_user = models.User(email=user.email, hashed_password=hashed_pw)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        return new_user


@app.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        # 1. Find User
        user = session.query(models.User).filter(models.User.email == form_data.username).first()
        
        # 2. Verify Password
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 3. Generate Token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}


# -------- SCRAPER & SEARCH ROUTES --------

@app.post("/search/{keyword}")
async def start_search(
    keyword: str, 
    background_tasks: BackgroundTasks, 
    max_price: Optional[float] = None,  # Explicitly optional
    current_user: models.User = Depends(get_current_user)
):
    # Log it to verify what the backend is receiving
    print(f"Search: {keyword}, Max Price: {max_price}")

    with Session(engine) as session:
        # Cleanup logic remains same...
        session.query(models.Product).filter(
            models.Product.is_saved == False,
            models.Product.user_id == current_user.id
        ).delete()
        session.commit()

    mission_id = int(asyncio.get_event_loop().time())

    # Pass max_price to the scraper (ensure scraper.py handles None)
    background_tasks.add_task(scrape_all, mission_id, keyword, max_price, current_user.id)

    return {"mission_id": mission_id}


@app.get("/results/{mission_id}")
async def get_results(
    mission_id: int,
    current_user: models.User = Depends(get_current_user) # SECURED
):
    with Session(engine) as session:
        # Only return results that belong to the user requesting them
        return session.query(models.Product).filter(
            models.Product.mission_id == mission_id,
            models.Product.user_id == current_user.id
        ).all()


# -------- CART & TRACKING ROUTES --------

@app.post("/cart/bulk-save")
async def bulk_save(
    request: BulkSaveRequest,
    current_user: models.User = Depends(get_current_user)
):
    with Session(engine) as session:
        saved_count = 0
        
        for item in request.items:
            # Look up the product by ID and ensure it belongs to the current user
            product = session.query(models.Product).filter(
                models.Product.id == item.product_id,
                models.Product.user_id == current_user.id
            ).first()
            
            if product:
                product.is_saved = True
                # Set the specific target price for this product
                product.target_price = item.target_price
                saved_count += 1
                
        session.commit()

    return {"message": f"Successfully tracking {saved_count} items."}


@app.get("/cart")
async def get_cart(current_user: models.User = Depends(get_current_user)): # SECURED
    with Session(engine) as session:
        # Return only the saved cart items for the currently logged-in user
        return session.query(models.Product).filter(
            models.Product.is_saved == True,
            models.Product.user_id == current_user.id
        ).all()
    
@app.get("/product/{product_id}/history")
async def get_product_history(product_id: int, current_user: models.User = Depends(get_current_user)):
    with Session(engine) as session:
        # 1. Verify the user owns this product
        product = session.query(models.Product).filter(
            models.Product.id == product_id,
            models.Product.user_id == current_user.id
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        # 2. Fetch the history, sorted by date (oldest to newest for the graph)
        history = session.query(models.PriceHistory).filter(
            models.PriceHistory.product_id == product_id
        ).order_by(models.PriceHistory.timestamp.asc()).all()
        
        return history