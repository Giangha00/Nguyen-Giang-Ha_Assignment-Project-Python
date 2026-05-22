from services.source_service import (
    create_source,
    delete_source,
    get_source,
    list_categories,
    list_sources,
    update_source,
)

SELECTOR_FIELDS = [
    ("link_selector", "Trang danh sách - lấy link bài (vd: h3.title-news a)"),
    ("title_selector", "Trang chi tiết - tiêu đề (vd: h1.title-detail)"),
    ("description_selector", "Trang chi tiết - tóm tắt/sapo (có thể bỏ trống)"),
    ("content_selector", "Trang chi tiết - nội dung bài (vd: article.fck_detail)"),
    ("image_selector", "Trang chi tiết - ảnh (có thể bỏ trống)"),
]

SELECTOR_PRESETS = {
    "1": {
        "label": "VnExpress",
        "values": {
            "link_selector": "h3.title-news a",
            "title_selector": "h1.title-detail",
            "description_selector": "p.description",
            "content_selector": "article.fck_detail",
            "image_selector": "img.detail-img",
        },
    },
    "2": {
        "label": "Tuổi Trẻ",
        "values": {
            "link_selector": ".box-category-item h3 a, h2.title-news a",
            "title_selector": "h1.article-title",
            "description_selector": ".detail-sapo, h2.sapo",
            "content_selector": "motion.div.article-content, div.detail-content",
            "image_selector": "div.detail-photo img, .detail-photo img",
        },
    },
}

REQUIRED_SELECTOR_KEYS = ("link_selector", "title_selector", "content_selector")


def _input_int(prompt, allow_empty=False):
    while True:
        value = input(prompt).strip()
        if allow_empty and not value:
            return None
        if value.isdigit():
            return int(value)
        print("Vui lòng nhập số nguyên hợp lệ.")


def _show_categories():
    categories = list_categories()
    print("\n--- Danh mục ---")
    for cat in categories:
        print(f"  [{cat.id}] {cat.name}")
    return categories


def _show_sources(sources):
    print("\n" + "=" * 70)
    print(f"{'ID':<5}{'Tên nguồn':<28}{'Danh mục':<15}{'URL'}")
    print("-" * 70)
    for src in sources:
        cat_name = src.category.name if src.category else "N/A"
        url = src.link[:35] + "..." if len(src.link) > 38 else src.link
        name = src.name[:25] + "..." if len(src.name) > 28 else src.name
        print(f"{src.id:<5}{name:<28}{cat_name:<15}{url}")
    print("=" * 70)


def _show_source_detail(source):
    print("\n" + "=" * 70)
    print(f"  NGUỒN TIN ID: {source.id}")
    print("=" * 70)
    print(f"Tên       : {source.name}")
    print(f"URL       : {source.link}")
    print(f"Danh mục  : {source.category.name if source.category else 'N/A'}")
    print("-" * 70)
    print("CSS SELECTOR (dùng khi crawl):")
    for key, label in SELECTOR_FIELDS:
        value = getattr(source, key, None) or "(chưa có)"
        print(f"  {key}:")
        print(f"    → {value}")
    print("=" * 70)


def _choose_preset():
    print("\n--- Chọn mẫu selector (có thể sửa từng dòng sau) ---")
    print("  1. Mẫu VnExpress")
    print("  2. Mẫu Tuổi Trẻ")
    print("  3. Không dùng mẫu (tự nhập từ đầu)")
    choice = input("Chọn [1/2/3]: ").strip()
    if choice in SELECTOR_PRESETS:
        preset = SELECTOR_PRESETS[choice]
        print(f"  Đã chọn mẫu: {preset['label']}")
        return dict(preset["values"])
    return {}


def _prompt_selectors(current=None):
    """
    Cho phép người dùng nhập/sửa từng CSS selector.
    current: dict giá trị hiện có (khi sửa nguồn hoặc từ preset).
    """
    current = current or {}
    print("\n--- Nhập CSS selector ---")
    print("Gợi ý: Mở trang web → Inspect (F12) → copy selector.")
    print("Có thể nhập nhiều selector, cách nhau bằng dấu phẩy.")
    print("Bắt buộc: link_selector, title_selector, content_selector.\n")

    data = {}
    for key, hint in SELECTOR_FIELDS:
        old = current.get(key) or ""
        required = key in REQUIRED_SELECTOR_KEYS
        tag = " *" if required else " (Enter = bỏ trống)"

        while True:
            prompt = f"{key}{tag}\n  {hint}"
            if old:
                prompt += f"\n  Hiện tại [{old}]"
            value = input(f"{prompt}\n  Nhập: ").strip()

            if not value:
                if required and not old:
                    print("  → Trường bắt buộc, vui lòng nhập.")
                    continue
                data[key] = old or None
                break

            data[key] = value
            break

    return data


def add_source():
    print("\n--- THÊM NGUỒN TIN ---")
    categories = _show_categories()
    if not categories:
        print("Chưa có danh mục. Chạy init database trước.")
        return

    name = input("Tên nguồn: ").strip()
    if not name:
        print("Tên nguồn không được để trống.")
        return

    link = input("URL trang danh sách tin (trang chuyên mục): ").strip()
    if not link:
        print("URL không được để trống.")
        return

    category_id = _input_int("Chọn category_id: ")

    preset = _choose_preset()
    selectors = _prompt_selectors(preset)

    data = {
        "name": name,
        "link": link,
        "category_id": category_id,
        **selectors,
    }
    ok, message = create_source(data)
    if ok:
        print(message)
        print("Chạy Cronjob 1 (lấy link) rồi Cronjob 2 (lấy nội dung) trong menu Điều khiển Cronjob.")
    else:
        print(f"Lỗi: {message}")


def edit_source():
    sources = list_sources()
    if not sources:
        print("Chưa có nguồn tin nào.")
        return

    _show_sources(sources)
    source_id = _input_int("\nNhập ID nguồn cần sửa: ")
    source = get_source(source_id)
    if not source:
        print("Không tìm thấy nguồn tin.")
        return

    _show_source_detail(source)
    print("\nNhấn Enter để giữ nguyên giá trị hiện tại.")

    name = input(f"Tên [{source.name}]: ").strip()
    link = input(f"URL [{source.link}]: ").strip()

    _show_categories()
    cat_input = input(f"category_id [{source.category_id}]: ").strip()

    edit_selectors = input("Sửa CSS selector? (y/N): ").strip().lower() == "y"

    data = {}
    if name:
        data["name"] = name
    if link:
        data["link"] = link
    if cat_input.isdigit():
        data["category_id"] = int(cat_input)

    if edit_selectors:
        current = {
            "link_selector": source.link_selector,
            "title_selector": source.title_selector,
            "description_selector": source.description_selector,
            "content_selector": source.content_selector,
            "image_selector": source.image_selector,
        }
        preset = _choose_preset()
        merged = {**current, **preset}
        data.update(_prompt_selectors(merged))

    if not data:
        print("Không có thay đổi.")
        return

    ok, message = update_source(source_id, data)
    print(message if ok else f"Lỗi: {message}")


def remove_source():
    sources = list_sources()
    if not sources:
        print("Chưa có nguồn tin nào.")
        return

    _show_sources(sources)
    source_id = _input_int("\nNhập ID nguồn cần xóa: ")
    confirm = input("Xác nhận xóa? (y/N): ").strip().lower()
    if confirm != "y":
        print("Đã hủy.")
        return

    ok, message = delete_source(source_id)
    print(message if ok else f"Lỗi: {message}")


def view_sources():
    sources = list_sources()
    if not sources:
        print("Chưa có nguồn tin nào.")
        return

    while True:
        _show_sources(sources)
        print("\n  [D] Xem selector của nguồn  |  [0] Quay lại")
        choice = input("Chọn: ").strip().upper()
        if choice == "0":
            break
        if choice == "D":
            source_id = _input_int("Nhập ID nguồn: ")
            source = get_source(source_id)
            if source:
                _show_source_detail(source)
            else:
                print("Không tìm thấy nguồn tin.")
        else:
            print("Lựa chọn không hợp lệ.")


def sources_menu():
    while True:
        print("\n========== QUẢN LÝ NGUỒN TIN ==========")
        print("1. Xem danh sách")
        print("2. Thêm nguồn (nhập URL + CSS selector)")
        print("3. Sửa nguồn")
        print("4. Xóa nguồn")
        print("0. Quay lại")
        choice = input("Chọn: ").strip()

        if choice == "1":
            view_sources()
        elif choice == "2":
            add_source()
        elif choice == "3":
            edit_source()
        elif choice == "4":
            remove_source()
        elif choice == "0":
            break
        else:
            print("Lựa chọn không hợp lệ.")
