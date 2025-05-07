from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user, require_role
from app.schemas.user_schemas import UserCreate, UserResponse, UserUpdate, UserListResponse
from app.services.user_service import UserService
from app.services.email_service import EmailService
from app.utils.link_generation import create_user_links

router = APIRouter()

@router.post("/register/", response_model=UserResponse)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = await UserService.register_user(db, user.model_dump(), EmailService())
    if not new_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    return UserResponse.model_construct(
        id=new_user.id,
        email=new_user.email,
        nickname=new_user.nickname,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        bio=new_user.bio,
        profile_picture_url=new_user.profile_picture_url,
        linkedin_profile_url=new_user.linkedin_profile_url,
        github_profile_url=new_user.github_profile_url,
        is_professional=new_user.is_professional,
        role=new_user.role,
        links=create_user_links(new_user.id, None)
    )

@router.get("/users/", response_model=UserListResponse)
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    users = await UserService.get_all(db)
    user_responses = [
        UserResponse.model_construct(
            id=u.id,
            email=u.email,
            nickname=u.nickname,
            first_name=u.first_name,
            last_name=u.last_name,
            bio=u.bio,
            profile_picture_url=u.profile_picture_url,
            linkedin_profile_url=u.linkedin_profile_url,
            github_profile_url=u.github_profile_url,
            is_professional=u.is_professional,
            role=u.role,
            links=create_user_links(u.id, None)
        )
        for u in users
    ]
    return UserListResponse(items=user_responses, total=len(user_responses), page=1, size=len(user_responses))

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_construct(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        first_name=user.first_name,
        last_name=user.last_name,
        bio=user.bio,
        profile_picture_url=user.profile_picture_url,
        linkedin_profile_url=user.linkedin_profile_url,
        github_profile_url=user.github_profile_url,
        is_professional=user.is_professional,
        role=user.role,
        links=create_user_links(user.id, None)
    )

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    update_data = user_update.model_dump(exclude_unset=True)
    updated_user = await UserService.update(db, user_id=user_id, update_data=update_data)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_construct(
        id=updated_user.id,
        email=updated_user.email,
        nickname=updated_user.nickname,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        bio=updated_user.bio,
        profile_picture_url=updated_user.profile_picture_url,
        linkedin_profile_url=updated_user.linkedin_profile_url,
        github_profile_url=updated_user.github_profile_url,
        is_professional=updated_user.is_professional,
        role=updated_user.role,
        links=create_user_links(updated_user.id, None)
    )

@router.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = await UserService.get_by_email(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_construct(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        first_name=user.first_name,
        last_name=user.last_name,
        bio=user.bio,
        profile_picture_url=user.profile_picture_url,
        linkedin_profile_url=user.linkedin_profile_url,
        github_profile_url=user.github_profile_url,
        is_professional=user.is_professional,
        role=user.role,
        links=create_user_links(user.id, request)
    )

@router.patch("/users/me", response_model=UserResponse)
async def update_current_user_profile(
    request: Request,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if user_update.role is not None and current_user["role"] not in ["ADMIN", "MANAGER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
    update_data = user_update.model_dump(exclude_unset=True)
    updated_user = await UserService.update(db, user_id=UUID(str(current_user["user_id"])), update_data=update_data)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_construct(
        id=updated_user.id,
        email=updated_user.email,
        nickname=updated_user.nickname,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        bio=updated_user.bio,
        profile_picture_url=updated_user.profile_picture_url,
        linkedin_profile_url=updated_user.linkedin_profile_url,
        github_profile_url=updated_user.github_profile_url,
        is_professional=updated_user.is_professional,
        role=updated_user.role,
        links=create_user_links(updated_user.id, request)
    )
