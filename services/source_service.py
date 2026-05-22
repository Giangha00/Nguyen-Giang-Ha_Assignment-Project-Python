from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from sql.init_sql import Category, Source, get_session


def list_categories():
    session = get_session()
    try:
        return session.query(Category).order_by(Category.id).all()
    finally:
        session.close()


def list_sources():
    session = get_session()
    try:
        return (
            session.query(Source)
            .options(joinedload(Source.category))
            .order_by(Source.id)
            .all()
        )
    finally:
        session.close()


def get_source(source_id):
    session = get_session()
    try:
        return (
            session.query(Source)
            .options(joinedload(Source.category))
            .filter_by(id=source_id)
            .first()
        )
    finally:
        session.close()


def category_exists(category_id):
    session = get_session()
    try:
        return session.query(Category).filter_by(id=category_id).first() is not None
    finally:
        session.close()


def create_source(data):
    if not data.get("name") or not data.get("link"):
        return False, "Tên nguồn và URL không được để trống."
    if not category_exists(data["category_id"]):
        return False, "Danh mục không tồn tại."

    missing = [
        key
        for key in ("link_selector", "title_selector", "content_selector")
        if not (data.get(key) or "").strip()
    ]
    if missing:
        return (
            False,
            "Thiếu selector bắt buộc: "
            + ", ".join(missing)
            + ". Cần nhập để crawl được tin từ nguồn mới.",
        )

    session = get_session()
    try:
        source = Source(
            name=data["name"].strip(),
            link=data["link"].strip(),
            link_selector=data.get("link_selector"),
            title_selector=data.get("title_selector"),
            description_selector=data.get("description_selector"),
            content_selector=data.get("content_selector"),
            image_selector=data.get("image_selector"),
            category_id=data["category_id"],
        )
        session.add(source)
        session.commit()
        return True, "Thêm nguồn tin thành công."
    except IntegrityError:
        session.rollback()
        return False, "Không thể thêm nguồn tin (dữ liệu không hợp lệ)."
    finally:
        session.close()


def update_source(source_id, data):
    session = get_session()
    try:
        source = session.query(Source).filter_by(id=source_id).first()
        if not source:
            return False, "Không tìm thấy nguồn tin."

        if "category_id" in data and not category_exists(data["category_id"]):
            return False, "Danh mục không tồn tại."

        for field in (
            "name",
            "link",
            "link_selector",
            "title_selector",
            "description_selector",
            "content_selector",
            "image_selector",
            "category_id",
        ):
            if field in data and data[field] is not None:
                value = data[field]
                if isinstance(value, str):
                    value = value.strip()
                setattr(source, field, value)

        session.commit()
        return True, "Cập nhật nguồn tin thành công."
    except IntegrityError:
        session.rollback()
        return False, "Cập nhật thất bại."
    finally:
        session.close()


def delete_source(source_id):
    session = get_session()
    try:
        source = session.query(Source).filter_by(id=source_id).first()
        if not source:
            return False, "Không tìm thấy nguồn tin."
        session.delete(source)
        session.commit()
        return True, "Xóa nguồn tin thành công."
    except IntegrityError:
        session.rollback()
        return False, "Không thể xóa (còn bài viết liên quan)."
    finally:
        session.close()
