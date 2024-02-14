import re
from stopWords import STOPWORDS
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup

UNIQUES = set()
LONGEST = (0, "")

def scraper(url, resp):
    global UNIQUES
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link, UNIQUES)]

def extract_next_links(url, resp):
    global UNIQUES, LONGEST
    url_list = list()

    # Check for empty sites
    try:
        if url == None or resp == None or resp.raw_response.content == None:
            return url_list
    except:
        pass
    
    # Verify response status is valid
    if not (resp.status == 200):
        # Check for permanent redirection
        # If valid get new location from redirection
        # Else return
        if not (resp.status == 301):
            print(resp.status)
            return url_list
        redirectedUrl = resp.url
        url = redirectedUrl
        
    # Convert text to usable format
    raw_text = resp.raw_response.text
    parsed_text = BeautifulSoup(raw_text,'html.parser')
    
    # Check large file
    if checkLargeFile(resp.raw_response):
        return url_list
    
    # Check if low value page
    if checkLowInformation(parsed_text):
        return url_list
    
    # Add html text to file
    writeHTMLData(parsed_text)
    # Check if it is the new longest page
    wordCount = len(parsed_text.get_text().split())
    if wordCount > LONGEST[0]:
        LONGEST = (wordCount, url)
    
    # Extract links from text
    for item in parsed_text.find_all('a'):
        link = item.get('href') # Get link
        # Turn link to url object
        parsed_link = urlparse(link.strip())
        # Remove fragment
        parsed_link = removeFragment(parsed_link)
        # Check valid link
        if is_valid(urlunparse(parsed_link), UNIQUES):
            # Add link
            UNIQUES.add(urlunparse(parsed_link))
            url_list.append(urlunparse(parsed_link))

    return url_list

def removeFragment(parsedUrl: urlparse) -> urlparse:
    # Remove fragment
    newURL = parsedUrl._replace(fragment='')
    
    return newURL

def checkValidUCIHost(parsedUrl: urlparse) -> bool:
    # Check if URL has a hostname
    if not parsedUrl.netloc:
        return False
    
    VALIDS = ["stat", "informatics", "cs", "ics"]
    
    # Splits URL by "."
    urlParts = parsedUrl.netloc.split(".")
    # Check if URL has at least 4 parameters ("www", domain name, "uci", "edu")
    if len(urlParts) != 4:
        return False
    # Grab important parts of URL
    urlDomain = urlParts[1]
    urlSchool = urlParts[2]
    urlEnd = urlParts[3]
    # Check if URL parts contain all the valid components
    if (urlDomain in VALIDS and urlSchool == "uci" and urlEnd == "edu"):
        return True

    return False
        

def is_valid(url, uniques):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        url = url.strip()
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not checkValidUCIHost(parsed):
            return False
        # Check dupliates but different schemes
        if parsed.scheme == 'http':
            newParsedUrl = 'https://' + parsed.netloc + parsed.path
            if newParsedUrl in uniques:
                return False
        else:
            newParsedUrl = 'http://' + parsed.netloc + parsed.path
            if newParsedUrl in uniques:
                return False
        # Check if query ends in file type
        if re.match(r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|txt"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|ppsx"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.query.lower()):
            return False
        # Check if path contains directory of file
        if re.search(r"\/(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|txt"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|ppsx"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)\/", parsed.path.lower()):
            return False
        # Check if path ends in file type
        return not re.match(    
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|txt"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|ppsx"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def getUniques():
    return UNIQUES

def writeUniquesReport():
    # Create a file in "reports/uniquesReport.txt" with number of unique links and the links
    with open('reports/uniquesReport.txt', 'w') as uniquesReport:
        uniquesReport.write("Number of unique pages: " + str(len(UNIQUES)) + "\n")
        for i in getUniques():
            uniquesReport.write(i+"\n")
            
def writeLongestReport():
    # Create a file in "reports/longestReport.txt" with link with most text and number of words
    with open('reports/longestReport.txt', 'w') as longestReport:
        words = LONGEST[0]
        URL = LONGEST[1]
        longestReport.write(f'{URL} - {words}')

def clearHTMLData():
    # Make file empty
    with open('reports/HTMLReport.txt', 'w'):
        pass
            
def writeHTMLData(htmlData):
    # Add HTML text to file
    with open('reports/HTMLReport.txt', 'a', encoding="utf-8") as HTMLReport:
        HTMLReport.write(htmlData.get_text())

def tokenize(TextFilePath: str) -> list[str]:
    with open(TextFilePath, 'r', encoding='utf-8') as textFile:
        tokens = []
        char = textFile.read(1).lower()
        token = ""
        while char:
            try:
                # Check if an english alphabet character or number
                if 97 <= ord(char) <= 122 or char.isnumeric():
                    token += char
                else:
                    if token:
                        tokens.append(token)
                        token = ""

                char = textFile.read(1).lower()
            except Exception as e:
                # If error occurs skip character and continue
                tokens.append(token)
                token = ""
                char = textFile.read(1).lower()
                continue

        if token:
            tokens.append(token)

        return tokens

def checkStopWord(token):
    if token in STOPWORDS:
        return True
    return False

def computeWordFrequencies(tokens: list[str]) -> dict[str, int]:
    frequencies = {}
    for token in tokens:
        # If token is a stop word skip
        if checkStopWord(token):
            continue
        # If 1 characters
        if len(token) == 1:
            continue 
        # If seen increment token count
        if token in frequencies:
            frequencies[token] += 1
        # Else add to frequencies dictionary
        else:
            frequencies[token] = 1

    return frequencies

def writeFiftyCommonWordsReport():
    tokens = tokenize("reports/HTMLReport.txt")
    frequencies = computeWordFrequencies(tokens)
    with open("reports/commonWordsReport.txt", "w") as commonWords:
        for tokenKey in sorted(frequencies, key=lambda x: frequencies[x], reverse=True)[:50]:
            commonWords.write(f"{tokenKey} - {str(frequencies[tokenKey])}" + "\n")

def checkLowInformation(parsed_text):
    THRESHOLD = 300
    wordCount = len(parsed_text.get_text().split())
    if wordCount < THRESHOLD:
        return True
    else:
        return False
    
def checkLargeFile(rawResponse):
    MAXSIZE = 10 * 1024 * 1024  # 10 MB threshold
    contentLength = int(rawResponse.headers.get("Content-Length", 0))
    
    # Check if the file size exceeds the maximum size
    if contentLength > MAXSIZE:
        return True
    return False
