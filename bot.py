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

DMARKET_KEY_VALUE = 1.85
BUFF163_KEY_VALUE = 12.3
BUFF163_COMMISSION_PERCENTAGE = 0.025

PREFERRED_FAMILY = ["bright water", "ultraviolet", "tiger tooth", "stained", "urban masked",
                    "safari mesh", "damascus steel", "autotronic", "rust coat", "vanilla",
                    "slaughter", "lore"]

PREFERRED_CATEGORY = ["knife", "rifle", "sniper rifle", "pistol", "smg", "machinegun", "shotgun"]

filter_arguments = {"game": "csgo-skins",
                    "is_stattrack": "not_stattrak_tm",
                    "starting_price": "2",
                    "ending_price": "5.22",
                    "category": PREFERRED_CATEGORY,
                    "family": [],
                    "sort_by": "Best Deals"}

driver = webdriver.Chrome('chromedriver')
driver.set_window_size(1920, 1080)
action = ActionChains(driver)

with open("api.txt", "r") as file:
    lines = file.readlines()
    PHONE, API_ID, API_HASH, GROUP = lines[0].strip(), int(lines[1].strip()), lines[2].strip(), lines[3].strip()
    print(PHONE, API_ID, API_HASH, GROUP)

""""Function takes value of the item and its currency and 
converts it to the equivalent number of keys (with decimal point)"""

def convert_price_to_keys(value, currency):
    if (currency == "CNY"):
        return (value - value * BUFF163_COMMISSION_PERCENTAGE) / BUFF163_KEY_VALUE
    return value / DMARKET_KEY_VALUE

def convert_keys_to_price(keys, currency):
    if (currency == "USD"):
        return keys * DMARKET_KEY_VALUE
    return keys * BUFF163_KEY_VALUE

def calculate_income_in_percentages(buff_price, income_in_yuans):
    buff_value_in_keys = convert_price_to_keys(buff_price, "CNY")
    return income_in_yuans / (buff_value_in_keys * BUFF163_KEY_VALUE) * 100


"""If you want to calculate your profit, you shall use these functions
Consider your optimal currency for this"""
def compare_prices_in_yuans(buff_price, dmarket_price):
    buff_value_in_keys = convert_price_to_keys(buff_price, "CNY")
    dmarket_value_in_keys = convert_price_to_keys(dmarket_price, "USD")
    return (buff_value_in_keys - dmarket_value_in_keys) * BUFF163_KEY_VALUE

def compare_prices_in_dollars(buff_price, dmarket_price):
    buff_value_in_keys = convert_price_to_keys(buff_price, "CNY")
    dmarket_value_in_keys = convert_price_to_keys(dmarket_price, "USD")
    return (buff_value_in_keys - dmarket_value_in_keys) * DMARKET_KEY_VALUE

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
                            if buff_items != None: #Sometimes there is no equivalent skin on buff163
                                buff_items, sell = get_buff163_deals_from(buff_link, 1)
                                if buff_items:
                                        yuans_income = compare_prices_in_yuans(buff_items[0].price, d_item.price)
                                        dollars_income = compare_prices_in_dollars(buff_items[0].price, d_item.price)
                                        percentage_income = calculate_income_in_percentages(buff_items[0].price, yuans_income)
                                        if yuans_income > 0:
                                            await client.send_message(GROUP, f"{d_item.name} | {d_item.skin} ({d_item.exterior})\n"
                                                                                 f"Price on DMarket: {d_item.price}$\n"
                                                                                 f"Price on BUFF163: {buff_items[0].price}¥\n"
                                                                                 f"Float: {d_item.float_wearing}\n"
                                                                                 f"Sales for past month: {sell}\n"
                                                                                 f"[DMARKET Link]({d_item.link})\n"
                                                                                 f"[BUFF163 Link]({buff_link})\n"
                                                                                 f"Income: {'{:10.2f}'.format(yuans_income)}¥ | {'{:10.2f}'.format(dollars_income)}$ | {'{:10.1f}'.format(percentage_income)}%\n"
                                                                                 "\n"
                                                                                 f"Note that this income was calculated considering that we buy\n"
                                                                                 f"keys for {BUFF163_KEY_VALUE}¥ each and sell it for {DMARKET_KEY_VALUE}$ each on dmarket\n")
                        file.write(d_item.link+"\n")
        driver.quit()

class Item:
    possible_exteriors = ('Factory New', 'Minimal Wear', 'Field-Tested', 'Well-Worn', 'Battle-Scarred', 'Not Painted')
    def __init__(self, params_dict):
        self.name = params_dict['name']
        self.skin = params_dict['skin']
        if params_dict['price'][0] == "$":
            self.price = float(params_dict['price'][1:])
        elif params_dict['price'][-1] == "Y":
            self.price = float(params_dict['price'].split()[0])
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

"""Converts a list of category / family
to a query params of DMARKET URL"""
def convert_list_to_market_query(list, type):
    query = ""
    for name in list:
        query = query + name.replace(" ", "%20") + ","
    if (type == "family"):
        return f"family={query}"
    elif (len(list) == 1):
        return query
    elif (len(list) > 1 and type=="category"):
        return f"categoryPath={query}"
    return query

def setup_market_search(delay=1.3, args=filter_arguments):
    family_string_url = convert_list_to_market_query(args["family"], "family")
    category_string_url = convert_list_to_market_query(args["category"], "category")

    baseUrl = f"https://dmarket.com/ingame-items/item-list/{args['game']}?{category_string_url}&{family_string_url}&category_0={args['is_stattrack']}&price-to={args['ending_price']}&price-from={args['starting_price']}"

    driver.get(baseUrl)
    time.sleep(delay)

    sort_list = driver.find_element(By.CLASS_NAME, 'o-select__currentArrow')
    sort_list.click()
    time.sleep(delay)

    sort_btn = driver.find_element(By.XPATH, f"//*[contains(text(), \'{args['sort_by']}\')]")
    sort_btn.click()
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
    setup_market_search()
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
    item_full_name = item.name + " | " + item.skin + " (" + item.exterior + ")"
    input.send_keys(item_full_name)
    time.sleep(5)
    search = driver.find_element(By.CSS_SELECTOR, 'a#search_btn_csgo')
    time.sleep(3)
    # item_btn = driver.find_element_by_xpath(f"// li[(text()=\'{item_full_name}\')]")
    item_btn = driver.find_element(By.XPATH, f"//li[text()=\'{item_full_name}\']")
    time.sleep(5)
    item_btn.click()
    link = driver.current_url
    print("Item link: " + link)
    time.sleep(5)
    try:
        item_container = driver.find_element(By.CLASS_NAME, 'img_td')
    except NoSuchElementException as e:
        print("WARNING: No equivalent skin was found")
        item_container = None
        return None
    finally:
        return link

def get_buff163_deals_from(website, number):
    items = []

    #GETTING PARAMETERS OF ALL SKIN INSTANCES on the website
    items_td = driver.find_elements(By.CLASS_NAME, 'img_td')
    imgs = [item_td.find_element(By.TAG_NAME, 'img') for item_td in items_td]
    selling_quantity = int(driver.find_element(By.CLASS_NAME, "new-tab").text.split('\n')[0].replace('Sell(', '').replace(')', '').replace("+", ""))
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
    asyncio.run(app.run(3, "parsed.txt", 10))