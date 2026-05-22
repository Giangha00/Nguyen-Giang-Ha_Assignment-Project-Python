import threading
import time
from datetime import datetime

import schedule

from config import CONTENT_CRON_INTERVAL_MINUTES, LINK_CRON_TIME
from services.article_service import (
    get_all_links,
    get_pending_articles,
    save_new_articles,
    update_article_content,
)
from services.crawler import crawl_content_for_article, crawl_links_for_source
from services.source_service import get_source, list_sources


class CronManager:
    def __init__(self):
        self._enabled = False
        self._thread = None
        self._stop_event = threading.Event()

    @property
    def enabled(self):
        return self._enabled

    def job_fetch_links(self):
        print(f"\n[Cronjob 1] Lấy danh sách link - {datetime.now():%Y-%m-%d %H:%M:%S}")
        sources = list_sources()
        if not sources:
            print("  Không có nguồn tin nào.")
            return

        existing_links = get_all_links()
        total_saved = 0
        for source in sources:
            items = crawl_links_for_source(source, existing_links)
            if items:
                saved = save_new_articles(items, source)
                total_saved += saved
                for item in items[:saved]:
                    existing_links.add(item["link"])
        print(f"[Cronjob 1] Hoàn tất. Đã lưu {total_saved} bài mới.\n")

    def job_fetch_content(self):
        print(f"\n[Cronjob 2] Lấy nội dung chi tiết - {datetime.now():%Y-%m-%d %H:%M:%S}")
        pending = get_pending_articles(limit=30)
        if not pending:
            print("  Không có bài nào cần lấy nội dung.")
            return

        updated = 0
        for article in pending:
            source = get_source(article.source_id)
            if not source:
                continue
            detail = crawl_content_for_article(article, source)
            if detail and update_article_content(article.id, detail):
                updated += 1
        print(f"[Cronjob 2] Hoàn tất. Đã cập nhật {updated} bài.\n")

    def _run_scheduler_loop(self):
        while not self._stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)

    def start(self):
        if self._enabled:
            print("Cronjob đã đang chạy.")
            return

        schedule.clear()
        schedule.every().day.at(LINK_CRON_TIME).do(self.job_fetch_links)
        schedule.every(CONTENT_CRON_INTERVAL_MINUTES).minutes.do(self.job_fetch_content)

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_scheduler_loop, daemon=True)
        self._thread.start()
        self._enabled = True
        print(
            f"Đã BẬT cronjob: Link lúc {LINK_CRON_TIME} hàng ngày, "
            f"Nội dung mỗi {CONTENT_CRON_INTERVAL_MINUTES} phút."
        )

    def stop(self):
        if not self._enabled:
            print("Cronjob chưa được bật.")
            return

        self._stop_event.set()
        schedule.clear()
        self._enabled = False
        print("Đã TẮT cronjob.")

    def status(self):
        state = "ĐANG CHẠY" if self._enabled else "ĐÃ TẮT"
        print(f"\nTrạng thái cronjob: {state}")
        print(f"  - Cronjob 1 (link): hàng ngày lúc {LINK_CRON_TIME}")
        print(
            f"  - Cronjob 2 (nội dung): mỗi {CONTENT_CRON_INTERVAL_MINUTES} phút"
        )
        if self._enabled:
            jobs = schedule.get_jobs()
            print(f"  - Số tác vụ đang lên lịch: {len(jobs)}")


cron_manager = CronManager()
