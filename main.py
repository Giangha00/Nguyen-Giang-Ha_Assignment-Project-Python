import sys

from cli.articles_menu import articles_menu
from cli.cronjob_menu import cronjob_menu
from cli.sources_menu import sources_menu
from sql.init_sql import init_database


def print_banner():
    print("\n" + "=" * 50)
    print("   HỆ THỐNG NEWS AGGREGATOR (CLI)")
    print("   Python + MySQL + Schedule")
    print("=" * 50)


def main_menu():
    while True:
        print("\n---------- MENU CHÍNH ----------")
        print("1. Quản lý nguồn tin (Sources)")
        print("2. Xem tin tức (Articles)")
        print("3. Điều khiển Cronjob")
        print("0. Thoát")
        choice = input("Chọn chức năng: ").strip()

        if choice == "1":
            sources_menu()
        elif choice == "2":
            articles_menu()
        elif choice == "3":
            cronjob_menu()
        elif choice == "0":
            from services.scheduler import cron_manager

            cron_manager.stop()
            print("Tạm biệt!")
            sys.exit(0)
        else:
            print("Lựa chọn không hợp lệ.")


if __name__ == "__main__":
    print_banner()
    try:
        init_database()
    except Exception as exc:
        print(f"Lỗi kết nối database: {exc}")
        print("Kiểm tra MySQL đang chạy và database 'news_management' đã được tạo.")
        sys.exit(1)

    main_menu()
