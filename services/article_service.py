from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from config import PAGE_SIZE
from sql.init_sql import Article, get_session


def get_all_links():
    session = get_session()
    try:
        rows = session.query(Article.link).all()
        return {row[0] for row in rows}
    finally:
        session.close()


def save_new_articles(items, source):
    session = get_session()
    saved = 0
    try:
        for item in items:
            article = Article(
                link=item["link"],
                title=item["title"],
                description=None,
                content=None,
                image=None,
                status=0,
                category_id=source.category_id,
                source_id=source.id,
            )
            session.add(article)
            try:
                session.commit()
                saved += 1
            except IntegrityError:
                session.rollback()
        return saved
    finally:
        session.close()


def get_pending_articles(limit=20):
    session = get_session()
    try:
        return (
            session.query(Article)
            .filter(Article.status == 0)
            .order_by(Article.created_at.asc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()


def update_article_content(article_id, detail):
    session = get_session()
    try:
        article = session.query(Article).filter_by(id=article_id).first()
        if not article:
            return False
        if detail.get("title"):
            article.title = detail["title"]
        if detail.get("description"):
            article.description = detail["description"]
        if detail.get("content"):
            article.content = detail["content"]
        if detail.get("image"):
            article.image = detail["image"]
        article.status = 1
        session.commit()
        return True
    finally:
        session.close()


def count_articles():
    session = get_session()
    try:
        return session.query(Article).count()
    finally:
        session.close()


def get_articles_page(page=1, page_size=PAGE_SIZE):
    session = get_session()
    try:
        offset = (page - 1) * page_size
        return (
            session.query(Article)
            .options(joinedload(Article.category), joinedload(Article.source))
            .order_by(Article.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
    finally:
        session.close()


def get_article_by_id(article_id):
    session = get_session()
    try:
        return (
            session.query(Article)
            .options(joinedload(Article.category), joinedload(Article.source))
            .filter_by(id=article_id)
            .first()
        )
    finally:
        session.close()
