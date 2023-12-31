import os
import random
import json
import argparse
from time import sleep
import signal
from tqdm.notebook import tqdm

from selenium import webdriver
from selenium.webdriver import ActionChains
from webdriver_manager.firefox import GeckoDriverManager

from utils.constants import CITY_DISCTRICT_DICT, ACCEPT_BUTTON, type_org_mapping, CITIES

from selenium.webdriver.firefox.webdriver import WebDriver


class LinksCollector:
    """
    A class to retrieve links to pages of facilities in the region
    ...
    Attributes
    ----------
    """
    def __init__(
        self,
        driver: WebDriver,
        link: str = "https://yandex.ru/maps",
        max_errors: int = 5,
        accept_button: str = ACCEPT_BUTTON,
        accept: bool = False,
    ):
        self.driver = driver
        self.slider = None
        self.max_errors = max_errors
        self.link = link
        self.accept_button = accept_button
        self.accept = accept

    def _init_driver(self):
        self.driver.maximize_window()

    def _driver_quit(self):
        driver_pid = self.driver.service.process.pid
        self.driver.quit()
        try:
            os.kill(int(driver_pid), signal.SIGTERM)
            print("Killed browser using process")
        except ProcessLookupError as ex:
            pass

    def _open_page(self, request: str):
        self.driver.get(self.link)
        sleep(random.uniform(1, 2))
        ActionChains(self.driver).move_to_element(
            self.driver.find_element_by_class_name(name="search-form-view__input")
        ).send_keys(request).perform()
        sleep(random.uniform(0.4, 0.7))
        self.driver.find_element_by_class_name(
            name="small-search-form-view__button"
        ).submit()
        # Нажимаем на кнопку поиска
        sleep(random.uniform(1.4, 2))
        self.slider = self.driver.find_element_by_class_name(
            name="scroll__scrollbar-thumb"
        )

        if self.accept:
            # Соглашение куки
            flag = True
            count = 0
            while flag:
                try:
                    count += 1
                    sleep(3)
                    self.driver.find_element_by_xpath(self.accept_button).click()
                    flag = False
                except:
                    if count > 5:
                        self._driver_quit()
                        self._init_driver()
                        self._open_page(request)
                    flag = True

    def run(self, city: str, district: str, type_org_ru: str, type_org: str):
        self._init_driver()
        request = city + " " + district + " " + type_org_ru
        self._open_page(request)
        organizations_hrefs = []

        count = 0
        link_number = [0]
        errors = 0
        while self.max_errors > errors:
            try:
                ActionChains(self.driver).click_and_hold(self.slider).move_by_offset(
                    0, int(100 / errors)
                ).release().perform()
                slider_organizations_hrefs = self.driver.find_elements_by_class_name(
                    name="search-snippet-view__link-overlay"
                )
                slider_organizations_hrefs = [
                    href.get_attribute("href") for href in slider_organizations_hrefs
                ]
                organizations_hrefs = list(
                    set(organizations_hrefs + slider_organizations_hrefs)
                )
                count += 1
                if count % 3 == 0:
                    if len(organizations_hrefs) == link_number[-1]:
                        errors = errors + 1
                    #     print("errors", errors)
                    # print(len(organizations_hrefs))
                    link_number.append(len(organizations_hrefs))

                sleep(random.uniform(0.05, 0.1))
            except Exception:
                errors = errors + 1
                # print("errors", errors)
                sleep(random.uniform(0.3, 0.4))

        directory = f"links/{city}/{type_org}"
        if not os.path.exists(directory):
            os.makedirs(directory)
        self._driver_quit()
        with open(f"{directory}/{request}.json", "w") as file:
            json.dump({"1": organizations_hrefs}, file)

    def run_city(self, city: str, type_org_ru: str, type_org: str):
        self._init_driver()
        request = city + " " + type_org_ru
        self._open_page(request)
        organizations_hrefs = []

        count = 0
        link_number = [0]
        errors = 0
        with tqdm(desc= f'{city} {type_org}, links parsing') as pbar:
            while self.max_errors > errors:
                try:
                    ActionChains(self.driver).click_and_hold(self.slider).move_by_offset(
                        0, int(100 / errors)
                    ).release().perform()
                    slider_organizations_hrefs = self.driver.find_elements_by_class_name(
                        name="search-snippet-view__link-overlay"
                    )
                    slider_organizations_hrefs = [
                        href.get_attribute("href") for href in slider_organizations_hrefs
                    ]
                    organizations_hrefs = list(
                        set(organizations_hrefs + slider_organizations_hrefs)
                    )
                    count += 1
                    if count % 3 == 0:
                        if len(organizations_hrefs) == link_number[-1]:
                            errors = errors + 1
                            # print("errors", errors)
                        else:
                            update_value = len(organizations_hrefs)-link_number[-1]
                            pbar.update(update_value)
                            pbar.refresh()
                        link_number.append(len(organizations_hrefs))

                    sleep(random.uniform(0.05, 0.1))
                except Exception:
                    errors = errors + 1
                    # print("errors", errors)
                    sleep(random.uniform(0.3, 0.4))

            directory = f"links/{city}/{type_org}"
            if not os.path.exists(directory):
                os.makedirs(directory)
            self._driver_quit()
            with open(f"{directory}/{request}.json", "w") as file:
                # print(len(organizations_hrefs))
                json.dump({"1": organizations_hrefs}, file)

def parse_links(type_org, city):
    sleep(1)
    headOption = webdriver.FirefoxOptions()
    headOption.headless = True
    driver_path = GeckoDriverManager(path="drivers", version="v0.32.2").install()
    driver = webdriver.Firefox(executable_path=driver_path, options=headOption)
    grabber = LinksCollector(driver)
    grabber.run_city(
        city=city,
        type_org_ru=type_org_mapping[type_org],
        type_org=type_org,
    )