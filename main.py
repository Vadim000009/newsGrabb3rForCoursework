import selenium
import re
from progress.bar import IncrementalBar
from lxml import etree
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains


def initDriverChrome():
    chromedriver = r"C:\Users\1\PycharmProjects\newsGrabb3rForCoursework\chromedriver.exe"
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    # Отключаем ругательства в PowerShell и всяких синезубах
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(executable_path=chromedriver, options=options)

    return driver


if __name__ == "__main__":
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
    driver.get("https://txt.newsru.com/allnews/")
    driver.implicitly_wait(1)

    button = driver.find_element_by_class_name("arch-arrows-link-l")

    parseRefCounter, scrollCounter, newsTemp, tags, newsRef, namesNews = 0, 0, [], [], [], []
    counter = 0

    xmlData = etree.Element("doc")

    categoryXmlData = etree.SubElement(xmlData, "category")
    categoryXmlData.text = "Все новости"
    categoryXmlData.attrib['verify'] = "true"
    categoryXmlData.attrib['type'] = "str"
    categoryXmlData.attrib['auto'] = "true"

    titleXmlData = etree.SubElement(xmlData, "title")
    titleXmlData.attrib['verify'] = "true"
    titleXmlData.attrib['type'] = "str"
    titleXmlData.attrib['auto'] = "true"

    textXmlData = etree.SubElement(xmlData, "text")
    textXmlData.attrib['verify'] = "true"
    textXmlData.attrib['type'] = "str"
    textXmlData.attrib['auto'] = "true"

    tagsXmlData = etree.SubElement(xmlData, "tags")
    tagsXmlData.attrib['verify'] = "true"
    tagsXmlData.attrib['type'] = "str"
    tagsXmlData.attrib['auto'] = "true"

    counterBar = IncrementalBar("Сбор ссылок", max=counterOfArticles,
                         suffix='%(percent)d%% статей %(remaining)s осталось,'
                                ' Секунд затрачено - %(elapsed)s')
    while counter != counterOfArticles:
        for news in driver.find_element_by_class_name("content-main")\
                .find_elements_by_class_name("inner-news-item"):
            if counter == counterOfArticles:
                break
            newsRef.append(news.find_element_by_tag_name("a").get_attribute("href"))
            tags.append(news.find_element_by_class_name("index-news-date")
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
        driver.get(ref)
        driver.implicitly_wait(1)
        if re.search(r'inopressa', str(ref)):
            for bodyText in driver.find_element_by_class_name("body")\
                    .find_elements_by_class_name("articPar"):
                newsTemp.append(bodyText.text)
        elif re.search(r'newsru', str(ref)):
            for bodyText in driver.find_element_by_class_name("article-text")\
                    .find_elements_by_tag_name("p"):
                newsTemp.append(bodyText.text)
        elif re.search(r'meddaily', str(ref)):
            for bodyText in driver.find_elements_by_class_name("topic_text"):
                newsTemp.append(bodyText.text)

        unionText = ''.join(newsTemp)
        titleXmlData.text = namesNews[parseRefCounter]
        textXmlData.text = etree.CDATA(unionText)
        tagsXmlData.text = tags[parseRefCounter]
        xmlTree = etree.ElementTree(xmlData)
        xmlTree.write(".\\articles\\output " + str(parseRefCounter) + ".xml", encoding="utf-8"
                      , xml_declaration=True, pretty_print=True)
        articleBar.next()
        parseRefCounter = parseRefCounter + 1
        newsTemp.clear()
    articleBar.finish()
    driver.close()
    exit(0)
