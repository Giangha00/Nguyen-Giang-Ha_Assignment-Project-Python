from services.scheduler import cron_manager


def cronjob_menu():
    while True:
        print("\n========== ĐIỀU KHIỂN CRONJOB ==========")
        print("1. Xem trạng thái")
        print("2. Bật cronjob tự động")
        print("3. Tắt cronjob tự động")
        print("4. Chạy thủ công: Lấy danh sách link (Cronjob 1)")
        print("5. Chạy thủ công: Lấy nội dung chi tiết (Cronjob 2)")
        print("0. Quay lại")
        choice = input("Chọn: ").strip()

        if choice == "1":
            cron_manager.status()
        elif choice == "2":
            cron_manager.start()
        elif choice == "3":
            cron_manager.stop()
        elif choice == "4":
            cron_manager.job_fetch_links()
        elif choice == "5":
            cron_manager.job_fetch_content()
        elif choice == "0":
            break
        else:
            print("Lựa chọn không hợp lệ.")
