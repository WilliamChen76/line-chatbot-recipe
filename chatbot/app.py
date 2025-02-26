from flask import Flask, request, abort
import requests
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
HF_API_KEY = os.getenv("HF_API_KEY")  # 改用環境變數

# 替換為你的 Channel Access Token & Secret
LINE_ACCESS_TOKEN = "3GF9S76wI6xYh7+ucK4Ozd0nFDtUlq8EHNBBGxweukbVtouM7D4j9mKwG/RfQ7dHwSQ5EadKDjyXwHNGiinh4mupLlNjCBfHiRS8WahnXMJUlTQ/rqOVim8BSjNcwuODm80i8pXpEHA9/p82ZYK6YwdB04t89/1O/w1cDnyilFU="
LINE_SECRET = "7feba977d46a33dd29b6915e540a4905"

app = Flask(__name__)
CORS(app)  # 允許所有跨域請求
@app.route("/")
def home():
    return "AI Recipe Chatbot is running!", 200  # 回應 200 OK，Render 才會認為健康狀態正常

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# Hugging Face API 設定
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

def query_huggingface(prompt, max_retries=5):
    """向 Hugging Face API 發送請求，並加入重試機制"""
    
    for attempt in range(max_retries):
        response = requests.post(API_URL, headers=HEADERS, json={"inputs": prompt})
        
        # 如果請求成功 (200)，返回生成的文字
        if response.status_code == 200:
            result = response.json()
            
            # 確保 response 格式正確
            if isinstance(result, list) and "generated_text" in result[0]:
                return result[0]["generated_text"]
            else:
                return "Error: Unexpected API response format"
        
        # 如果模型超載，等待 10 秒再試
        elif response.status_code == 503 or ("error" in response.json() and response.json()["error_type"] == "overloaded"):
            print(f"[Retry {attempt+1}/{max_retries}] Model is overloaded. Retrying in 10 seconds...")
            time.sleep(10)
        
        # 其他錯誤（如 500, 429），等待 5 秒再試
        else:
            print(f"[Retry {attempt+1}/{max_retries}] Error {response.status_code}: {response.text}. Retrying in 5 seconds...")
            time.sleep(5)
    
    return "Sorry, the AI is currently unavailable. Please try again later."

# 測試
print(query_huggingface("Give me a simple recipe"))


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text  # 用戶輸入的食材

    # 🔹 動態生成 Prompt，讓 AI 根據用戶提供的食材生成食譜
    prompt = f"""You are a professional chef. Based on the following ingredients, create a healthy and delicious recipe. Include a title, ingredients list, and step-by-step cooking instructions.

    Ingredients: {user_input}

    Make sure the recipe is easy to follow and provides a balanced meal."""

    # 送入 Hugging Face API
    llm_reply = query_huggingface(prompt)

    # 回應用戶
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=llm_reply))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # 讀取 Render 設定的 PORT
    app.run(host="0.0.0.0", port=port)
