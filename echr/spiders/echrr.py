import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scrapy.selector import Selector
import time


def stop_element(s, word):
    str = []
    i = 0
    while i < len(s):
        if s[i].find(word) == -1:
            str.append(s[i])
            i += 1
        else:
            break
    return str


class EchrrSpider(scrapy.Spider):
    name = 'echrr'
    allowed_domains = ['hudoc.echr.coe.int']
    start_urls = ['https://hudoc.echr.coe.int/eng/']

    def __init__(self):
        self.options = Options()
        # comment out if you want selenium to run on screen.
        # self.options.add_argument("headless")

        self.options.add_experimental_option(
            "excludeSwitches", ["enable-logging"])
        # change the user agent if the page doesnt load.
        self.options.add_argument(
            "user-agent= Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4716.39 Safari/537.36")

        self.driver = webdriver.Chrome(
            executable_path=r"/Users/hassantariq/Desktop/ECHR_FYP/chromedriver", options=self.options)
        self.driver.set_window_size(1520, 1080)
        self.driver.get(self.start_urls[0])
        time.sleep(4)

        # change the number on the range, to keep scrolling as much as you want, (20 results) per scroll.
        for i in range(6000):
            self.driver.execute_script(
                "window.scrollTo(0,document.body.scrollHeight)")
            time.sleep(1)
        time.sleep(6)
        self.html = self.driver.page_source

    def parse(self, response):
        abso_url = 'https://hudoc.echr.coe.int'
        response = Selector(text=self.html)

        links = response.xpath(
            "//div[@class='results-list-block ']//div[@class='headlineContaniner']//a//@href").extract()
        languages = response.xpath(
            "//span[@class='column availableOnlyColumn ']//a//text()").extract()
        i = len(links)
        x = 0
        for link in links:
            if x < i:
                language = languages[x]
                x += 1
            urls = f"{abso_url}{link}"
            print(urls, 'url in paaaarseee')
            yield scrapy.Request(urls, callback=self.parse_2,
                                 meta={"url": urls,
                                       "language": language
                                       }, dont_filter=True
                                 )

    def parse_2(self, response):
        abso_url = 'https://hudoc.echr.coe.int'
        self.driver.get(response.meta['url'])
        self.driver.refresh()
        time.sleep(3)
        resp = self.driver.page_source
        res = Selector(text=resp)
        # ['/eng/#{"display":[2],"tabview":["document"],"languageisocode":["ENG"],"itemid":["001-215919"]}']
        title_2 = res.xpath(
            "//span[contains(text(), 'CASE')]//following::span//descendant::text()").extract() or None
        if title_2 is None:
            print("here should goooooooooo")
            # time.sleep(3)
            links = res.xpath(
                "//div[@class='languageEntry']//@href").extract()
            print(links, 'links to bee parsed')
            for link in links:
                b = link.split('i')[-1].split(':')[-1]
                v = '/eng#{"itemid":'
                full = v + b
                urls = f"{abso_url}{full}"
                print(urls, 'url in paaaarseee')
                yield scrapy.Request(urls, callback=self.parse_links,
                                     meta={"url": urls, "language": response.meta['language']}, dont_filter=True)
        else:
            title_1 = "CASE OF "
            title_2 = res.xpath(
                "//span[contains(text(), 'CASE')]//following::span//descendant::text()").extract()
            title_2_clean = [el.replace('\xa0', ' ')
                             for el in stop_element(title_2, 'JUDGMENT')]
            clean_title = ' '.join(title_2_clean)

            introduction = res.xpath(
                "//span[contains(text(), 'INTRODUCTION')]//following::span//descendant::text()").extract()
            clean_intro = [el.replace('\xa0', ' ')
                           for el in stop_element(introduction, 'THE FACTS')]

            factt = res.xpath(
                "//span[contains(text(), 'THE FACTS')]//following::span//descendant::text()").extract()
            clean_fact = [el.replace('\xa0', ' ')
                          for el in stop_element(factt, 'RELEVANT LEGAL')]

            unanimous_decision = res.xpath(
                "//span[contains(text(), 'FOR THESE')]//following::span//descendant::text()").extract()
            final_unaimous = [el.replace('\xa0', ' ') for el in stop_element(
                unanimous_decision, 'Done in English')]

            judgment = res.xpath(
                "//span[contains(text(), 'JUD')]//following::span//descendant::text()").extract()
            clean_judgment = [el.replace('\xa0', ' ')
                              for el in stop_element(judgment, 'STRASBOURG')]

            the_law = res.xpath(
                "//span[contains(text(), 'THE LAW')]//following::span//descendant::text()").extract()
            clean_the_law = [el.replace('\xa0', ' ')
                             for el in stop_element(the_law, 'Done in English')]

            relevant_legal = res.xpath(
                "//span[contains(text(), 'RELEVANT LEGAL')]//following::span//descendant::text()").extract()
            relevant_clean = [el.replace('\xa0', ' ') for el in stop_element(
                relevant_legal, 'THE LAW')]

            admissibility = res.xpath(
                "//span[contains(text(), 'Admissibility')]//following::span//descendant::text()").extract()
            clean_admissibility = [el.replace(
                '\xa0', ' ') for el in stop_element(admissibility, "Merits")]

            courts_assesment = res.xpath(
                "//span[contains(text(), 'General principles')]//following::span//descendant::text()").extract()
            clean_courts_assesment = [el.replace('\xa0', ' ') for el in stop_element(
                courts_assesment, "ALLEGED VIOLATION")]


            language = self.driver.find_element_by_xpath(
                "//*[@id='translation']/a/div[2]").click()
            time.sleep(2)
            resp = self.driver.page_source
            res = Selector(text=resp)

            language_1 = res.xpath(
                "//*[@id='officialLanguageTranslationLinks']/div/div/a/div/span//text()").extract_first()

            if (language_1 in ['French', 'Armenian', 'Turkish', 'Russian', 'Italian', 'Serbian', 'Romanian', 'Ukrainian', 'Bulgarian']):
                yield {
                    "language": response.meta['language'],
                }
            else:
                yield {
                    "url": response.meta['url'],
                    "language": language_1,
                    "title": (title_1 + clean_title),
                    "JUDGMENT": clean_judgment,
                    "introduction": clean_intro,
                    "Facts": clean_fact,
                    "The Law": clean_the_law,
                    "releavent legal framework": relevant_clean,
                    "Unanimously": final_unaimous,
                    "courts_assesment": clean_courts_assesment,
                    "Admissibility": clean_admissibility,

                }

    def parse_links(self, response):
        self.driver.get(response.meta['url'])
        print(response.meta['url'], ' urrrrrrrrrrrrrrrrrrrrrrrrrrr')
        time.sleep(3)
 
        self.driver.refresh()
        time.sleep(4)
        for i in range(2):
            time.sleep(1)
            self.driver.execute_script(
                "window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(2)
        resp = self.driver.page_source
        res = Selector(text=resp)

        title_1 = "CASE OF "
        title_2 = res.xpath(
            "//span[contains(text(), 'CASE')]//following::span//descendant::text()").extract()
        title_2_clean = [el.replace('\xa0', ' ')
                         for el in stop_element(title_2, 'JUDGMENT')]
        clean_title = ' '.join(title_2_clean)

        introduction = res.xpath(
            "//span[contains(text(), 'INTRODUCTION')]//following::span//descendant::text()").extract()
        clean_intro = [el.replace('\xa0', ' ')
                       for el in stop_element(introduction, 'THE FACTS')]

        factt = res.xpath(
            "//span[contains(text(), 'THE FACTS')]//following::span//descendant::text()").extract()
        clean_fact = [el.replace('\xa0', ' ')
                      for el in stop_element(factt, 'RELEVANT LEGAL')]

        unanimous_decision = res.xpath(
            "//span[contains(text(), 'FOR THESE')]//following::span//descendant::text()").extract()
        final_unaimous = [el.replace('\xa0', ' ')
                          for el in stop_element(unanimous_decision, 'Done in English')]

        judgment = res.xpath(
            "//span[contains(text(), 'JUD')]//following::span//descendant::text()").extract()
        clean_judgment = [el.replace('\xa0', ' ')
                          for el in stop_element(judgment, 'STRASBOURG')]

        the_law = res.xpath(
            "//span[contains(text(), 'THE LAW')]//following::span//descendant::text()").extract()
        clean_the_law = [el.replace('\xa0', ' ')
                         for el in stop_element(the_law, 'Done in English')]

        relevant_legal = res.xpath(
            "//span[contains(text(), 'RELEVANT LEGAL')]//following::span//descendant::text()").extract()
        relevant_clean = [el.replace('\xa0', ' ')
                          for el in stop_element(relevant_legal, 'THE LAW')]

        admissibility = res.xpath(
            "//span[contains(text(), 'Admissibility')]//following::span//descendant::text()").extract()
        clean_admissibility = [el.replace('\xa0', ' ')
                               for el in stop_element(admissibility, "Merits")]

        courts_assesment = res.xpath(
            "//span[contains(text(), 'General principles')]//following::span//descendant::text()").extract()
        clean_courts_assesment = [el.replace('\xa0', ' ') for el in stop_element(
            courts_assesment, "ALLEGED VIOLATION")]


        language = self.driver.find_element_by_xpath(
            "//*[@id='translation']/a/div[2]").click()
        time.sleep(2)
        resp = self.driver.page_source
        res = Selector(text=resp)

        language_1 = res.xpath(
            "//*[@id='officialLanguageTranslationLinks']/div/div/a/div/span//text()").extract_first()
        if (language_1 in ['French', 'Armenian', 'Turkish', 'Russian', 'Italian', 'Serbian', 'Romanian', 'Ukrainian', 'Bulgarian']):
            yield {
                "language": response.meta['language'],
            }
        else:
            yield {
                "url": response.meta['url'],
                "language": language_1,
                "title": (title_1 + clean_title),
                "JUDGMENT": clean_judgment,
                "introduction": clean_intro,
                "Facts": clean_fact,
                "The Law": clean_the_law,
                "releavent legal framework": relevant_clean,
                "Unanimously": final_unaimous,
                "courts_assesment": clean_courts_assesment,
                "Admissibility": clean_admissibility,
            }