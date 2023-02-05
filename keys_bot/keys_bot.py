import time

from selenium import webdriver
from selenium.webdriver.common.by import By

options = webdriver.ChromeOptions()
options.add_argument("user-data-dir=dmarket")
driver = webdriver.Chrome('chromedriver', options=options)
driver.set_window_size(1920, 1080)

def get_key_price_dmarket(driver):
    link = "https://dmarket.com/ingame-items/item-list/tf2-skins?exchangeTab=exchange"
    driver.get(link)
    time.sleep(10)
    assets_div = driver.find_element(By.CSS_SELECTOR, "div.c-assets__container")
    price = float(assets_div.find_elements(By.CSS_SELECTOR, "price.ng-star-inserted")[0].text[1:])
    print(price)
    return price

if __name__ == "__main__":
    get_key_price_dmarket(driver)