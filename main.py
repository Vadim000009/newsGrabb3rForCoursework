import selenium
import re
import os
from sys import exit  # Потому что .exe файл не знает откуда взять имя exit ¯\_(ツ)_/¯
from progress.bar import IncrementalBar  # Красивый прогресс бар в Гадюке
from lxml import etree  # Работа с XML
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains


def attribAdd(name):
    name.attrib['verify'] = "true"
    name.attrib['type'] = "str"
    name.attrib['auto'] = "true"


def initDriverChrome():
    try:
        if not os.path.exists(r".\chromedriver.exe"):
            print("Файл chromedriver.exe не находится в директории с программой!\n"
                  "Запуск программы невозможен! Выход из программы...\n")
            exit(0)
        chromedriver = r".\chromedriver.exe"
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("start-maximized")
        options.add_argument("enable-automation")
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-browser-side-navigation")
        options.page_load_strategy = 'none'
        # Отключаем ругательства в PowerShell о всяких синезубах
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(executable_path=chromedriver, options=options)
        return driver
    except selenium.common.exceptions.SessionNotCreatedException as error:
        print("Запуск невозможен! Ошибка:\n")
        print(error)  # На всякий пожарный оповестим о несоответствии версий
        exit(0)


# TODO: Дописать многопоток
# TODO: Может стоит... Картинки тоже брать на борт?
if __name__ == "__main__":
    os.system("cls")
    print("Введите количество статей, которое необходимо собрать")
    while True:
        try:
            counterOfArticles = int(input())
            if counterOfArticles <= 0:
                print("Введите пожалуйства ПОЛОЖИТЕЛЬНОЕ число")
            else:
                break
        except (ValueError, KeyboardInterrupt):
            print("Введите пожалуйства число")

    driver = initDriverChrome()
    if not os.path.isdir("articles"):
        os.mkdir("articles1")
    driver.get("https://txt.newsru.com/allnews/30may2017/") # 30may2021
    driver.implicitly_wait(1)
    driver.set_page_load_timeout(30)
    try:
        # Жмём на кнопку "на день назад"
        button = driver.find_element_by_class_name("arch-arrows-link-l")

        newsTemp, category, newsRef, namesNews, tags = [], [], [], [], []
        counter, parseRefCounter, scrollCounter, date, ex = 0, 0, 0, '', ''

        xmlData = etree.Element("doc")
        originalURLData = etree.SubElement(xmlData, "URL")
        attribAdd(originalURLData)
        titleXmlData = etree.SubElement(xmlData, "title")
        attribAdd(titleXmlData)
        textXmlData = etree.SubElement(xmlData, "text")
        attribAdd(textXmlData)
        dateXmlData = etree.SubElement(xmlData, "date")
        attribAdd(dateXmlData)
        categoryXmlData = etree.SubElement(xmlData, "category")
        attribAdd(categoryXmlData)
        tagsXmlData = etree.SubElement(xmlData, "tags")
        attribAdd(tagsXmlData)
        print("Для экстренного завершения программы нажмите \'ctrl + c\'")
        counterBar = IncrementalBar("Сбор ссылок! ", max=counterOfArticles,
                                    suffix='%(percent)d%% собрано и %(remaining)s осталось,'
                                           ' Секунд затрачено - %(elapsed)s')
        while counter != counterOfArticles:
            for news in driver.find_element_by_class_name("content-main") \
                    .find_elements_by_class_name("inner-news-item"):
                if counter == counterOfArticles:
                    break
                newsRef.append(news.find_element_by_tag_name("a").get_attribute("href"))
                category.append(news.find_element_by_class_name("index-news-date") \
                                .find_element_by_tag_name("a").text)
                namesNews.append(news.find_element_by_class_name("index-news-title").text)
                counter = counter + 1
                counterBar.next()
            if counter > counterOfArticles:
                counterBar.finish()
                break
            try:
                ActionChains(driver).move_to_element(button).click().perform()
            except selenium.common.exceptions.StaleElementReferenceException:
                button = driver.find_element_by_class_name("arch-arrows-link-l")
                ActionChains(driver).move_to_element(button).click().perform()

        print("\n\nСсылки собраны! Приступаем к сбору статей.\n\n")
        articleBar = IncrementalBar("Сбор статей", max=len(newsRef),
                                    suffix='Собрано %(index)s статей и %(remaining)s осталось,'
                                           ' Секунд затрачено - %(elapsed)s')
        for ref in newsRef:
            try:
                driver.get(ref)
                articleBar.next()
                ex = ref
                if re.search(r'inopressa', str(ref)):
                    tags = str("[" + driver.find_element_by_class_name("topic").find_element_by_tag_name("a")
                               .text + "]").replace("|", ",")
                    date = str(driver.find_element_by_class_name("maincaption").text).replace(" г.", "")
                    for bodyText in driver.find_element_by_class_name("body") \
                            .find_elements_by_class_name("articPar"):
                        newsTemp.append(bodyText.text)
                elif re.search(r'newsru', str(ref)):
                    date = driver.find_element_by_class_name("article-date").text
                    date = re.search(r".\d+.*?,", str(date)).group().replace(",", "").replace(" г.", "")[1:]
                    for bodyText in driver.find_element_by_class_name("article-text") \
                            .find_elements_by_tag_name("p"):
                        newsTemp.append(bodyText.text)
                    for tag in driver.find_elements_by_class_name("article-tags-list"):
                        tags.append(tag.text)
                    try:
                        tags.remove('Каталог NEWSru.com')
                        tags.remove('Информационные интернет-ресурсы')
                        tags.remove('Досье NEWSru.com')
                    except ValueError:
                        tags = []
                elif re.search(r'meddaily', str(ref)):
                    for tag in driver.find_elements_by_class_name("topic_rubric"):
                        tags.append(tag.text)
                    tags.pop(0)
                    tags = str(tags).replace("Темы:", "")
                    date = driver.find_element_by_class_name("topic_date").text
                    for bodyText in driver.find_elements_by_class_name("topic_text"):
                        newsTemp.append(bodyText.text)
                unionText = ''.join(newsTemp)
                originalURLData.text = str(ref)
                titleXmlData.text = namesNews[parseRefCounter]
                textXmlData.text = etree.CDATA(unionText)
                categoryXmlData.text = category[parseRefCounter]
                tagsXmlData.text = str(tags)[1:-1].replace("' ", "").replace("'", "")
                dateXmlData.text = date
                xmlTree = etree.ElementTree(xmlData)
                xmlTree.write(".\\articles\\output " + str(parseRefCounter) + ".xml", encoding="utf-8"
                              , xml_declaration=True, pretty_print=True)
                parseRefCounter = parseRefCounter + 1
                newsTemp.clear()
                tags = []
            except (selenium.common.exceptions.NoSuchElementException, IndexError,
                    selenium.common.exceptions.TimeoutException,
                    selenium.common.exceptions.StaleElementReferenceException):
                print("\nОшибка! Ссылка:" + str(ex))
                parseRefCounter = parseRefCounter + 1
                newsTemp.clear()
                tags, date = [], ""
        articleBar.finish()
        print("\nСбор завершён! Все собранные статьи храняться в папке articles "
              "в директории запуска данной программы")
    except selenium.common.exceptions.NoSuchElementException:
        print("О неееееееет, что-то пошло не так. Видимо, они знают, что я робот :с\n"
              "Или сайт упал и скайнет победил С:\nПрограмма будет завершена")
    driver.close()
    driver.quit()
    exit(0)
