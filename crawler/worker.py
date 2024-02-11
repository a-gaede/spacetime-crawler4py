from threading import Thread

from inspect import getsource
from utils.download import download
from urllib.parse import urlparse, urlunparse
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.subdomains = {}
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def addSubdomain(self, url: str) -> None:
        # Turn URL to URLPARSE object
        parsed = urlparse(url)
        try:
            # Create URL string in form https://subdomain.domainname.uci.edu
            URL = f'{parsed.scheme}://{parsed.hostname}'
            # If subdomain for URL exists in dictionary, append it to the list of links with the same subdomain
            if URL in self.subdomains:
                self.subdomains[URL].append(urlunparse(parsed))
            # Subdomain not in dicitonary, add it with the link in a list as the value
            else:
                self.subdomains[URL] = [urlunparse(parsed)]
        except:
            pass
    
    def getSubdomainList(self) -> list[str]:
        # Create a list in format (subdomain, number of links with that subdomain)
        subdomainList = []
        for key in self.subdomains:
            subdomainList.append(f'{key}, {len(self.subdomains[key])}')
        return sorted(subdomainList, key=lambda x: x.split("//")[-1])

    def writeSubdomainReport(self, subdomainList: list[str]) -> None:
        # Create a file in "reports/subdomainReport.txt" with list of subdomains and number of sites
        with open('reports/subdomainReport.txt', 'w') as subdomainReport:
            subdomainReport.write("Number of subdomains: " + str(len(subdomainList)) + "\n")
            for i in subdomainList:
                subdomainReport.write(i+"\n")
    
    def createAllReports(self):
        self.writeSubdomainReport(self.getSubdomainList())
        scraper.writeUniquesReport()
        scraper.writeFiftyCommonWordsReport()
        scraper.writeLongestReport()
        
    def run(self):
        scraper.clearHTMLData()
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            self.addSubdomain(tbd_url)
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
        self.createAllReports()
