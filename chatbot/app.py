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

def query_huggingface(prompt):
    """向 Hugging Face API 發送請求"""
    response = requests.post(API_URL, headers=HEADERS, json={"inputs": prompt})

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")  # Debug
        return "Sorry, the AI is currently unavailable. Please try again later."

    return response.json()[0]["generated_text"]

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
