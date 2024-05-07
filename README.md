# Facebook 貼文爬蟲常數說明文件

## 原理

### 爬取
1. 開啟瀏覽器並登入
2. 搜尋關鍵字並進行篩選設定
3. 點開每則貼文的「更多」，並記錄 HTML
4. 持續將頁面下滾、載入貼文後重複動作
5. 最後存下貼文的部分 HTML 內容

### 解析
1. 透過爬取後存下的 HTML 檔案解析
2. 於終端機輸出特定資料

### 特色(?)
> 雖然 HTML 檔案較為龐大（Facebook 會亂加東西反爬蟲），但我盡量不使用奇怪的 class 來找 tag，或許可以撐過比較多版本(?)

## 套件安裝

```shell
pip install beautifulsoup4 python-dotenv selenium tqdm
```

## 環境變數

```shell
cp .env.example .env
```

### `.env`
- 請設定 Facebook 之帳號密碼（不需經由驗證之帳號）
- 較不建議使用主帳號，過於頻繁登入有可能會被封鎖（不確定）

## 常數

### `main.py`
- 爬取與解析
  - `crawl`：是否進行爬取，並存下貼文的部分 HTML。
  - `parse`：是否解析 HTML 檔並輸出爬取的內容，目前只有輸出貼文連結與文章內容，須已爬取過才能解析。
- 爬取相關設定
  - `search_words`：要在 Facebook 中搜尋的關鍵字。
  - `latest_posts`：是否從最新文章開始爬取。
  - `crawling_number`：預計爬取的貼文數量（每組關鍵字獨立計算）。
  - `directory`：爬取貼文之部分 HTML 檔案的儲存位置。
- 解析相關設定
  - `basic_filtered_patterns`：要排除的字詞，支援 Regex 語法，排除範圍包含整個貼文。
  - `advanced_filtered_patterns`：要排除的字詞，支援 Regex 語法，排除範圍包含整個貼文。

### 備註
  - 由於 Facebook 的貼文是動態載入，因此爬取需要花上一定的時間（最多約為貼文數量 × 3 秒）。
  - 最終數量有可能比 `crawling_number` 多出 1 ~ 3 篇左右。
  - `basic_filtered_patterns` 與 `advanced_filtered_patterns` 無異，僅供使用者自由設定。
  - 要排除的字詞請盡量嚴格，實際上是包含 HTML 內容的。
  - 爬取期間請保持瀏覽器開啟。

### 範例
```python
crawl = True
parse = True
search_words = ['租補', '租屋補助']
latest_posts = True
crawling_number = 50
directory = 'posts'
basic_filtered_patterns = ['已關閉這則貼文的回應功能。', '(禁|無)租屋?補助?']
advanced_filtered_patterns = []
```