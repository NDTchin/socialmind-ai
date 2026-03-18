import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import time
from webdriver_manager.chrome import ChromeDriverManager

def login(email, password):
    facebook_url = "https://www.facebook.com"

    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--lang=vi")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.set_window_size(1000, 800)
    driver.set_window_position(10, 10)

    driver.get(facebook_url)

    wait = WebDriverWait(driver, 15)

    # Xử lý popup cookie nếu có
    try:
        cookie_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button[@data-cookiebanner="accept_button"] | //button[contains(text(), "Allow")] | //button[contains(text(), "Cho phép")] | //button[contains(text(), "Accept")]')
        ))
        cookie_btn.click()
        print("🍪 Đã chấp nhận cookie.")
        time.sleep(random.randint(1, 2))
    except TimeoutException:
        # Không có popup cookie → tiếp tục
        pass

    # Tìm và điền email
    try:
        email_input = wait.until(EC.presence_of_element_located((By.ID, 'email')))
        email_input.clear()
        email_input.send_keys(email)
    except TimeoutException:
        print("❌ Không tìm thấy ô nhập email. Có thể Facebook đã thay đổi giao diện.")
        print("⏳ Hãy thử đăng nhập thủ công trong cửa sổ Chrome...")
        input("👉 Nhấn Enter sau khi đã đăng nhập xong...")
        return driver

    # Tìm và điền password
    try:
        password_input = wait.until(EC.presence_of_element_located((By.ID, 'pass')))
        password_input.clear()
        password_input.send_keys(password)
        password_input.send_keys(Keys.ENTER)
    except TimeoutException:
        print("❌ Không tìm thấy ô nhập mật khẩu.")
        input("👉 Nhấn Enter sau khi đã đăng nhập xong...")
        return driver

    # Chờ đăng nhập
    print("⏳ Đang đăng nhập, chờ trang tải...")
    time.sleep(random.randint(8, 10))

    # Kiểm tra đăng nhập thành công (kiểm tra có bị checkpoint không)
    current_url = driver.current_url
    if "checkpoint" in current_url or "login" in current_url:
        print("⚠️ Facebook yêu cầu xác minh (checkpoint/2FA).")
        print("⏳ Hãy xác minh thủ công trong cửa sổ Chrome...")
        input("👉 Nhấn Enter sau khi đã xác minh xong...")

    print("✅ Đăng nhập thành công!")
    return driver
