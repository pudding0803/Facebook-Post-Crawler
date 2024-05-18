import os
import re
import time

import yaml
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager


def normalize_list(ls: list | None) -> list:
    return [] if ls is None else ls


def main():
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
            facebook_email = config['facebook_email']
            facebook_password = config['facebook_password']
            crawl = config['crawl']
            parse = config['parse']
            search_words = normalize_list(config['search_words'])
            latest_posts = config['latest_posts']
            crawling_number = config['crawling_number']
            directory = config['directory']
            regex = config['regex']
            html_filtered_patterns = normalize_list(config['html_filtered_patterns'])
            post_content_filtered_patterns = normalize_list(config['post_content_filtered_patterns'])
    except FileNotFoundError:
        print('❌ Please create the config file first.')
        return
    except KeyError as key:
        print(f'❌ The config file is lacking the variable: {key}.')
        return

    html_filtered_patterns = '|'.join(
        f'({pattern if regex else re.escape(pattern)})' for pattern in html_filtered_patterns
    )
    post_content_filtered_patterns = '|'.join(
        f'({pattern if regex else re.escape(pattern)})' for pattern in post_content_filtered_patterns
    )

    if crawl:
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--incognito')
        options.add_argument('start-maximized')
        options.add_argument("--disable-notifications")
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(f'https://www.facebook.com')
        time.sleep(2)
        driver.find_element(By.XPATH, '//input[@type="text" and @id="email"]').send_keys(facebook_email)
        driver.find_element(By.XPATH, '//input[@type="password" and @id="pass"]').send_keys(facebook_password)
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
                                ".//div[@role='button' and @tabindex='0' and "
                                "(text()='查看更多' or text()='顯示更多')]"
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
        links = []
        for search_word in search_words:
            try:
                with open(f'./{directory}/{search_word}.html', 'r') as file:
                    html = file.read()
            except FileExistsError:
                print(f'❌ The parsed file {search_word}.html does not exist.')
                break
            posts = BeautifulSoup(html, 'html.parser').find_all('div', recursive=False)[:-1]

            for post in posts:
                if html_filtered_patterns and re.search(html_filtered_patterns, post.get_text()):
                    continue
                texts = []
                try:
                    link = post.find('a')['href']
                    group = re.search(r'/groups/(\d+)/', link).group(1)
                    permalink = re.search(r'multi_permalinks=(\d+)', link).group(1)
                    link = f'https://www.facebook.com/groups/{group}/permalink/{permalink}'
                    if link in links:
                        continue
                    links.append((group, permalink))
                    texts.append(f'🔗 貼文網址：{link}\n')
                except AttributeError:
                    texts.append('⚠️ This post does not contain public linkage.')
                except IndexError:
                    texts.append('🚀 Cannot extract the linkage by rule. Please consider reporting it. 💡')

                try:
                    # General posts
                    if divs := post.find_all('div', {'dir': 'auto', 'style': 'text-align: start;'}):
                        for div in divs:
                            text = ''
                            for child in div.children:
                                if isinstance(child, str):
                                    text += child
                                elif img := child.find('img'):
                                    text += img['alt']
                                elif a := child.find('a'):
                                    text += a.text
                                else:
                                    text += child.string
                            texts.append(text)
                    # The posts with some rich text
                    elif divs := post.find('div', {'dir': 'auto'}) \
                            .find('div', recursive=False).find('span', recursive=False):
                        divs = divs.find_all('div')
                        for div in divs:
                            span = div.find('span', recursive=False)
                            text = ''
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
                                    text += child.string
                            texts.append(text)
                    # The posts with background
                    elif div := post.find('div', {'dir': 'auto'}).find('div').find('div').find('div') \
                            .find_all('div')[1].find_all('div')[1]:
                        text = ''
                        for child in div.children:
                            if isinstance(child, str):
                                text += child
                            elif img := child.find('img'):
                                text += img['alt']
                            elif a := child.find('a'):
                                text += a.text
                            elif child.name == 'br':
                                pass
                            else:
                                text += child.string
                        texts.append(text)
                except Exception as error:
                    texts.append('🚀 The structure of the post has not been supported yet. '
                                 'Please consider reporting it. 💡')
                    texts.append(str(error))

                content = '\n'.join(texts)
                if not post_content_filtered_patterns or not re.search(post_content_filtered_patterns, content):
                    print(content + '\n\n' + '=' * 100 + '\n')


if __name__ == '__main__':
    main()
