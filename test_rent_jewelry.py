import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException, TimeoutException


@pytest.fixture
def setup():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()


def wait_for_and_accept_alert(driver, timeout=5):
    """Return alert text if present and accept it, else return None."""
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        text = alert.text
        print(f"🔔 Alert detected: {text!r}")
        alert.accept()
        return text
    except TimeoutException:
        return None


def click_confirm_with_retry(driver, wait, confirm_button_css, retries=3, backoff_seconds=3):
    """Click confirm, handle 'Please wait' alerts, and retry."""
    for attempt in range(1, retries + 1):
        try:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, confirm_button_css))).click()
        except UnexpectedAlertPresentException:
            pass

        alert_text = wait_for_and_accept_alert(driver, timeout=2)
        if alert_text:
            if "Please wait" in alert_text or "already placed another order" in alert_text:
                if attempt < retries:
                    print(f"⚠ Server throttle alert → retrying in {backoff_seconds}s (attempt {attempt}/{retries})")
                    time.sleep(backoff_seconds)
                    continue
                else:
                    raise AssertionError("Throttled: 'Please wait' alert shown multiple times.")
        else:
            return True

    try:
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".section.order-completed")))
        return True
    except TimeoutException:
        return False


def test_rent_jewelry(setup):
    driver = setup
    wait = WebDriverWait(driver, 15)

    print("🔹 Opening nopCommerce demo site...")
    driver.get("https://demo.nopcommerce.com/")
    time.sleep(1.5)

    # ---------------- LOGIN ----------------
    print("🔹 Logging in...")
    driver.find_element(By.CLASS_NAME, "ico-login").click()
    wait.until(EC.visibility_of_element_located((By.ID, "Email"))).send_keys("lavanya.2828cs@gmail.com")
    driver.find_element(By.ID, "Password").send_keys("lav@2828")
    driver.find_element(By.CSS_SELECTOR, "button.login-button").click()
    time.sleep(1.5)

    # ---------------- JEWELRY SECTION ----------------
    print("🔹 Navigating to Jewelry section...")
    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Jewelry"))).click()
    time.sleep(1.5)

    print("🔹 Selecting first jewelry item...")
    product = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".product-item h2 a")))
    product.click()
    time.sleep(1.5)

    # If rental fields exist, enter dates
    try:
        print("🔹 Entering rental dates...")
        start_date = driver.find_element(By.CSS_SELECTOR, "input[id*='rental_start_date']")
        end_date = driver.find_element(By.CSS_SELECTOR, "input[id*='rental_end_date']")
        start_date.clear()
        start_date.send_keys("10/30/2025")
        end_date.clear()
        end_date.send_keys("11/02/2025")
    except Exception:
        print("ℹ Rental fields not found, skipping.")
    time.sleep(1.5)

    # ---------------- ADD TO CART ----------------
    print("🔹 Adding item to cart...")
    driver.find_element(By.CSS_SELECTOR, "button[id*='add-to-cart-button']").click()
    success = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "p.content")))
    assert "added to your shopping cart" in success.text
    print("✅ Item successfully added to cart.")
    time.sleep(1.5)

    # ---------------- CHECKOUT PROCESS ----------------
    print("🔹 Opening shopping cart...")
    driver.find_element(By.LINK_TEXT, "shopping cart").click()
    time.sleep(1.5)

    print("🔹 Accepting terms and starting checkout...")
    wait.until(EC.element_to_be_clickable((By.ID, "termsofservice"))).click()
    driver.find_element(By.ID, "checkout").click()
    time.sleep(1.5)

    # ---------------- BILLING ADDRESS ----------------
    print("🔹 Continuing with billing address...")
    wait.until(EC.element_to_be_clickable((By.NAME, "save"))).click()
    time.sleep(1.5)

    # ---------------- SHIPPING METHOD ----------------
    print("🔹 Selecting shipping method...")
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.shipping-method-next-step-button"))).click()
    time.sleep(1.5)

    # ---------------- PAYMENT METHOD ----------------
    print("🔹 Selecting payment method...")
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.payment-method-next-step-button"))).click()
    time.sleep(1.5)

    # ---------------- PAYMENT INFORMATION ----------------
    print("🔹 Proceeding with payment information...")
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.payment-info-next-step-button"))).click()
    time.sleep(1.5)

    # ---------------- CONFIRM ORDER ----------------
    print("🔹 Confirming order...")
    confirm_btn_css = "button.confirm-order-next-step-button"
    progressed = click_confirm_with_retry(driver, wait, confirm_btn_css, retries=4, backoff_seconds=3)
    if not progressed:
        raise AssertionError("❌ Could not complete order (server throttled multiple times).")

    # ---------------- VERIFY ORDER SUCCESS ----------------
    print("🔹 Verifying order success message...")
    success_text = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".section.order-completed"))
    ).text
    assert "Your order has been successfully processed!" in success_text
    print("🎉 ✅ Jewelry rental order successfully completed and verified!")