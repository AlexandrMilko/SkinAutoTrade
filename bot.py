import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

HOVER_DELAY = 2
driver = webdriver.Chrome('chromedriver')
action = ActionChains(driver)

class Item:
    possible_exteriors = ('Factory New', 'Minimal Wear', 'Field-Tested', 'Well-Worn', 'Battle-Scarred', 'Not Painted')
    def __init__(self, params_dict):
        self.name = params_dict['name']
        self.skin = params_dict['skin']
        self.price = params_dict['price']
        self.exterior = params_dict['exterior']
        self.float_wearing = params_dict['float_wearing']
        self.paint_seed = params_dict['paint_seed']
        self.paint_index = params_dict['paint_index']

    @classmethod
    def get_exterior_from_string(cls, string):
        for exterior in cls.possible_exteriors:
            if exterior in string: return exterior

def apply_avanmarket_filters(delay=1, category="Knives", price=(60, 180)):

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

def close_info_btn(driver):
    driver.find_element(By.CSS_SELECTOR,
                        'mat-icon.mat-icon.notranslate.ng-tns-c285-50.material-icons.mat-icon-no-color').click()

def get_avanmarket_deals(website):
    driver.get("https://dmarket.com/ingame-items/item-list/csgo-skins")
    apply_avanmarket_filters(delay=1, category="Knives", price=(60, 180))

    time.sleep(5)
    info_div = driver.find_element(By.CSS_SELECTOR, 'div.c-assets__container')
    assets = info_div.find_elements(By.CSS_SELECTOR, "asset-card-action.ng-star-inserted")
    time.sleep(3)
    close_hint_btn(driver)
    for asset in assets:
        btn = asset.find_element(By.CSS_SELECTOR, '*')
        action.move_to_element(btn).perform()
        btn.click()
        time.sleep(2)
        close_info_btn(driver)
        time.sleep(3)

    time.sleep(10)
    driver.quit()

def get_buff163_deals_for_skin(website):
    driver.get(website)
    knives = []

    #GETTING PARAMETERS OF ALL SKIN INSTANCES on the website
    items_td = driver.find_elements(By.CLASS_NAME, 'img_td')
    imgs = [item_td.find_element(By.TAG_NAME, 'img') for item_td in items_td]
    info_dicts = []
    selling_quantity = int(driver.find_element(By.CLASS_NAME, "new-tab").text.split('\n')[0].replace('Sell(', '').replace(')', ''))
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
        paint_index = int(paint_index.replace("Paint index: ", ''))
        info_dict['name'] = name
        info_dict['skin'] = skin
        info_dict['price'] = price
        info_dict['exterior'] = exterior
        info_dict['float_wearing'] = float_wearing
        info_dict['paint_seed'] = paint_seed
        info_dict['paint_index'] = paint_index
        info_dicts.append(info_dict)

    driver.quit()

    return info_dicts, selling_quantity

if __name__ == "__main__":
    get_avanmarket_deals('https://dmarket.com/ingame-items/item-list/csgo-skins')