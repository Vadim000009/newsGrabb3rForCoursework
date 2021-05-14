import selenium
import re
import os
from sys import exit  # Потому что .exe файл не знает откуда взять имя exit ¯\_(ツ)_/¯
from progress.bar import IncrementalBar  # Красивый прогресс бар в Гадюке
from lxml import etree  # Работа с XML
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains


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
        # options.add_argument("--headless") # Некорректно работает
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        # Отключаем ругательства в PowerShell о всяких синезубах
        driver = webdriver.Chrome(executable_path=chromedriver, options=options)
        return driver
    except selenium.common.exceptions.SessionNotCreatedException as error:
        print("Запуск невозможен! Ошибка:\n")
        print(error)  # На всякий пожарный оповестим о несоответствии версий
        exit(0)


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
        except ValueError or KeyboardInterrupt:
            print("Введите пожалуйства число")

    driver = initDriverChrome()
    if not os.path.isdir("articles"):
        os.mkdir("articles")
    driver.get("https://txt.newsru.com/allnews/")
    driver.implicitly_wait(2)
    # Жмём на кнопку "на день назад"
    button = driver.find_element_by_class_name("arch-arrows-link-l")

    newsTemp, category, newsRef, namesNews, tags = [], [], [], [], []
    counter, parseRefCounter, scrollCounter, date, ex = 0, 0, 0, '', ''

    xmlData = etree.Element("doc")
    originalURLData = etree.SubElement(xmlData, "URL")
    originalURLData.attrib['verify'] = "true"
    originalURLData.attrib['type'] = "str"
    originalURLData.attrib['auto'] = "true"

    titleXmlData = etree.SubElement(xmlData, "title")
    titleXmlData.attrib['verify'] = "true"
    titleXmlData.attrib['type'] = "str"
    titleXmlData.attrib['auto'] = "true"

    textXmlData = etree.SubElement(xmlData, "text")
    textXmlData.attrib['verify'] = "true"
    textXmlData.attrib['type'] = "str"
    textXmlData.attrib['auto'] = "true"

    dateXmlData = etree.SubElement(xmlData, "date")
    dateXmlData.attrib['verify'] = "true"
    dateXmlData.attrib['type'] = "str"
    dateXmlData.attrib['auto'] = "true"

    categoryXmlData = etree.SubElement(xmlData, "category")
    categoryXmlData.attrib['verify'] = "true"
    categoryXmlData.attrib['type'] = "str"
    categoryXmlData.attrib['auto'] = "true"

    tagsXmlData = etree.SubElement(xmlData, "tags")
    tagsXmlData.attrib['verify'] = "true"
    tagsXmlData.attrib['type'] = "str"
    tagsXmlData.attrib['auto'] = "true"

    counterBar = IncrementalBar("Сбор ссылок! ", max=counterOfArticles,
                                suffix='%(percent)d%% собрано и %(remaining)s осталось,'
                                       ' Секунд затрачено - %(elapsed)s')
    while counter != counterOfArticles:
        driver.implicitly_wait(1)
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
            ex = ref
            driver.implicitly_wait(1)
            if re.search(r'inopressa', str(ref)):
                tags = str("[" + driver.find_element_by_xpath("/html/body/table/tbody/tr[2]/td/table[2]/"
                                                        "tbody/tr/td[1]/div[3]/div[2]/h3/a")
                           .text + "]").replace("|", ",")
                date = driver.find_element_by_class_name("maincaption").text
                for bodyText in driver.find_element_by_class_name("body") \
                        .find_elements_by_class_name("articPar"):
                    newsTemp.append(bodyText.text)
            elif re.search(r'newsru', str(ref)):
                date = driver.find_element_by_class_name("article-date").text
                date = re.search(r".\d+.*?,", str(date)).group().replace(",", "")
                for bodyText in driver.find_element_by_class_name("article-text") \
                        .find_elements_by_tag_name("p"):
                    newsTemp.append(bodyText.text)
                for tag in driver.find_elements_by_class_name("article-tags-list"):
                    tags.append(tag.text)
                tags.pop(0)
                tags.pop(0)
                tags.pop(0)
            elif re.search(r'meddaily', str(ref)):
                tags = str(driver.find_element_by_xpath("//*[@id='main']/tbody/tr/td[1]/table/"
                                                        "tbody/tr/td[2]/div/div[1]/div[2]/div[6]")
                           .text).replace("Темы:", "")
                date = driver.find_element_by_class_name("topic_date").text
                str(date) + "."
                for bodyText in driver.find_elements_by_class_name("topic_text"):
                    newsTemp.append(bodyText.text)
            unionText = ''.join(newsTemp)
            originalURLData.text = str(ref)
            titleXmlData.text = namesNews[parseRefCounter]
            textXmlData.text = etree.CDATA(unionText)
            categoryXmlData.text = category[parseRefCounter]
            tagsXmlData.text = str(tags)[1:-1]
            dateXmlData.text = date
            xmlTree = etree.ElementTree(xmlData)
            xmlTree.write(".\\articles\\output " + str(parseRefCounter) + ".xml", encoding="utf-8"
                          , xml_declaration=True, pretty_print=True)
            articleBar.next()
            parseRefCounter = parseRefCounter + 1
            newsTemp.clear()
            tags = []
        except selenium.common.exceptions.NoSuchElementException:
            print("Удивительно, но статьи по данной ссылке не существует\n" + str(ex) +
                  "\nПродолжаю работу")
    articleBar.finish()
    print("\nСбор завершён! Все собранные статьи храняться в папке articles "
          "в директории запуска данной программы")
    driver.close()
    exit(0)
