from __future__ import annotations

import os
from typing import Any, Optional, List

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict

from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, Session

# --- Import your SQLAlchemy models ---
# Put this file next to models.py (the one you pasted in the prompt)
from models import Base, User, Group, GroupMember

# -----------------------------
# Database & Session setup
# -----------------------------
# Use a PostgreSQL URL like:
#   postgresql+psycopg://user:password@localhost:5432/mydb
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:root@localhost:5432/voice_face_rag")

engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

app = FastAPI(title="Users/Groups API", version="1.0.0")


# -------------------------------------
# DB utilities
# -------------------------------------

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    """Ensure required extensions/types and create tables."""
    # pgvector extension is required by models. It's safe to run conditionally.
    with engine.begin() as conn:
        try:
            conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector;")
        except Exception:
            # If the connected DB role cannot create extensions, ignore — as long as the extension exists.
            pass
        # Create tables if they don't exist
        Base.metadata.create_all(bind=conn)


# -----------------------------
# Pydantic Schemas (v2 style)
# -----------------------------

class UserCreate(BaseModel):
    name: str = Field(..., max_length=100)
    profile_json: Optional[dict[str, Any]] = Field(default_factory=dict)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    profile_json: dict[str, Any]
    created_at: Any
    updated_at: Any


class GroupCreate(BaseModel):
    name: str = Field(..., max_length=100)


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    group_id: int
    name: str
    created_at: Any
    updated_at: Any


class GroupMemberAdd(BaseModel):
    user_id: int
    role: str = Field(default="member", max_length=50)


class GroupMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    group_id: int
    user_id: int
    role: str
    joined_at: Any
    # Convenience: embed basic user info when listing members
    user: Optional[UserOut] = None


# -----------------------------
# Routes
# -----------------------------

@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# Users
@app.post("/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(name=payload.name, profile_json=payload.profile_json or {})
    db.add(user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # Likely unique violation on name
        raise HTTPException(status_code=400, detail="User with this name already exists.")
    db.refresh(user)
    return user


@app.get("/users", response_model=List[UserOut])
def list_users(
        db: Session = Depends(get_db),
        offset: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
):
    users = db.execute(select(User).offset(offset).limit(limit)).scalars().all()
    return users


@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Groups
@app.post("/groups", response_model=GroupOut, status_code=201)
def create_group(payload: GroupCreate, db: Session = Depends(get_db)):
    group = Group(name=payload.name)
    db.add(group)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Group with this name already exists.")
    db.refresh(group)
    return group


@app.get("/groups", response_model=List[GroupOut])
def list_groups(
        db: Session = Depends(get_db),
        offset: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
):
    groups = db.execute(select(Group).offset(offset).limit(limit)).scalars().all()
    return groups


@app.get("/groups/{group_name}", response_model=GroupOut)
def get_group_by_name(group_name: str, db: Session = Depends(get_db)):
    group = db.execute(select(Group).where(Group.name == group_name)).scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


# Group Members
@app.post("/groups/{group_id}/members", response_model=GroupMemberOut, status_code=201)
def add_member(group_id: int, payload: GroupMemberAdd, db: Session = Depends(get_db)):
    # Validate user & group exist
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    gm = GroupMember(group_id=group_id, user_id=payload.user_id, role=payload.role)
    db.add(gm)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="This user is already a member of the group.")

    # load back with joined user for convenience
    db.refresh(gm)
    out = GroupMemberOut(
            group_id=gm.group_id,
            user_id=gm.user_id,
            role=gm.role,
            joined_at=gm.joined_at,
            user=user,
    )
    return out


@app.get("/groups/{group_id}/members", response_model=List[GroupMemberOut])
def list_members(
        group_id: int,
        db: Session = Depends(get_db),
        offset: int = Query(0, ge=0),
        limit: int = Query(200, ge=1, le=1000),
):
    # Verify group
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Join to users so we can embed user info in the response
    stmt = (
            select(GroupMember, User)
            .join(User, User.user_id == GroupMember.user_id)
            .where(GroupMember.group_id == group_id)
            .offset(offset)
            .limit(limit)
    )
    rows = db.execute(stmt).all()
    results: List[GroupMemberOut] = []
    for gm, user in rows:
        results.append(
                GroupMemberOut(
                        group_id=gm.group_id,
                        user_id=gm.user_id,
                        role=gm.role,
                        joined_at=gm.joined_at,
                        user=user,
                )
        )
    return results


# Optional convenience: see which groups a user belongs to
@app.get("/users/{user_id}/groups", response_model=List[GroupOut])
def groups_for_user(
        user_id: int,
        db: Session = Depends(get_db),
        offset: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
):
    # Validate user
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = (
            select(Group)
            .join(GroupMember, GroupMember.group_id == Group.group_id)
            .where(GroupMember.user_id == user_id)
            .offset(offset)
            .limit(limit)
    )
    groups = db.execute(stmt).scalars().all()
    return groups


# -------------------------------------
# Error handlers (optional sugar)
# -------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# -------------------------------------
# Local dev entrypoint
# -------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
