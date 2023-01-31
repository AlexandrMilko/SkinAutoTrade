import time
import pickle
from currency_converter import CurrencyConverter
from tkinter import Tk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import telethon as tg
import asyncio
from numpy import loadtxt

HOVER_DELAY = 2
c = CurrencyConverter()
tk = Tk()

driver = webdriver.Chrome('chromedriver')
driver.set_window_size(1920, 1080)
action = ActionChains(driver)

with open("api.txt", "r") as file:
    lines = file.readlines()
    PHONE, API_ID, API_HASH, GROUP = lines[0].strip(), int(lines[1].strip()), lines[2].strip(), int(lines[3].strip())
    print(PHONE, API_ID, API_HASH, GROUP)

class App:
    def __init__(self):
        pass
    async def run(self, desired_margin, parsed_filename, deals_num):
        deals = get_dmarket_deals('https://dmarket.com/ingame-items/item-list/csgo-skins', deals_num)
        parsed = loadtxt(parsed_filename, dtype="str")
        print(parsed)
        async with tg.TelegramClient(PHONE, API_ID, API_HASH) as client:
            with open(parsed_filename, 'a') as file:
                for d_item in deals:
                    if d_item.link not in parsed:
                        load_cookies(driver, "https://buff.163.com/market/csgo#tab=selling&page_num=1", "cookies.pkl")
                        buff_link = find_on_buff(d_item)
                        if buff_link != None: #Sometimes there is no equivalent skin on buff163
                            buff_items, sell = get_buff163_deals_from(buff_link, 1)
                            if buff_items:
                                margin = buff_items[0].price - d_item.price
                                if (margin > desired_margin):
                                    await client.send_message(GROUP, f"{d_item.name} | {d_item.skin} ({d_item.exterior})\n"
                                                                     f"Float: {d_item.float_wearing}\n"
                                                                     f"DMARKET Link: {d_item.link}\n"
                                                                     f"BUFF163 Link: {buff_link}\n"
                                                                     f"Price margin: {buff_items[0].price - d_item.price}\n"
                                                                     f"Sell: {sell}")
                        file.write(d_item.link+"\n")
        driver.quit()

class Item:
    possible_exteriors = ('Factory New', 'Minimal Wear', 'Field-Tested', 'Well-Worn', 'Battle-Scarred', 'Not Painted')
    def __init__(self, params_dict):
        self.name = params_dict['name']
        self.skin = params_dict['skin']
        if params_dict['price'][0] == "$": self.price = float(params_dict['price'][1:])
        elif params_dict['price'][-1] == "Y": self.price = float(c.convert(params_dict['price'].split()[0], "CNY", "USD"))
        self.exterior = params_dict['exterior']
        self.float_wearing = float(params_dict['float_wearing'])
        self.link = params_dict['link']
        self.paint_seed = params_dict['paint_seed']
        self.paint_index = params_dict['paint_index']

    @classmethod
    def get_exterior_from_string(cls, string):
        for exterior in cls.possible_exteriors:
            if exterior in string: return exterior

    def print_info(self):
        for parameter in dir(self):
            exec(f"if parameter[0] != \"_\": print(parameter + \":\", self.{parameter})")

def load_cookies(driver, website, cookies_filename):
    driver.get(website)
    cookies = pickle.load(open(cookies_filename, "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)

def apply_avanmarket_filters(delay=1.3, category="Knives", price=(60, 180)):

    sort_list = driver.find_element(By.CLASS_NAME, 'o-select__currentArrow')
    sort_list.click()

    time.sleep(delay)
    best_discount_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Best Discount')]")
    best_discount_btn.click()

    time.sleep(delay)
    best_price_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Best Price on Global Market')]")
    best_price_btn.click()

    time.sleep(delay)
    items_category_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Items category')]")
    items_category_btn.click()
    knives_btn = driver.find_element(By.XPATH, f"//*[contains(text(), '{category}')]")
    knives_btn.click()

    time.sleep(delay)
    filters_div = driver.find_element(By.CLASS_NAME, "с-filtersArea__content")
    price_panel = filters_div.find_elements(By.TAG_NAME, "mat-expansion-panel")[0]
    price_panel.click()
    inputs = price_panel.find_elements(By.TAG_NAME, 'input')
    from_input = inputs[0]
    to_input = inputs[1]
    from_input.send_keys(price[0])
    to_input.send_keys(price[1])
    time.sleep(delay)

def close_hint_btn(driver):
    driver.find_element(By.CSS_SELECTOR,
                        'mat-icon.mat-icon.notranslate.c-exchangeTabOnboarding__close.material-icons.mat-icon-no-color').click()

def highlight(element, effect_time, color, border):
    """Highlights (blinks) a Selenium Webdriver element"""
    driver = element._parent
    def apply_style(s):
        driver.execute_script("arguments[0].setAttribute('style', arguments[1]);",
                              element, s)
    original_style = element.get_attribute('style')
    apply_style("border: {0}px solid {1};".format(border, color))
    time.sleep(effect_time)
    apply_style(original_style)

def close_info(driver):
    div = driver.find_element(By.CSS_SELECTOR, 'div.c-dialogHeader').find_element(By.XPATH, '..')
    button = div.find_element(By.CSS_SELECTOR, "button.c-dialogHeader__close")
    highlight(button, 2, "blue", 5)
    button.click()

def open_info(asset):
    btn = asset.find_element(By.CSS_SELECTOR, '*')
    action.move_to_element(btn).perform()
    btn.click()

def get_dmarket_deals(website, deals_num):
    items = []
    driver.get("https://dmarket.com/ingame-items/item-list/csgo-skins")
    time.sleep(5)
    apply_avanmarket_filters(delay=1, category="Knives", price=(60, 180))
    time.sleep(5)
    deals_div = driver.find_element(By.CSS_SELECTOR, 'div.c-assets__container')
    assets = deals_div.find_elements(By.CSS_SELECTOR, "asset-card-action.ng-star-inserted")
    time.sleep(3)
    close_hint_btn(driver)
    counter = 0
    for asset in assets:
        open_info(asset)
        time.sleep(7)
        info_div = driver.find_element(By.CSS_SELECTOR, 'div.c-dialog__body.c-dialog__body--preview')
        highlight(info_div, 2, "blue", 5)
        params = dict()
        params['name'], params['skin'] = info_div.find_element(By.TAG_NAME, "h3").text.split('|')
        params['name'] = params['name'].strip()
        params['exterior'] = Item.get_exterior_from_string(params['skin'])
        params['skin'] = params['skin'].split('(')[0].strip()
        params['price'] = info_div.find_element(By.CSS_SELECTOR, 'price.ng-star-inserted').text
        params['float_wearing'] = info_div.find_element(By.CSS_SELECTOR, 'strong.o-qualityChart__infoValue').text

        link_btn = info_div.find_element(By.CSS_SELECTOR, 'button.mat-focus-indicator.c-shareLink__btn.mat-flat-button.mat-button-base')
        link_btn.click()
        copy_btn = info_div.find_element(By.CSS_SELECTOR, 'button.c-copy__cbCopyButton')
        copy_btn.click()
        params['link'] = tk.clipboard_get()

        params['paint_seed'] = None
        params['paint_index'] = None
        items.append(Item(params))
        counter += 1
        close_info(driver)
        if counter >= deals_num:

            time.sleep(5)
            break
    return items

def find_on_buff(item):
    driver.get("https://buff.163.com/market/csgo#tab=selling&page_num=1")
    input = driver.find_element(By.CSS_SELECTOR, 'input.i_Text')
    input.send_keys(item.name + " | " + item.skin + " (" + item.exterior + ")")
    time.sleep(5)
    search = driver.find_element(By.CSS_SELECTOR, 'a#search_btn_csgo')
    search.click()
    time.sleep(5)
    try:
        asset_ul = driver.find_element(By.CSS_SELECTOR, 'ul.card_csgo')
    except NoSuchElementException as e:
        print("WARNING: No equivalent skin was found")
        asset_ul = None
        link = None
    finally:
        link = asset_ul.find_element(By.TAG_NAME, 'a').get_attribute("href")

    return link

def get_buff163_deals_from(website, number):
    driver.get(website)
    time.sleep(5)
    items = []

    #GETTING PARAMETERS OF ALL SKIN INSTANCES on the website
    items_td = driver.find_elements(By.CLASS_NAME, 'img_td')
    imgs = [item_td.find_element(By.TAG_NAME, 'img') for item_td in items_td]
    selling_quantity = int(driver.find_element(By.CLASS_NAME, "new-tab").text.split('\n')[0].replace('Sell(', '').replace(')', ''))
    counter = 0
    for img in imgs:
        info_dict = dict()
        action.move_to_element(img).perform()
        time.sleep(HOVER_DELAY)
        div_name_price = driver.find_element(By.CLASS_NAME, "floattip-cont")
        name, skin = div_name_price.find_element(By.TAG_NAME, 'h3').text.split('|')
        name = name.strip()
        exterior = Item.get_exterior_from_string(skin)
        skin = skin.split('(')[0].strip()
        price = div_name_price.find_element(By.TAG_NAME, "big").text + " Y"
        paint_seed, paint_index, float_wearing = driver.find_element(By.CLASS_NAME, "skin-info").text.split('\n')[:3]
        float_wearing = float(float_wearing.replace('Float: ', ''))
        paint_seed = int(paint_seed.replace('Paint seed: ', ''))
        paint_index = int(paint_index.replace("Paint index: ", '').split(' ')[0]) # I use split to remove Phase number. For example, "571 (Phase3)" -> "571"
        info_dict['name'] = name
        info_dict['skin'] = skin
        info_dict['price'] = price
        info_dict['exterior'] = exterior
        info_dict['float_wearing'] = float_wearing
        info_dict['paint_seed'] = paint_seed
        info_dict['paint_index'] = paint_index
        info_dict['link'] = website
        items.append(Item(info_dict))
        counter+=1
        if counter >= number:

            break

    return items, selling_quantity

if __name__ == "__main__":
    app = App()
    asyncio.run(app.run(0, "parsed.txt", 7))