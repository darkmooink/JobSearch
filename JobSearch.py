from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import \
    staleness_of
from selenium.webdriver.support.ui import Select

import csv
from selenium.webdriver.support.ui import Select
import sys
import datetime
import generateUtils
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

# get variables
settings = generateUtils.get_varible('settings.pkl',
                                     {"blacklist": {}, "username": None, 'selectLinkOpeninNewTab': None})
history = generateUtils.get_varible('history.pkl', {"viewed": [], 'applied': [], 'not_viewed': {}})

def main():

    if settings['selectLinkOpeninNewTab'] is None:
        appleKeys = Keys.COMMAND + Keys.RETURN
        windowsKeys = Keys.CONTROL + Keys.RETURN
        driver = webdriver.Chrome("Drivers/chromedriver")
        url = driver.current_url
        driver.get('https://bbc.co.uk')
        WebDriverWait(driver,10).until(EC.url_changes(url))
        link = driver.find_element(By.TAG_NAME, 'a')
        link.send_keys(appleKeys)
        if len(driver.window_handles) > 1:
            settings['selectLinkOpeninNewTab'] = appleKeys
        else:
            settings['selectLinkOpeninNewTab'] = windowsKeys
        generateUtils.save_varible('settings.pkl', settings)
        driver.quit()

    selectLinkOpeninNewTab = settings['selectLinkOpeninNewTab']

    # check variables and get inputs
    if settings['username'] is None:
        settings['username'] = input('What is your dwp.gov username?')
        settings['password'] = input('What is your dwp.gov password?')
        settings['name'] = input('What is your name? (this is used when submitting your CV)')
        settings['message'] = input('What do you want to be in your cover letter? Just press enter to use the default. Use \\n for a new line')
        copy = input('Receive a copy of each application by email? yes/no')
        if copy[0] == 'y' or copy[0] == 'Y':
            settings['copy'] = True
        elif copy[0] == 'n' or copy[0] == 'n':
            settings['copy'] = False


        generateUtils.save_varible('settings.pkl', settings)

    # searchLocation = input("Where do you want to search?")
    searchLocation ='cromer'

    driver = webdriver.Chrome("Drivers/chromedriver")
    wait = WebDriverWait(driver, 30)

    # login
    login_url = "https://findajob.dwp.gov.uk/sign-in"
    driver.get(login_url)
    driver.find_element(By.ID, 'email').send_keys(settings['username'])
    driver.find_element(By.ID, 'password').send_keys(settings['password'])
    driver.find_element(By.ID, 'password').send_keys(Keys.ENTER)
    try:
        WebDriverWait(driver, 5).until(EC.url_changes(login_url))
    except TimeoutException:
        print('Please login')
        while(driver.current_url == "https://findajob.dwp.gov.uk/sign-in"):
            try:
                wait.until(EC.url_changes("https://findajob.dwp.gov.uk/sign-in"))
            except TimeoutException:
                do = 'nothing'


    # search
    driver.get("https://findajob.dwp.gov.uk/")
    elem = driver.find_element(By.ID, "where")
    elem.send_keys(searchLocation)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'autocomplete-selected'))).click() # this is needed because the page dosent like incorect formatted search terms, the first auto complete will be selected.
    elem.send_keys(Keys.RETURN)

    wait.until(EC.title_contains('Jobs in'))
    is_last_page = False
    while is_last_page is False:


        # look at each job
        for job in driver.find_elements(By.CLASS_NAME, 'search-result'):

            # checking if you should skip it
            jobid = job.get_attribute('data-aid')
            if jobid in history['viewed']:
                continue
            for word in settings['blacklist']:
                if word in job.find_element(By.TAG_NAME, 'a').text:
                    continue
                if word in job.find_element(By.CLASS_NAME, 'search-result-description'):
                    continue
            link = job.find_element(By.CLASS_NAME, 'govuk-link')
            link.send_keys(selectLinkOpeninNewTab)

            jobs_to_check_at_once = 10
            if len(driver.window_handles) > jobs_to_check_at_once:
                driver.implicitly_wait(1)
                filter_jobs(driver)


        # loop through pages, check if last page
        try:
            page_links = driver.find_element(By.CLASS_NAME, "pager-items").find_elements(By.TAG_NAME,'li')
            last_page = page_links[len(page_links)-1].find_element(By.TAG_NAME, 'a')
            url = driver.current_url
            driver.find_element(By.CLASS_NAME, 'pager-next').click()
            wait.until(EC.url_changes(url))
        except NoSuchElementException:
            is_last_page = True

        generateUtils.save_varible('history.pkl', history)

    input("Press enter to close")


# todo submit cv

def filter_jobs(driver):
    window_number = 1
    while window_number is not len(driver.window_handles):
        driver.switch_to_window(driver.window_handles[window_number])

        try:
            jobid = driver.find_elements(By.CLASS_NAME, 'govuk-link')
            for link in jobid:
                if link.text == 'Save to favourites':
                    jobid = link.get_attribute('data-js-favourite')
            link = driver.find_element_by_class_name("govuk-grid-column-two-thirds").find_element_by_tag_name(
                "p").find_element_by_tag_name("a")

            if link is not None and "findajob.dwp.gov.uk" in link.get_attribute("href") and link.get_attribute(
                    "data-js") is None:
                link.click()
                WebDriverWait(driver, 20).until(
                    staleness_of(link)
                )
                if "https://findajob.dwp.gov.uk/" not in driver.current_url:
                    driver.close()
                else:
                    form = driver.find_element(By.NAME, 'apply')
                    jobid = form.find_element(By.NAME, 'ad_id').get_attribute('value')
                    form.find_element(By.ID, 'full_name').send_keys(settings['name'])
                    form.find_element(By.ID, 'message').send_keys(settings['message'])
                    selection = form.find_element(By.ID, 'cv_id')
                    while len(selection.find_elements(By.TAG_NAME, 'option'))==1 and True:
                        input('please upload your cv then press enter here')
                    Select(selection).select_by_index(1)


                    if not settings['copy']:
                        form.find_element(By.ID, 'cc_self').send_keys(Keys.SPACE)

                    # form.submit()
                    history['applied'].append(jobid)

                    driver.close()

                    # driver.back()
                    # window_number = window_number+1
            else:
                driver.close()
            history['viewed'].append(jobid)
        except:
            driver.close()



    driver.switch_to_window(driver.window_handles[0])

if __name__ == "__main__":
    main()