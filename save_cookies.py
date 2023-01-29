import pickle
import sys
import time

import selenium.webdriver

website = sys.argv[1]
cookies_filename = sys.argv[2]

driver = selenium.webdriver.Chrome('chromedriver')
driver.get(website)
for i in range(60):
    print(i)
    time.sleep(1)
pickle.dump( driver.get_cookies() , open(cookies_filename, "wb"))