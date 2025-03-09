# from flask import Flask, request, abort, jsonify
# from flask_cors import CORS
# from linebot import LineBotApi
# from linebot.v3 import WebhookHandler
# from linebot.v3.exceptions import InvalidSignatureError
# from linebot.v3.webhooks import MessageEvent, TextMessageContent, TextSendMessage
# import os
# from RAG import chat_with_model  # 匯入 RAG 的 chat_with_model

# # LINE 設定
# LINE_ACCESS_TOKEN = "3GF9S76wI6xYh7+ucK4Ozd0nFDtUlq8EHNBBGxweukbVtouM7D4j9mKwG/RfQ7dHwSQ5EadKDjyXwHNGiinh4mupLlNjCBfHiRS8WahnXMJUlTQ/rqOVim8BSjNcwuODm80i8pXpEHA9/p82ZYK6YwdB04t89/1O/w1cDnyilFU="
# LINE_SECRET = "7feba977d46a33dd29b6915e540a4905"

# app = Flask(__name__)
# CORS(app)

# @app.route("/", methods=["GET", "HEAD"])
# def home():
#     return jsonify({"message": "Hello, this is your chatbot API!"})

# line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
# handler = WebhookHandler(LINE_SECRET)

# @app.route("/callback", methods=["POST"])
# def callback():
#     signature = request.headers["X-Line-Signature"]
#     body = request.get_data(as_text=True)
#     try:
#         handler.handle(body, signature)
#     except InvalidSignatureError:
#         abort(400)
#     return "OK"

# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     user_id = event.source.user_id  # 獲取用戶 ID
#     user_input = event.message.text  # 用戶輸入

#     # 初始回應，告知用戶正在處理
#     line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Generating your recipe, please wait..."))

#     # 使用 RAG 的 chat_with_model 獲取回應
#     response_text = chat_with_model(user_id, user_input)

#     # 確保回應在 LINE 4000 字元限制內
#     max_length = 4000
#     response_text = response_text[:max_length]

#     # 使用 push_message 發送最終回應
#     line_bot_api.push_message(user_id, TextSendMessage(text=response_text))

# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)

from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from linebot.v3.messaging import MessagingApi, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent
import os
from RAG import chat_with_model  # 匯入 RAG 的 chat_with_model

# LINE 設定
LINE_ACCESS_TOKEN = "3GF9S76wI6xYh7+ucK4Ozd0nFDtUlq8EHNBBGxweukbVtouM7D4j9mKwG/RfQ7dHwSQ5EadKDjyXwHNGiinh4mupLlNjCBfHiRS8WahnXMJUlTQ/rqOVim8BSjNcwuODm80i8pXpEHA9/p82ZYK6YwdB04t89/1O/w1cDnyilFU="
LINE_SECRET = "7feba977d46a33dd29b6915e540a4905"

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET", "HEAD"])
def home():
    return jsonify({"message": "Hello, this is your chatbot API!"})

# 初始化 LINE Bot
line_bot_api = MessagingApi(LINE_ACCESS_TOKEN) #
handler = WebhookHandler(LINE_SECRET)

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
    user_id = event.source.user_id  # 獲取用戶 ID
    user_input = event.message.text  # 用戶輸入

    # 初始回應，告知用戶正在處理
    line_bot_api.reply_message(
        event.reply_token,
        messages=[TextMessage(text="Generating your recipe, please wait...")]
    )

    # 使用 RAG 的 chat_with_model 獲取回應
    response_text = chat_with_model(user_id, user_input)

    # 確保回應在 LINE 4000 字元限制內
    max_length = 4000
    response_text = response_text[:max_length]

    # 使用 push_message 發送最終回應
    line_bot_api.push_message(
        to=user_id,
        messages=[TextMessage(text=response_text)]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
