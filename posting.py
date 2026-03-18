import os
import random
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time


TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "temp_images")


def download_image(url, save_dir=None):
    """
    Download ảnh từ URL và lưu vào thư mục tạm.
    Trả về đường dẫn tuyệt đối của file đã tải.
    """
    if save_dir is None:
        save_dir = TEMP_DIR

    os.makedirs(save_dir, exist_ok=True)

    # Tạo tên file từ URL
    filename = url.split("/")[-1].split("?")[0]
    if not filename or "." not in filename:
        filename = f"image_{random.randint(1000, 9999)}.jpg"

    filepath = os.path.join(save_dir, filename)

    try:
        print(f"  ⬇️ Đang tải ảnh: {url[:80]}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"  ✅ Đã tải: {filename} ({len(response.content) // 1024}KB)")
        return os.path.abspath(filepath)
    except Exception as e:
        print(f"  ❌ Lỗi tải ảnh: {e}")
        return None


def prepare_image_paths(raw_paths):
    """
    Xử lý danh sách đường dẫn ảnh: nếu là URL thì download, nếu là file local thì giữ nguyên.
    Trả về list đường dẫn tuyệt đối.
    """
    prepared = []
    for path in raw_paths:
        path = path.strip()
        if not path:
            continue

        if path.startswith("http://") or path.startswith("https://"):
            # Download ảnh từ URL
            local_path = download_image(path)
            if local_path:
                prepared.append(local_path)
        else:
            # File local - chuyển thành đường dẫn tuyệt đối
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                prepared.append(abs_path)
            else:
                print(f"  ❌ Không tìm thấy file: {abs_path}")

    return prepared


def upload_images(driver, image_paths, dialog=None):
    """
    Upload ảnh vào bài viết bằng input[type='file'].
    Không cần PyAutoGUI, hoạt động ổn định và headless.
    """
    if not image_paths:
        return

    # Tìm input[type="file"] ẩn trên trang (Facebook dùng để upload ảnh)
    search_context = dialog if dialog else driver
    file_input = None

    try:
        # Facebook thường có input file ẩn trong dialog
        file_input = search_context.find_element(By.CSS_SELECTOR, 'input[type="file"][accept*="image"]')
    except NoSuchElementException:
        try:
            file_input = driver.find_element(By.CSS_SELECTOR, 'input[type="file"][accept*="image"]')
        except NoSuchElementException:
            pass

    if not file_input:
        # Click nút "Ảnh/video" để làm input file xuất hiện
        photo_btn = None
        try:
            if dialog:
                photo_btn = dialog.find_element(By.CSS_SELECTOR, '[aria-label="Ảnh/video"]')
            else:
                photo_btn = driver.find_element(By.CSS_SELECTOR, '[aria-label="Ảnh/video"]')
        except NoSuchElementException:
            try:
                photo_btn = driver.find_element(By.CSS_SELECTOR, '[aria-label="Photo/video"]')
            except NoSuchElementException:
                pass

        if photo_btn:
            photo_btn.click()
            time.sleep(random.randint(1, 2))

        # Thử tìm lại input file
        try:
            file_input = driver.find_element(By.CSS_SELECTOR, 'input[type="file"][accept*="image"]')
        except NoSuchElementException:
            try:
                # Fallback: tìm bất kỳ input file nào
                file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                if file_inputs:
                    file_input = file_inputs[0]
            except Exception:
                pass

    if not file_input:
        print("  ❌ Không tìm thấy input upload ảnh.")
        return

    # Upload tất cả ảnh cùng lúc (join paths bằng \n)
    all_paths = "\n".join(image_paths)
    file_input.send_keys(all_paths)
    print(f"  ✅ Đã upload {len(image_paths)} ảnh.")

    # Chờ ảnh được xử lý
    time.sleep(random.randint(3, 5))


def find_element_with_fallback(driver, selectors, wait_time=10):
    """
    Thử tìm element bằng nhiều selector khác nhau.
    Trả về element đầu tiên tìm được, hoặc None nếu không tìm thấy.
    """
    wait = WebDriverWait(driver, wait_time)
    for method, selector in selectors:
        try:
            element = wait.until(EC.element_to_be_clickable((method, selector)))
            return element
        except TimeoutException:
            continue
    return None


def posts(driver, link, content, name_gr, image_paths=None):
    """
    Đăng 1 bài vào 1 nhóm Facebook.
    Selector dựa trên Facebook Comet UI (2025).
    """
    driver.get(link)
    time.sleep(random.randint(3, 5))

    wait = WebDriverWait(driver, 15)

    # ===== Bước 1: Click vào ô tạo bài viết =====
    # Trên trang nhóm, ô này chứa text "Bạn viết gì đi..."
    create_btn = None
    create_selectors = [
        (By.XPATH, '//div[@role="button"]//span[contains(text(), "Bạn viết gì đi")]'),
        (By.XPATH, '//span[contains(text(), "Bạn viết gì đi")]'),
        (By.XPATH, '//span[contains(text(), "Bạn đang nghĩ gì")]'),
        (By.XPATH, '//span[contains(text(), "Write something")]'),
    ]

    for method, selector in create_selectors:
        try:
            create_btn = wait.until(EC.element_to_be_clickable((method, selector)))
            break
        except TimeoutException:
            continue

    if not create_btn:
        print(f"❌ Không tìm thấy ô tạo bài:\n    - Nhóm: {name_gr}\n    - URL: {link}")
        return driver

    try:
        create_btn.click()
        print(f"  ✅ Đã click ô tạo bài.")
    except Exception as e:
        print(f"  ❌ Lỗi click: {e}")
        return driver

    time.sleep(random.randint(3, 5))

    # ===== Bước 2: Chờ dialog mở ra =====
    dialog = None
    try:
        dialog = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'div[role="dialog"]')
        ))
        print(f"  ✅ Dialog tạo bài đã mở.")
    except TimeoutException:
        print(f"  ⚠️ Không thấy dialog, thử tìm textbox trực tiếp...")

    # ===== Bước 3: Tìm textbox nhập nội dung =====
    text_input = None

    # Cách 1: Tìm trong dialog bằng aria-placeholder chính xác
    if dialog:
        try:
            text_input = dialog.find_element(
                By.CSS_SELECTOR, 'div[role="textbox"][aria-placeholder="Bạn viết gì đi..."]'
            )
        except NoSuchElementException:
            pass

        # Cách 2: Tìm bất kỳ textbox nào trong dialog
        if not text_input:
            try:
                text_input = dialog.find_element(
                    By.CSS_SELECTOR, 'div[role="textbox"][contenteditable="true"]'
                )
            except NoSuchElementException:
                pass

    # Cách 3: Fallback - tìm trên toàn trang bằng aria-placeholder
    if not text_input:
        try:
            text_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[role="textbox"][aria-placeholder="Bạn viết gì đi..."]')
            ))
        except TimeoutException:
            pass

    if not text_input:
        print(f"  ❌ Không tìm thấy ô nhập nội dung:\n    - Nhóm: {name_gr}\n    - URL: {link}")
        return driver

    # Nhập nội dung
    time.sleep(1)
    text_input.click()
    time.sleep(1)
    text_input.send_keys(content)
    print(f"  ✅ Đã nhập nội dung ({len(content)} ký tự).")

    # ===== Bước 4: Thêm ảnh nếu có =====
    if image_paths and len(image_paths) > 0:
        time.sleep(random.randint(1, 2))
        upload_images(driver, image_paths, dialog=dialog)

    # ===== Bước 5: Nhấn nút Đăng =====
    time.sleep(random.randint(2, 3))

    post_btn = None

    # Tìm nút Đăng trong dialog trước (chính xác hơn)
    if dialog:
        try:
            post_btn = dialog.find_element(By.CSS_SELECTOR, 'div[aria-label="Đăng"][role="button"]')
        except NoSuchElementException:
            try:
                post_btn = dialog.find_element(By.CSS_SELECTOR, 'div[aria-label="Post"][role="button"]')
            except NoSuchElementException:
                pass

    # Fallback: tìm trên toàn trang
    if not post_btn:
        post_btn = find_element_with_fallback(driver, [
            (By.CSS_SELECTOR, 'div[aria-label="Đăng"][role="button"]'),
            (By.CSS_SELECTOR, 'div[aria-label="Post"][role="button"]'),
            (By.XPATH, '//div[@aria-label="Đăng"]'),
            (By.XPATH, '//span[text()="Đăng"]/ancestor::div[@role="button"]'),
        ], wait_time=8)

    if not post_btn:
        print(f"  ⚠️ Không tìm thấy nút Đăng:\n    - Nhóm: {name_gr}\n    - URL: {link}")
        return driver

    post_btn.click()
    print(f"✅ Đăng bài thành công:\n    - Nhóm: {name_gr}\n    - URL: {link}")


    return driver


def post_a_lot(driver, df_gr, df_ct, start, end, image_paths=None):
    """
    Đăng bài vào nhiều nhóm từ start đến end.
    - image_paths: list đường dẫn ảnh đính kèm (tùy chọn).
    """
    for i in range(start, end):
        print(f'\n<-------> Đăng bài nhóm {i + 1}/{end} <------->')
        driver = posts(
            driver=driver,
            link=df_gr['Link group'][i],
            content=df_ct["Content"][random.randint(0, df_ct.shape[0] - 1)],
            name_gr=df_gr["Name group"][i],
            image_paths=image_paths
        )

    return driver


def post_selected_groups(driver, df_gr, df_ct, indices, image_paths=None):
    """
    Đăng bài vào các nhóm theo danh sách index, nội dung random từ DataFrame.
    """
    total = len(indices)
    for count, i in enumerate(indices, 1):
        print(f'\n<-------> Đăng bài {count}/{total} - Nhóm [{i}] <------->')
        driver = posts(
            driver=driver,
            link=df_gr['Link group'][i],
            content=df_ct["Content"][random.randint(0, df_ct.shape[0] - 1)],
            name_gr=df_gr["Name group"][i],
            image_paths=image_paths
        )

    return driver


def post_to_selected_groups(driver, df_gr, content, indices, image_paths=None):
    """
    Đăng bài vào các nhóm theo danh sách index, nội dung do user nhập.
    - content: string nội dung bài viết
    - indices: list số thứ tự nhóm đã chọn
    """
    total = len(indices)
    for count, i in enumerate(indices, 1):
        print(f'\n<-------> Đăng bài {count}/{total} - Nhóm [{i}] <------->')
        driver = posts(
            driver=driver,
            link=df_gr['Link group'][i],
            content=content,
            name_gr=df_gr["Name group"][i],
            image_paths=image_paths
        )

    return driver


