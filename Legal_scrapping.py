from bs4 import BeautifulSoup
import urllib
import sys
import random
from urllib.request import urlopen
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

sys.setrecursionlimit(200000)

desktop_agents = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']

class Scrapping:

    def __init__(self, website_url):
        self.url = website_url
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--blink-settings=imagesEnabled=false')
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    def random_headers(self):
        return {'User-Agent': random.choice(desktop_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}

    def get_json_request(self, url):
        req = urllib.request.Request(url, headers=self.random_headers())
        r = urllib.request.urlopen(req)
        beautifulsoup = BeautifulSoup(r, "lxml")
        return beautifulsoup

    def extractIssueInformation(self, url):
        issueDict_list = []
        project_soup = self.get_json_request(url)
        issues = project_soup.find_all("div", {"class": "al-article-list-group"})
        if len(issues) == 0:
            issues = project_soup.find_all("div", {"class": "section-container"})
        for issue in issues:
            for child in issue.children:
                try:
                    articles = child.find_all('div', {'class': 'al-article-items'})
                    for article in articles:
                        try:
                            dict = {}
                            title = self.extractIssueInformation_Title(article)
                            authors = self.extractIssueInformation_Authors(article)
                            citation = self.extractIssueInformation_citation(article)
                            abstract = self.getAbstract(citation['Link'])
                            published_date = self.getPublication_date(citation['Link'])
                            dict['Title'] = title
                            dict['Authors'] = authors
                            dict['Abstract'] = abstract
                            dict['Published Date'] = published_date
                            dict.update(citation)
                            issueDict_list.append(dict)
                        except:
                            continue
                except:
                    continue
        return issueDict_list

    def saveData(self, dict_list):
        path = 'Data/'
        df = pd.DataFrame(dict_list)
        df.to_csv(path + '/LegalIssues.csv')

    def remove_newlines(self, text):
        return text.strip()

    def splitString(self, text, sep):
        return text.split(sep)

    def extractIssueInformation_Title(self, child):
        try:
            title = child.find_all("h5", {"class": 'customLink item-title'})[0].text
            tilte = self.remove_newlines(title)
            return tilte
        except:
            return ""

    def extractCitationDict(self, citation_list):
        dict = {}
        dict["Journal Title"] = citation_list[0]
        dict["Volume"] = citation_list[1]
        if "Issue" in citation_list[2]:
            dict["Issue"] = citation_list[2]
            dict["Year"] = citation_list[3]
            dict["Pages"] = citation_list[4]
            dict["Link"] = citation_list[5]
        else:
            dict["Issue"] = ""
            dict["Year"] = citation_list[2]
            dict["Pages"] = citation_list[3]
            dict["Link"] = citation_list[4]
        return dict

    def extractIssueInformation_Authors(self, child):
        authors = child.find_all("div", {"class": 'al-authors-list'})
        try:
           author = self.remove_newlines(authors[0].text)
           authorlist = self.splitString(author, ",")
           return authorlist
        except:
            return []

    def extractIssueInformation_citation(self, child):
        try:
            authors = child.find_all("div", {"class": 'ww-citation-primary'})
            author = self.remove_newlines(authors[0].text)
            citation_list = self.splitString(author, ",")
            citation_dict = self.extractCitationDict(citation_list)
            return citation_dict
        except:
            return []

    def getissueIdentifer(self, url):
        project_soup = self.get_json_request(url)
        identifier = project_soup.find_all("h1", {"class": "issue-identifier"})
        return identifier.text

    def getAbstract(self, url):
        self.driver.get(url)
        abstarct_ele = self.driver.find_element_by_class_name("abstract")
        try:
            return abstarct_ele.text
        except:
            return ""

    def getPublication_date(self, url):
        self.driver.get(url)
        publication_ele = self.driver.find_element_by_class_name("ww-citation-date-wrap")
        try:
            publication_date = self.splitString(publication_ele.text, ":")
            return publication_date[1]
        except:
            return ""

    def getsubIssues(self, url):
        sublinks = []
        project_soup = self.get_json_request(url)
        issues = project_soup.find_all("div", {"class": "single-dropdown-wrap dropdown-issue"})
        totalIssues = issues[0].find_all('option')
        for issueLink in totalIssues:
            sublinks.append(issueLink.attrs['value'])
        return sublinks

    def getMainIssuelink(self):
        issueLink = []
        years_link = []
        project_soup = self.get_json_request(self.url)
        issues = project_soup.find_all("div", {"class": "single-dropdown-wrap dropdown-year"})
        for issue in issues[0].children:
            try:
                totalIssues = issue.find_all('option')
                for link in totalIssues:
                    issueLink.append(link.attrs['value'])
                    years_link.append(link.text)
                return issueLink, years_link
            except:
                print("No isssues")

    def get_Journal_of_Legal_Analysis(self):
        totalIssueLinks = self.getMainIssuelink()
        issueLinks = totalIssueLinks[0]
        totalSubIssues = []
        final_information_list = []
        for subIssue in issueLinks:
            totalSubIssues.append(self.getsubIssues('https://academic.oup.com/' + subIssue))
        for subissues in totalSubIssues:
            for subissue in subissues:
                information_list = self.extractIssueInformation('https://academic.oup.com/' + subissue)
                final_information_list.extend(information_list)
        df = pd.DataFrame(final_information_list)
        self.saveData(df)

if __name__ == '__main__':
    obj = Scrapping('https://academic.oup.com/jla/issue')
    obj.get_Journal_of_Legal_Analysis()