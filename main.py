import os
import re
import time

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager


def main():
    load_dotenv()
    crawl = True
    parse = True
    search_words = []
    latest_posts = True
    crawling_number = 50
    directory = 'posts'
    basic_filtered_patterns = []
    advanced_filtered_patterns = []
    filtered_patterns = '|'.join(f'({word})' for word in basic_filtered_patterns + advanced_filtered_patterns)

    if crawl:
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--incognito')
        options.add_argument('start-maximized')
        options.add_argument("--disable-notifications")
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(f'https://www.facebook.com')
        time.sleep(2)
        driver.find_element(By.XPATH, '//input[@type="text" and @id="email"]').send_keys(os.getenv('FB_EMAIL'))
        driver.find_element(By.XPATH, '//input[@type="password" and @id="pass"]').send_keys(os.getenv('FB_PASSWORD'))
        time.sleep(1)
        driver.find_element(By.XPATH, '//button[@name="login"]').click()
        time.sleep(2)

        for search_word in search_words:
            driver.get(f'https://www.facebook.com/search/posts?q={search_word}')
            time.sleep(2)
            if latest_posts:
                driver.find_element(By.XPATH, '//input[@type="checkbox" and @aria-label="最新貼文"]').click()
                time.sleep(3)

            html = []
            index = 1
            with tqdm(desc='Loading Posts', total=crawling_number, unit='roll') as pbar:
                body = driver.find_element(By.TAG_NAME, 'body')
                post_area = driver.find_element(By.XPATH, "//div[@role='feed']")
                while len(html) < crawling_number:
                    body.send_keys(Keys.END)
                    time.sleep(2)
                    posts = post_area.find_elements(By.XPATH, "./div")[:-1]
                    while index <= len(posts):
                        post = posts[index - 1].find_element(By.XPATH, f".//div[@aria-posinset='{index}']")
                        try:
                            more = post.find_element(
                                By.XPATH,
                                ".//div[@role='button' and @tabindex='0' and (text()='查看更多' or text()='顯示更多')]"
                            )
                            ActionChains(driver).move_to_element(more).click().perform()
                            time.sleep(1)
                        except NoSuchElementException:
                            pass
                        except Exception as error:
                            print(index, error)
                        html.append(post.get_attribute('outerHTML'))
                        index += 1
                        pbar.update()
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(f'./{directory}/{search_word}.html', 'w') as file:
                file.write('\n'.join(html))
        time.sleep(3)
        driver.quit()

    if parse:
        for search_word in search_words:
            try:
                with open(f'./{directory}/{search_word}.html', 'r') as file:
                    html = file.read()
            except FileExistsError:
                print(f'The parsed file {search_word}.html does not exist.')
                break
            posts = BeautifulSoup(html, 'html.parser').find_all('div', recursive=False)[:-1]
            for post in posts:
                if re.search(filtered_patterns, post.get_text()):
                    continue
                try:
                    link = post.find('a')['href']
                    group = re.search(r'/groups/(\d+)/', link).group(1)
                    permalink = re.search(r'multi_permalinks=(\d+)', link).group(1)
                    print(f'https://www.facebook.com/groups/{group}/permalink/{permalink}')
                except AttributeError:
                    print('This post does not contain public linkage.')
                except IndexError:
                    print('Cannot extract the linkage by rule.')

                text = ''
                divs = post.find_all('div', {'dir': 'auto', 'style': 'text-align: start;'})
                if len(divs) > 0:
                    for div in divs:
                        for child in div.children:
                            if isinstance(child, str):
                                text += child
                            elif img := child.find('img'):
                                text += img['alt']
                            elif a := child.find('a'):
                                text += a.text
                            else:
                                print(child)
                        text += '\n'
                else:
                    divs = (post.find('div', {'dir': 'auto'})
                            .find('div', recursive=False).find('span', recursive=False).find_all('div'))
                    text = ""
                    for div in divs:
                        span = div.find('span', recursive=False)
                        for child in span.children:
                            if isinstance(child, str):
                                text += child
                            elif img := child.find('img'):
                                text += img['alt']
                            elif a := child.find('a'):
                                text += a.text
                            elif b := child.find('b'):
                                text += b.text
                            elif child.name == 'br':
                                pass
                            else:
                                print(child)
                        text += '\n'
                print(text)
                print()


if __name__ == '__main__':
    main()
