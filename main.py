import os
import time
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def generate_and_post():
    # 1. Geminiで記事を生成
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = "noteに投稿する、クリエイター向けのタメになる面白い記事をタイトル付きで1つ執筆してください。親しみやすく知的なトーンで。"
    response = model.generate_content(prompt)
    
    lines = response.text.split("\n")
    title = lines[0].replace("# ", "").replace("**", "")
    body = "\n".join(lines[1:])

    # 2. Seleniumでnoteに自動投稿（ロボット検知回避を最大化）
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1200,800')
    
    # 【超重要】普通の人間用のブラウザだと偽装する設定
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled') # 「自動操作されてます」のフラグを隠す
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)
    
    # 完全にロボットの痕跡を消す呪文を実行
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    wait = WebDriverWait(driver, 25) # 待ち時間をさらに伸ばして25秒に
    
    try:
        # まずは一度普通のトップページを踏んでからログインに向かう（怪しまれない足跡をつける）
        driver.get("https://note.com/")
        time.sleep(5)
        
        # 直接ログイン画面へ
        driver.get("https://note.com/login/v2")
        time.sleep(5)
        
        # メールアドレス入力欄を色々な方法で必死に探す
        email_field = None
        for element_identifier in [
            (By.NAME, "email"),
            (By.XPATH, "//input[@type='email']"),
            (By.XPATH, "//input[contains(@placeholder, 'メールアドレス')]")
        ]:
            try:
                email_field = wait.until(EC.presence_of_element_located(element_identifier))
                if email_field:
                    break
            except:
                continue
                
        if not email_field:
            raise Exception("Note login page could not be loaded or was blocked by bot detection.")
            
        # 入力処理
        email_field.send_keys(os.environ["NOTE_EMAIL"])
        driver.find_element(By.NAME, "password").send_keys(os.environ["NOTE_PASS"])
        time.sleep(2)
        
        # フォーム送信でログイン実行
        email_field.submit()
        
        # ログイン後の読み込みをじっくり待つ
        time.sleep(12)
        
        # 投稿画面へ移動
        driver.get("https://note.com/intent/post")
        
        # タイトル入力
        title_field = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        title_field.send_keys(title)
        
        # 本文入力
        body_field = driver.find_element(By.CLASS_NAME, "ProseMirror")
        body_field.send_keys(body)
        time.sleep(5)
        
        # 下書き保存ボタンを探してクリック
        save_btn = None
        for xpath in [
            "//button[contains(., '下書き保存')]",
            "//button[contains(text(), '下書き保存')]",
            "//button[@data-testid='draft-save-button']"
        ]:
            try:
                save_btn = driver.find_element(By.XPATH, xpath)
                if save_btn:
                    break
            except:
                continue
                
        if save_btn:
            save_btn.click()
            time.sleep(5)
            print("Success: Post saved safely.")
        else:
            raise Exception("Save button not found.")
        
    except Exception as e:
        print(f"Error: {e}")
        raise e
    finally:
        driver.quit()

if __name__ == "__main__":
    generate_and_post()
