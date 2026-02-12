import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models import User, Word, ChildProgress
from app.auth import hash_password, create_access_token

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def parent_user(db):
    user = db.query(User).filter(User.username == "testparent").first()
    if not user:
        user = User(
            email="parent@test.com",
            username="testparent",
            hashed_password=hash_password("parentpass"),
            role="parent",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def parent_token(parent_user):
    return create_access_token(data={"sub": parent_user.username})


@pytest.fixture
def parent_headers(parent_token):
    return {"Authorization": f"Bearer {parent_token}"}


@pytest.fixture
def child_user(db, parent_user):
    user = db.query(User).filter(User.username == "testchild").first()
    if not user:
        user = User(
            username="testchild",
            hashed_password=hash_password("childpass"),
            role="child",
            parent_id=parent_user.id,
        )
        db.add(user)
        db.flush()
        progress = ChildProgress(child_id=user.id)
        db.add(progress)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def child_token(child_user):
    return create_access_token(data={"sub": child_user.username})


@pytest.fixture
def child_headers(child_token):
    return {"Authorization": f"Bearer {child_token}"}


@pytest.fixture
def child_id(child_user):
    return child_user.id


@pytest.fixture
def sample_words(db):
    existing = db.query(Word).filter(Word.english == "apple").first()
    if existing:
        return db.query(Word).filter(Word.section.in_([1, 2])).all()
    words = [
        Word(english="apple", japanese="りんご", english_katakana="アップル", section=1),
        Word(english="banana", japanese="バナナ", english_katakana="バナナ", section=1),
        Word(english="cat", japanese="猫", english_katakana="キャット", section=1),
        Word(english="dog", japanese="犬", english_katakana="ドッグ", section=2),
        Word(english="egg", japanese="卵", english_katakana="エッグ", section=2),
    ]
    db.add_all(words)
    db.commit()
    for w in words:
        db.refresh(w)
    return words
