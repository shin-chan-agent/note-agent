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

    # 2. Seleniumでnoteに自動投稿（ログイン処理を強化）
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1200,800')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # ログイン画面を開く
        driver.get("https://note.com/login")
        
        # メールアドレスとパスワードを入力
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.send_keys(os.environ["NOTE_EMAIL"])
        driver.find_element(By.NAME, "password").send_keys(os.environ["NOTE_PASS"])
        
        # 【修正ポイント】確実な方法でログインボタンを探して押す
        # フォームの送信機能を使ってログインを実行させるよ
        email_field.submit()
        
        # ログイン後のマイページ移動をしっかり待つ
        time.sleep(10)
        
        # 投稿画面へ移動
        driver.get("https://note.com/intent/post")
        
        # タイトル入力
        title_field = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        title_field.send_keys(title)
        
        # 本文入力
        body_field = driver.find_element(By.CLASS_NAME, "ProseMirror")
        body_field.send_keys(body)
        time.sleep(5)
        
        # 下書き保存ボタンをいくつかのパターンで探してクリックする
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
        # エラーが起きたら何が原因か強制的にエラーを出して記録する
        raise e
    finally:
        driver.quit()

if __name__ == "__main__":
    generate_and_post()
