import random
import re
import time
import pandas as pd
from selenium.webdriver.common.by import By


def clean_group_name(raw_text):
    """Làm sạch tên nhóm: bỏ 'Lần hoạt động gần nhất:...' và metadata thừa."""
    lines = raw_text.strip().split("\n")
    clean_lines = []
    for line in lines:
        line = line.strip()
        if "hoạt động gần nhất" in line.lower():
            continue
        if "last active" in line.lower():
            continue
        if re.match(r'^(khoảng\s+)?\d+\s+(giờ|phút|ngày|tuần|tháng|năm|giây)', line.lower()):
            continue
        if "vài giây trước" in line.lower():
            continue
        if line:
            clean_lines.append(line)
    return " ".join(clean_lines).strip() if clean_lines else ""


def scrape_groups(driver):
    """
    Scrape danh sách nhóm đã tham gia từ Facebook.
    Dùng URL desktop + scroll để load hết tất cả nhóm.
    Trả về list các dict: [{'Name group': ..., 'Link group': ...}, ...]
    """
    groups = []
    seen_links = set()

    url = "https://www.facebook.com/groups/joins/?nav_source=tab"

    print("\n🔍 Đang scrape danh sách nhóm từ Facebook...")
    print(f"  🔗 URL: {url}")

    driver.get(url)
    time.sleep(random.randint(4, 6))

    print(f"  📄 URL hiện tại: {driver.current_url}")

    # Cuộn trang để load hết tất cả nhóm
    last_count = 0
    no_change_count = 0
    max_no_change = 5  # Dừng nếu 5 lần cuộn liên tiếp không tìm thêm nhóm mới

    scroll_round = 0
    while no_change_count < max_no_change:
        scroll_round += 1

        # Tìm tất cả link nhóm trên trang hiện tại
        all_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/groups/"]')

        for link_elem in all_links:
            try:
                href = link_elem.get_attribute("href") or ""
                raw_text = link_elem.text.strip()

                # Kiểm tra link nhóm hợp lệ
                if not is_valid_group_link(href):
                    continue

                # Làm sạch tên nhóm: bỏ "Lần hoạt động gần nhất: ..." và metadata thừa
                clean_name = clean_group_name(raw_text)

                # Bỏ nếu tên rỗng hoặc quá ngắn
                if not clean_name or len(clean_name) < 3:
                    continue

                # Bỏ nếu tên là thời gian
                if re.match(r'^\d+\s+(giờ|phút|ngày|tuần|tháng|năm|giây|hour|minute|day|week|month|year)', clean_name.lower()):
                    continue

                # Chuẩn hóa link
                normalized_link = normalize_group_link(href)

                # Tránh trùng lặp
                if normalized_link not in seen_links:
                    seen_links.add(normalized_link)
                    groups.append({
                        'Name group': clean_name,
                        'Link group': normalized_link
                    })

            except Exception:
                continue

        current_count = len(groups)

        if current_count > last_count:
            print(f"  📊 Lần cuộn {scroll_round}: tìm được {current_count} nhóm (+{current_count - last_count} mới)")
            last_count = current_count
            no_change_count = 0
        else:
            no_change_count += 1

        # Cuộn xuống cuối trang
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.randint(2, 4))

    print(f"\n{'='*50}")
    print(f"✅ Hoàn tất! Đã scrape được tổng cộng {len(groups)} nhóm.")
    print(f"{'='*50}")

    if len(groups) == 0:
        print("💡 Không scrape được nhóm nào.")
        print("   Hãy thử dùng option [2] để đọc từ file groups.csv có sẵn.")

    return groups


def is_valid_group_link(href):
    """Kiểm tra xem link có phải là link nhóm hợp lệ hay không."""
    if not href or "/groups/" not in href:
        return False

    # Bỏ các link hệ thống
    skip_patterns = [
        "/groups/join", "/groups/create", "/groups/discover",
        "/groups/feed", "/groups/search", "/groups/notifications",
        "/groups/yours", "/groups/browse",
        "category=", "nav_source=",
        "/user/", "/posts/", "/permalink/", "/comment/",
        "/photo/", "/videos/", "/media/", "/events/",
        "/members/", "/about/", "/files/",
    ]

    href_lower = href.lower()
    for pattern in skip_patterns:
        if pattern in href_lower:
            return False

    # Phải match: /groups/<id_or_slug>
    match = re.search(r'/groups/([^/?#]+)', href)
    if not match:
        return False

    group_id = match.group(1)
    if len(group_id) < 2 or group_id in ["joins", "feed", "discover", "create", "search", "yours", "browse"]:
        return False

    return True


def normalize_group_link(href):
    """Chuẩn hóa link nhóm."""
    link = href.replace("mbasic.facebook.com", "www.facebook.com")
    link = link.replace("m.facebook.com", "www.facebook.com")

    match = re.search(r'(https://www\.facebook\.com/groups/[^/?#]+)', link)
    if match:
        link = match.group(1)

    if not link.endswith("/"):
        link += "/"

    return link


def save_groups_to_csv(groups, filepath="./data/groups.csv"):
    """Lưu danh sách nhóm vào file CSV."""
    df = pd.DataFrame(groups)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"💾 Đã lưu {len(groups)} nhóm vào {filepath}")
    return df


def load_groups_from_csv(filepath="./data/groups.csv"):
    """Đọc danh sách nhóm từ file CSV có sẵn."""
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
        print(f"📂 Đã đọc {df.shape[0]} nhóm từ {filepath}")
        return df
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file {filepath}")
        return None
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        return None
