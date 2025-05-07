from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy import update as sqlalchemy_update
from app.models.user_model import User
from app.services.email_service import EmailService
from uuid import UUID

class UserService:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: UUID):
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str):
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_data: dict, email_service: EmailService):
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        await email_service.send_verification_email(user)
        return user

    @staticmethod
    async def update(db: AsyncSession, user_id: UUID, update_data: dict):
        await db.execute(sqlalchemy_update(User).where(User.id == user_id).values(**update_data))
        await db.commit()
        return await UserService.get_by_id(db, user_id)

    @staticmethod
    async def delete(db: AsyncSession, user_id: UUID):
        user = await UserService.get_by_id(db, user_id)
        if not user:
            return False
        await db.delete(user)
        await db.commit()
        return True

    @staticmethod
    async def count(db: AsyncSession):
        result = await db.execute(select(User))
        return len(result.scalars().all())

    @staticmethod
    async def list_users(db: AsyncSession, skip: int = 0, limit: int = 10):
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def verify_email_with_token(db: AsyncSession, user_id: UUID, token: str):
        user = await UserService.get_by_id(db, user_id)
        if user and user.verification_token == token:
            user.email_verified = True
            user.role = "AUTHENTICATED"
            await db.commit()
            return True
        return False

    @staticmethod
    async def is_account_locked(db: AsyncSession, email: str):
        user = await UserService.get_by_email(db, email)
        return user.failed_attempts >= 5 if user else False

    @staticmethod
    async def login_user(db: AsyncSession, email: str, password: str):
        user = await UserService.get_by_email(db, email)
        if user and user.password == password:
            user.failed_attempts = 0
            await db.commit()
            return user
        elif user:
            user.failed_attempts += 1
            await db.commit()
        return None

    @staticmethod
    async def register_user(db: AsyncSession, user_data: dict, email_service: EmailService):
        existing = await UserService.get_by_email(db, user_data["email"])
        if existing:
            return None
        return await UserService.create(db, user_data, email_service)
