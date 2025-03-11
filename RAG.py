# RAG.py
import os
import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import openai
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# ----------------------------------------- 
# 🔹 初始化全局變數
# ----------------------------------------- 
# FIREBASE_CRED_PATH = "C:/Users/user/anaconda3/line-chatbot-recipe/chatbot/api1.env.txt"
# CSV_PATH = "C:/Users/user/anaconda3/line-chatbot-recipe/chatbot/RecipeNLG_dataset.csv"
CSV_PATH = "RecipeNLG_dataset.csv"
FAISS_INDEX_PATH = "recipe_faiss.index"
METADATA_PATH = "recipe_metadata.csv"

# Load environment variables
load_dotenv(FIREBASE_CRED_PATH)
openai_api_key = os.getenv("OPENAI_API_KEY")
# firebase_cred_path = "C:/Users/user/anaconda3/line-chatbot-recipe/chatbot/ai-recipe-87c0b-firebase-adminsdk-fbsvc-1abcfa88d1.json"
firebase_cred_json = os.getenv("FIREBASE_CREDENTIALS")

if not openai_api_key:
    raise ValueError("❌ OPENAI_API_KEY not found! Check your .env file.")

# Initialize Firebase
# if not firebase_admin._apps:
#     cred = credentials.Certificate(firebase_cred_path)
#     firebase_admin.initialize_app(cred)
if firebase_cred_json:
    cred = credentials.Certificate(json.loads(firebase_cred_json))
else:
    raise ValueError("Firebase credentials not found in environment variables.")
db = firestore.client()

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load recipe dataset and FAISS index
if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(METADATA_PATH):
    index = faiss.read_index(FAISS_INDEX_PATH)
    df = pd.read_csv(METADATA_PATH)
else:
    df = pd.read_csv(CSV_PATH, nrows=10000)
    df["text"] = df.apply(lambda row: f"Title: {row['title']}\nIngredients: {row['ingredients']}\nInstructions: {row['directions']}", axis=1)
    df["embedding"] = df["text"].apply(lambda x: model.encode(x, convert_to_numpy=True))
    embeddings = np.vstack(df["embedding"].values)
    embedding_dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(embedding_dim)
    index.add(embeddings)
    faiss.write_index(index, FAISS_INDEX_PATH)
    df.to_csv(METADATA_PATH, index=False)

# ----------------------------------------- 
# 🔹 Firestore 函數
# ----------------------------------------- 
def get_user_data(user_id):
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    return user_doc.to_dict() if user_doc.exists else None

def set_user_data(user_id, data):
    user_ref = db.collection("users").document(user_id)
    user_ref.set(data, merge=True)

def get_user_conversation(user_id):
    user_ref = db.collection("conversations").document(user_id)
    user_doc = user_ref.get()
    return user_doc.to_dict().get("messages", []) if user_doc.exists else []

def save_user_conversation(user_id, messages):
    user_ref = db.collection("conversations").document(user_id)
    user_ref.set({"messages": messages}, merge=True)

# ----------------------------------------- 
# 🔹 FAISS 檢索
# ----------------------------------------- 
def search_recipe(query, k=3):
    query_embedding = model.encode(query, convert_to_numpy=True).reshape(1, -1)
    distances, indices = index.search(query_embedding, k)
    return df.iloc[indices[0]]

# ----------------------------------------- 
# 🔹 GPT 整合
# ----------------------------------------- 
def chat_with_model(user_id, user_input):
    user_data = get_user_data(user_id)
    preferences = user_data.get("preferences", None) if user_data else None

    if not preferences:
        return "Please enter your dietary preferences (e.g., vegetarian, no beef, low-carb)."

    best_recipes = search_recipe(user_input, k=3)
    formatted_recipes = "\n\n".join([
        f"**Title:** {row['title']}\n**Ingredients:** {row['ingredients']}\n**Instructions:** {row['directions']}"
        for _, row in best_recipes.iterrows()
    ])

    system_prompt = f"""
    You are a professional chef assistant. The user follows these dietary preferences: {preferences}.
    Here are recommended recipes based on their preferences:
    {formatted_recipes}
    Provide a response considering these preferences strictly.
    """

    conversation = get_user_conversation(user_id)
    if not conversation:
        conversation.append({"role": "system", "content": system_prompt})
    conversation.append({"role": "user", "content": user_input})

    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation,
        max_tokens=200
    )

    reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": reply})

    if len(conversation) > 20:
        conversation = conversation[-20:]
    save_user_conversation(user_id, conversation)

    return reply
