import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
import telethon as tg
import sys
import asyncio
import os


with open("api.txt", "r") as file:
    lines = file.readlines()
    PHONE, API_ID, API_HASH, GROUP = lines[0].strip(), int(lines[1].strip()), lines[2].strip(), lines[3].strip()
    print(PHONE, API_ID, API_HASH, GROUP)


dir = os.path.join(os.getcwd(), "dmarket")

print(dir)

options = webdriver.ChromeOptions()
options.add_argument(f"user-data-dir={dir}")
driver = webdriver.Chrome('chromedriver', options=options)
driver.set_window_size(1920, 1080)

PRICE_DELAY = 20

def get_key_price_dmarket(driver=driver):
    link = "https://dmarket.com/ingame-items/item-list/tf2-skins?exchangeTab=exchange"
    driver.get(link)
    time.sleep(50)
    assets_div = driver.find_element(By.CSS_SELECTOR, "div.c-assets__container")
    price = float(assets_div.find_elements(By.CSS_SELECTOR, "price.ng-star-inserted")[0].text[1:])
    print(price)
    return price

async def send_key_price(delay=PRICE_DELAY, last_price=None, ):
    price = get_key_price_dmarket()
    if (last_price != price):
        async with tg.TelegramClient(PHONE, API_ID, API_HASH) as client:
            await client.send_message(GROUP, f"Price of the key has changed! "
                                        f"Right now, it costs: {price}$")
    await asyncio.sleep(PRICE_DELAY)
    await send_key_price(PRICE_DELAY, price)


if __name__ == "__main__":
    asyncio.run(send_key_price(PRICE_DELAY))