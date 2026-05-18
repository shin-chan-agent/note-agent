import os
import time
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def generate_and_post():
    # 1. Geminiで記事を生成（モデルを2.5-flashに固定）
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = "noteに投稿する、クリエイター向けのタメになる面白い記事をタイトル付きで1つ執筆してください。親しみやすく知的なトーンで。"
    response = model.generate_content(prompt)
    
    lines = response.text.split("\n")
    title = lines[0].replace("# ", "").replace("**", "")
    body = "\n".join(lines[1:])

    # 2. Seleniumでnoteに自動投稿（待機処理を強化）
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1200,800')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15) # 最大15秒、画面の読み込みを待つ設定
    
    try:
        # ログイン画面
        driver.get("https://note.com/login")
        
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.send_keys(os.environ["NOTE_EMAIL"])
        driver.find_element(By.NAME, "password").send_keys(os.environ["NOTE_PASS"])
        
        login_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'ログイン') or @type='submit']")
        login_btn.click()
        
        # ログイン後にマイページが読み込まれるのを待つ
        time.sleep(7)
        
        # 投稿画面へ移動
        driver.get("https://note.com/intent/post")
        
        # タイトル入力（h1タグが表示されるまで待つ）
        title_field = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        title_field.send_keys(title)
        
        # 本文入力
        body_field = driver.find_element(By.CLASS_NAME, "ProseMirror")
        body_field.send_keys(body)
        time.sleep(3) # 文字がしっかり入力されるのを少し待つ
        
        # 下書き保存ボタンを名前で探してクリック
        save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '下書き保存')]")))
        save_btn.click()
        
        # 保存完了の余韻を持たせる
        time.sleep(5)
        print("Success: Post saved safely.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    generate_and_post()
