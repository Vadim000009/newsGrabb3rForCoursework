import selenium
from lxml import etree
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
import driver


def initDriverChrome():
    chromedriver = r"C:\Users\1\PycharmProjects\untitled\chromedriver.exe"
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(executable_path=chromedriver, options=options)
    return driver


def check_exists_by_class(driver):
    try:
        driver.find_element_by_class_name("article-text").find_element_by_tag_name("p")
    except NoSuchElementException:
        return False
    return True

def check_exists_by_MEDaily(driver):
    try:
        driver.find_element_by_class_name("topic_text")
    except NoSuchElementException:
        return False
    return True

def check_exists_by_Inopressa(driver):
    try:
        driver.find_element_by_class_name("topic").find_element_by_class_name("body")\
            .find_elements_by_class_name("articPar")
    except NoSuchElementException:
        return False
    return True

if __name__ == "__main__":
    counter = 0
    driver = driver.initDriverChrome()
    driver.get("https://txt.newsru.com/allnews/")
    driver.implicitly_wait(1)

    button = driver.find_element_by_class_name("arch-arrows-link-l")

    parseRefCounter, scrollCounter, newsTemp, tags, newsRef, namesNews = 0, 0, [], [], [], []

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

    print("counter ref")
    while counter != 16:
        for news in driver.find_element_by_class_name("content-main")\
                .find_elements_by_class_name("inner-news-item"):
            if counter == 16:
                break
            newsRef.append(news.find_element_by_tag_name("a").get_attribute("href"))
            tags.append(news.find_element_by_class_name("index-news-date")
                        .find_element_by_tag_name("a").text)
           # Неправильно передаёт теги, необходимо доработать
            namesNews.append(news.find_element_by_class_name("index-news-title").text)
            counter = counter + 1
            print(counter)
        print("fin")
        if counter > 16:
            break
        try:
            ActionChains(driver).move_to_element(button).click().perform()
        except selenium.common.exceptions.StaleElementReferenceException:
            button = driver.find_element_by_class_name("arch-arrows-link-l")
            ActionChains(driver).move_to_element(button).click().perform()

    print("counter Ready")
    for ref in newsRef:
        driver.get(ref)
        # driver.implicitly_wait(1)
        if check_exists_by_Inopressa(driver):
            for news in driver.find_element_by_class_name("body")\
                    .find_elements_by_class_name("articPar"):
              # Скипает Инопрессу, доделать
                newsTemp.append(news.text)
        elif check_exists_by_class(driver):
            for bodyText in driver.find_element_by_class_name("article-text")\
                    .find_elements_by_tag_name("p"):
                newsTemp.append(bodyText.text)
        else:
            for bodyText in driver.find_elements_by_class_name("topic_text"):
                newsTemp.append(bodyText.text)
        unionText = ''.join(newsTemp)
        titleXmlData.text = namesNews[parseRefCounter]
        textXmlData.text = etree.CDATA(unionText)
        tagsXmlData.text = tags[parseRefCounter]
        xmlTree = etree.ElementTree(xmlData)
        xmlTree.write("output " + str(parseRefCounter) + ".xml", encoding="utf-8"
                      , xml_declaration=True, pretty_print=True)
        print(parseRefCounter)
        parseRefCounter = parseRefCounter + 1
        newsTemp.clear()
    driver.close()
