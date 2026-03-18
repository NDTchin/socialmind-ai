import os
import time
import pandas as pd

from login import login
from posting import post_a_lot, post_selected_groups, post_to_selected_groups, prepare_image_paths
from scrape_groups import scrape_groups, save_groups_to_csv, load_groups_from_csv


# Thư mục gốc của project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")


def select_account(df_account):
    """Hiển thị danh sách tài khoản và cho user chọn."""
    print("\n" + "=" * 50)
    print("📋 DANH SÁCH TÀI KHOẢN")
    print("=" * 50)

    for i in range(df_account.shape[0]):
        email = df_account["Email"][i]
        print(f"  [{i}] {email}")

    print("-" * 50)

    while True:
        try:
            idx = int(input("👉 Chọn tài khoản (nhập số): "))
            if 0 <= idx < df_account.shape[0]:
                print(f"✅ Đã chọn: {df_account['Email'][idx]}")
                return idx
            else:
                print("❌ Số không hợp lệ, thử lại.")
        except ValueError:
            print("❌ Vui lòng nhập số.")


def select_group_source(driver):
    """Cho user chọn cách lấy danh sách nhóm."""
    print("\n" + "=" * 50)
    print("📂 CÁCH LẤY DANH SÁCH NHÓM")
    print("=" * 50)
    print("  [1] 🔍 Scrape từ Facebook (lấy nhóm đã tham gia)")
    print("  [2] 📄 Đọc từ file groups.csv có sẵn")
    print("-" * 50)

    while True:
        choice = input("👉 Chọn (1 hoặc 2): ").strip()

        if choice == "1":
            # Scrape nhóm từ Facebook
            groups = scrape_groups(driver)
            if not groups:
                print("❌ Không scrape được nhóm nào. Thử đọc từ CSV...")
                df_groups = load_groups_from_csv(os.path.join(DATA_DIR, "groups.csv"))
                return df_groups

            # Hỏi có muốn lưu vào CSV không
            save = input("💾 Lưu danh sách nhóm vào groups.csv? (y/n): ").strip().lower()
            if save == "y":
                df_groups = save_groups_to_csv(groups, os.path.join(DATA_DIR, "groups.csv"))
            else:
                df_groups = pd.DataFrame(groups)
            return df_groups

        elif choice == "2":
            # Đọc từ CSV
            df_groups = load_groups_from_csv(os.path.join(DATA_DIR, "groups.csv"))
            if df_groups is None:
                print("❌ Không thể đọc file. Vui lòng kiểm tra lại.")
                continue
            return df_groups

        else:
            print("❌ Chọn 1 hoặc 2.")


def select_groups(df_groups):
    """Hiển thị nhóm và cho user chọn một hoặc nhiều nhóm."""
    print("\n" + "=" * 50)
    print(f"📋 DANH SÁCH NHÓM ({df_groups.shape[0]} nhóm)")
    print("=" * 50)

    for i in range(df_groups.shape[0]):
        name = df_groups["Name group"][i]
        print(f"  [{i}] {name}")

    print("-" * 50)
    print("  Cách chọn:")
    print("    • Nhập 'all' → chọn tất cả nhóm")
    print("    • Nhập '0-10' → chọn nhóm từ 0 đến 10")
    print("    • Nhập '1,3,5,8' → chọn các nhóm cụ thể")
    print("    • Kết hợp: '0-5,8,12,20-25'")
    print("-" * 50)

    while True:
        choice = input("👉 Chọn nhóm: ").strip().lower()

        if choice == "all":
            indices = list(range(df_groups.shape[0]))
            print(f"✅ Đã chọn tất cả {len(indices)} nhóm")
            return indices

        try:
            indices = []
            parts = choice.split(",")
            for part in parts:
                part = part.strip()
                if "-" in part:
                    # Phạm vi: 0-10
                    start_str, end_str = part.split("-", 1)
                    start = int(start_str.strip())
                    end = int(end_str.strip())
                    for j in range(start, end + 1):
                        if 0 <= j < df_groups.shape[0] and j not in indices:
                            indices.append(j)
                else:
                    # Số đơn: 3
                    j = int(part)
                    if 0 <= j < df_groups.shape[0] and j not in indices:
                        indices.append(j)

            if indices:
                print(f"\n✅ Đã chọn {len(indices)} nhóm:")
                for i in indices:
                    print(f"    [{i}] {df_groups['Name group'][i]}")
                return indices
            else:
                print("❌ Không có nhóm hợp lệ, thử lại.")
        except ValueError:
            print("❌ Định dạng không hợp lệ. VD: all, 0-10, 1,3,5, hoặc 0-5,8,12")


def select_images():
    """Cho user chọn ảnh đính kèm."""
    print("\n" + "=" * 50)
    print("🖼️  CHỌN ẢNH ĐÍNH KÈM")
    print("=" * 50)

    # Liệt kê ảnh có sẵn
    available_images = []
    if os.path.exists(IMAGES_DIR):
        available_images = [f for f in os.listdir(IMAGES_DIR)
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]

    if available_images:
        print("  Ảnh có sẵn trong data/images/:")
        for i, img in enumerate(available_images):
            print(f"    [{i}] {img}")
        print()

    print("  [1] 📷 Dùng ảnh có sẵn (chọn từ danh sách trên)")
    print("  [2] ❌ Không đính kèm ảnh")
    print("-" * 50)

    choice = input("👉 Chọn (1 hoặc 2): ").strip()

    if choice == "1" and available_images:
        selected = input("👉 Nhập số thứ tự ảnh, cách nhau bằng dấu phẩy (VD: 0,1,2): ").strip()
        try:
            indices = [int(x.strip()) for x in selected.split(",")]
            image_paths = []
            for idx in indices:
                if 0 <= idx < len(available_images):
                    full_path = os.path.join(IMAGES_DIR, available_images[idx])
                    image_paths.append(full_path)
                    print(f"  ✅ {available_images[idx]}")
            if image_paths:
                return image_paths
        except ValueError:
            pass

    print("📝 Sẽ đăng bài không có ảnh.")
    return None


def main():
    print("\n" + "🚀" * 25)
    print("  FACEBOOK AUTO-POSTING TOOL")
    print("🚀" * 25)

    # Bước 1: Đọc dữ liệu tài khoản
    accounts_path = os.path.join(DATA_DIR, "accounts.csv")
    if not os.path.exists(accounts_path):
        print("❌ Không tìm thấy data/accounts.csv. Hãy tạo file này trước.")
        return

    df_account = pd.read_csv(accounts_path)
    if df_account.shape[0] == 0:
        print("❌ File accounts.csv rỗng.")
        return

    # Bước 2: Chọn tài khoản
    idx = select_account(df_account)

    # Bước 3: Đăng nhập
    print(f"\n🔐 Đang đăng nhập với {df_account['Email'][idx]}...")
    driver = login(
        email=df_account["Email"][idx],
        password=df_account["Password"][idx]
    )

    # Bước 4: Lấy danh sách nhóm
    df_groups = select_group_source(driver)
    if df_groups is None or df_groups.shape[0] == 0:
        print("❌ Không có nhóm nào để đăng bài.")
        driver.quit()
        return

    # Bước 5: Chọn nhóm
    selected_indices = select_groups(df_groups)

    # Bước 6: Nhập nội dung bài đăng
    print("\n" + "=" * 50)
    print("📝 NHẬP NỘI DUNG BÀI ĐĂNG")
    print("=" * 50)
    print("  Nhập nội dung bài viết (nhấn Enter 2 lần để kết thúc):")
    print("-" * 50)

    lines = []
    while True:
        line = input()
        if line == "":
            if lines and lines[-1] == "":
                lines.pop()  # Bỏ dòng trống cuối
                break
            lines.append(line)
        else:
            lines.append(line)

    content = "\n".join(lines)
    print(f"\n✅ Nội dung ({len(content)} ký tự):")
    print(f"  {content[:100]}{'...' if len(content) > 100 else ''}")

    # Bước 7: Chọn ảnh đính kèm
    print("\n" + "=" * 50)
    print("🖼️  CHỌN ẢNH ĐÍNH KÈM")
    print("=" * 50)
    print("  [1] 📷 Thêm ảnh từ máy tính (nhập đường dẫn file)")
    print("  [2] 🌐 Thêm ảnh từ URL")
    print("  [3] ❌ Không đính kèm ảnh")
    print("-" * 50)

    image_paths = None
    img_choice = input("👉 Chọn (1, 2 hoặc 3): ").strip()

    if img_choice == "1":
        # Ảnh từ máy tính
        print("  Nhập đường dẫn ảnh, mỗi đường dẫn 1 dòng.")
        print("  Nhấn Enter 2 lần để kết thúc.")
        print("  VÍ dụ: C:\\Users\\Admin\\Pictures\\anh1.jpg")
        print("-" * 50)
        raw = []
        while True:
            line = input("  🖼️  ").strip()
            if line == "":
                break
            raw.append(line)
        if raw:
            image_paths = prepare_image_paths(raw)
            if image_paths:
                print(f"\n✅ Đã chuẩn bị {len(image_paths)} ảnh.")

    elif img_choice == "2":
        # Ảnh từ URL
        print("  Nhập URL ảnh, mỗi URL 1 dòng.")
        print("  Nhấn Enter 2 lần để kết thúc.")
        print("  VÍ dụ: https://example.com/image.jpg")
        print("-" * 50)
        raw = []
        while True:
            line = input("  🌐 ").strip()
            if line == "":
                break
            raw.append(line)
        if raw:
            image_paths = prepare_image_paths(raw)
            if image_paths:
                print(f"\n✅ Đã tải và chuẩn bị {len(image_paths)} ảnh.")

    else:
        print("📝 Sẽ đăng bài không có ảnh.")

    # Bước 8: Xác nhận và bắt đầu
    print("\n" + "=" * 50)
    print("🚀 XÁC NHẬN")
    print("=" * 50)
    print(f"  📧 Tài khoản: {df_account['Email'][idx]}")
    print(f"  📋 Số nhóm: {len(selected_indices)}")
    print(f"  📝 Nội dung: {content[:50]}{'...' if len(content) > 50 else ''}")
    print(f"  🖼️  Ảnh: {len(image_paths) if image_paths else 'Không'}")
    print("-" * 50)

    confirm = input("👉 Bắt đầu đăng bài? (y/n): ").strip().lower()
    if confirm != "y":
        print("❌ Đã hủy.")
        driver.quit()
        return

    # Bắt đầu đăng bài
    print("\n🚀 Bắt đầu đăng bài...")
    post_to_selected_groups(
        driver=driver,
        df_gr=df_groups,
        content=content,
        indices=selected_indices,
        image_paths=image_paths
    )

    print("\n" + "✅" * 25)
    print("  HOÀN TẤT!")
    print("✅" * 25)

    time.sleep(5)
    driver.quit()


if __name__ == '__main__':
    main()
