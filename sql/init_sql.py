from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DB_URL = "mysql+pymysql://root:@localhost:3306/news_management"
engine = create_engine(DB_URL, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

CATEGORY_SEEDS = [
    "Công nghệ",
    "Kinh doanh",
    "Thể thao",
    "Giải trí",
    "Thời sự",
    "Sức khỏe",
]

DEFAULT_SOURCES = [
    {
        "name": "VnExpress - Công nghệ",
        "link": "https://vnexpress.net/cong-nghe",
        "link_selector": "h3.title-news a",
        "title_selector": "h1.title-detail",
        "description_selector": "p.description",
        "content_selector": "article.fck_detail",
        "image_selector": "img.detail-img",
        "category_name": "Công nghệ",
    },
    {
        "name": "Tuổi Trẻ - Thể thao",
        "link": "https://tuoitre.vn/the-thao.htm",
        "link_selector": ".box-category-item h3 a, h2.title-news a",
        "title_selector": "h1.article-title",
        "description_selector": ".detail-sapo, h2.sapo",
        "content_selector": "motion.div.article-content, div.detail-content",
        "image_selector": "motion.div.detail-photo img, div.detail-photo img",
        "category_name": "Thể thao",
    },
]


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)

    articles = relationship("Article", back_populates="category")
    sources = relationship("Source", back_populates="category")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    link = Column(Text, nullable=False)
    link_selector = Column(Text, nullable=True)
    title_selector = Column(Text, nullable=True)
    description_selector = Column(Text, nullable=True)
    content_selector = Column(Text, nullable=True)
    image_selector = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    category = relationship("Category", back_populates="sources")
    articles = relationship("Article", back_populates="source")


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("link", name="uq_article_link"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    link = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    image = Column(Text, nullable=True)
    status = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)

    category = relationship("Category", back_populates="articles")
    source = relationship("Source", back_populates="articles")


def get_session():
    return SessionLocal()


def seed_categories(session):
    for name in CATEGORY_SEEDS:
        exists = session.query(Category).filter_by(name=name).first()
        if not exists:
            session.add(Category(name=name))
    session.commit()


def seed_default_sources(session):
    for item in DEFAULT_SOURCES:
        category = session.query(Category).filter_by(name=item["category_name"]).first()
        if not category:
            continue
        exists = session.query(Source).filter_by(link=item["link"]).first()
        if exists:
            exists.link_selector = item["link_selector"]
            exists.title_selector = item["title_selector"]
            exists.description_selector = item["description_selector"]
            exists.content_selector = item["content_selector"]
            exists.image_selector = item["image_selector"]
            continue
        session.add(
            Source(
                name=item["name"],
                link=item["link"],
                link_selector=item["link_selector"],
                title_selector=item["title_selector"],
                description_selector=item["description_selector"],
                content_selector=item["content_selector"],
                image_selector=item["image_selector"],
                category_id=category.id,
            )
        )
    session.commit()


def create_database_if_not_exists():
    import pymysql

    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS news_management "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()


def init_database():
    create_database_if_not_exists()
    Base.metadata.create_all(engine)
    session = get_session()
    try:
        seed_categories(session)
        seed_default_sources(session)
        print("Database 'news_management' initialized successfully.")
    finally:
        session.close()


if __name__ == "__main__":
    init_database()
