from config import PAGE_SIZE
from services.article_service import count_articles, get_article_by_id, get_articles_page


def _truncate(text, length=60):
    if not text:
        return ""
    text = text.replace("\n", " ")
    return text[:length] + "..." if len(text) > length else text


def _print_article(article, index):
    status_label = "Đã lấy nội dung" if article.status == 1 else "Mới (chỉ link)"
    source_name = article.source.name if article.source else "N/A"
    cat_name = article.category.name if article.category else "N/A"
    created = article.created_at.strftime("%d/%m/%Y %H:%M") if article.created_at else ""

    print(f"\n  STT {index} | ID: {article.id} | {status_label}")
    print(f"      Tiêu đề : {_truncate(article.title, 80)}")
    print(f"      Nguồn   : {source_name} | Danh mục: {cat_name}")
    print(f"      URL     : (xem đầy đủ trong chi tiết - phím D, ID {article.id})")
    print(f"      Tóm tắt : {_truncate(article.description, 100)}")
    print(f"      Ngày tạo: {created}")


def _resolve_article(articles_on_page, user_input):
    """Nhận STT (1-10) trên trang hiện tại hoặc ID trong database."""
    if not user_input.isdigit():
        return None

    value = int(user_input)
    if 1 <= value <= len(articles_on_page):
        return articles_on_page[value - 1]

    return get_article_by_id(value)


def articles_menu():
    page = 1
    total = count_articles()
    if total == 0:
        print("\nChưa có tin tức nào trong hệ thống.")
        return

    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    while True:
        articles = get_articles_page(page)
        print("\n" + "=" * 70)
        print(f"  DANH SÁCH TIN TỨC - Trang {page}/{total_pages} ({total} bài)")
        print("=" * 70)

        for idx, article in enumerate(articles, start=1):
            _print_article(article, idx)

        print("\n" + "-" * 70)
        print("  [N] Trang sau  |  [P] Trang trước  |  [D] Xem chi tiết  |  [0] Quay lại")
        nav = input("Chọn: ").strip().upper()

        if nav == "N":
            if page < total_pages:
                page += 1
            else:
                print("Đã ở trang cuối.")
        elif nav == "P":
            if page > 1:
                page -= 1
            else:
                print("Đã ở trang đầu.")
        elif nav == "D":
            _view_detail(articles)
        elif nav == "0":
            break
        else:
            print("Lựa chọn không hợp lệ. Gõ D rồi nhập STT/ID để xem chi tiết.")


def _fetch_content_now(article):
    from services.crawler import crawl_content_for_article
    from services.source_service import get_source
    from services.article_service import update_article_content

    source = get_source(article.source_id)
    if not source:
        print("Không tìm thấy nguồn tin của bài viết.")
        return article

    print("\nĐang lấy nội dung từ website, vui lòng đợi...")
    detail = crawl_content_for_article(article, source)
    if not detail:
        print("Không lấy được nội dung. Thử chạy Cronjob 2 trong menu Điều khiển Cronjob.")
        return article

    if update_article_content(article.id, detail):
        print("Đã cập nhật nội dung bài viết.")
        return get_article_by_id(article.id)

    return article


def _view_detail(articles_on_page):
    hint = f"1-{len(articles_on_page)}" if articles_on_page else "1"
    user_input = input(
        f"Nhập STT trên trang [{hint}] hoặc ID bài viết: "
    ).strip()

    if not user_input.isdigit():
        print("Giá trị không hợp lệ. Nhập số STT hoặc ID.")
        return

    article = _resolve_article(articles_on_page, user_input)
    if not article:
        print(f"Không tìm thấy bài viết với STT/ID = {user_input}.")
        return

    _print_detail(article)

    if article.status == 0 or not article.content:
        choice = input(
            "\nBài chưa có nội dung. Lấy ngay từ website? (Y/n): "
        ).strip().lower()
        if choice in ("", "y", "yes"):
            article = _fetch_content_now(article)
            print("\n" + "=" * 70)
            print("  CẬP NHẬT SAU KHI LẤY NỘI DUNG")
            print("=" * 70)
            _print_detail(article)

    open_browser = input("\nMở link trong trình duyệt? (y/N): ").strip().lower()
    if open_browser in ("y", "yes"):
        import webbrowser

        webbrowser.open(article.link)
        print("Đã gửi link tới trình duyệt.")

    input("\nNhấn Enter để quay lại danh sách...")


def _print_detail(article):
    source_name = article.source.name if article.source else "N/A"
    cat_name = article.category.name if article.category else "N/A"
    status_label = "Đã lấy nội dung" if article.status == 1 else "Chỉ có link (chưa crawl)"

    print("\n" + "=" * 70)
    print(f"  CHI TIẾT BÀI VIẾT (ID: {article.id})")
    print("=" * 70)
    print(f"Tiêu đề  : {article.title or '(Chưa có)'}")
    print(f"Nguồn    : {source_name}")
    print(f"Danh mục : {cat_name}")
    print(f"Trạng thái: {status_label}")
    print("-" * 70)
    print("LINK ĐẦY ĐỦ (copy dán vào trình duyệt):")
    print(article.link)
    print("-" * 70)
    print("TÓM TẮT:")
    print(article.description.strip() if article.description else "(Chưa có)")
    print("-" * 70)
    print("NỘI DUNG:")
    if article.content:
        content = article.content.strip()
        print(content[:3000] + ("..." if len(content) > 3000 else ""))
    else:
        print("(Chưa có — chạy Cronjob 2 hoặc chọn Y khi được hỏi để lấy nội dung)")
    print("=" * 70)
