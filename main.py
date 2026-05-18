import os
import time
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def generate_and_post():
    # 1. Geminiで記事を生成
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = "noteに投稿する、クリエイター向けのタメになる面白い記事をタイトル付きで1つ執筆してください。親しみやすく知的なトーンで。"
    response = model.generate_content(prompt)
    
    lines = response.text.split("\n")
    title = lines[0].replace("# ", "").replace("**", "")
    body = "\n".join(lines[1:])

    # 2. Seleniumでnoteに自動投稿（下書き保存）
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get("https://note.com/login")
        time.sleep(3)
        driver.find_element(By.NAME, "email").send_keys(os.environ["NOTE_EMAIL"])
        driver.find_element(By.NAME, "password").send_keys(os.environ["NOTE_PASS"])
        driver.find_element(By.XPATH, "//button[contains(text(), 'ログイン')]").click()
        time.sleep(5)
        
        driver.get("https://note.com/intent/post")
        time.sleep(5)
        
        title_field = driver.find_element(By.TAG_NAME, "h1")
        title_field.send_keys(title)
        
        body_field = driver.find_element(By.CLASS_NAME, "ProseMirror")
        body_field.send_keys(body)
        time.sleep(3)
        
        save_btn = driver.find_element(By.XPATH, "//button[contains(text(), '下書き保存')]")
        save_btn.click()
        time.sleep(3)
        print("Success")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    generate_and_post()
