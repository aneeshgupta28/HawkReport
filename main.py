import os
import smtplib
import tweepy
import numpy as np
import json
from flask import Flask, request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.cloud import firestore
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from utils import prompts, news, structure
from langchain_google_genai import ChatGoogleGenerativeAI
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
print("Loading AI Models...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Setup Clients
db = firestore.Client()


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5)
llm_relevance = llm.with_structured_output(structure.RelevancyList)
llm_update = llm.with_structured_output(structure.isUpdate)
relevant_prompt = prompts.relevant_prompt
post_prompt = prompts.post_prompt
update_prompt = prompts.update_prompt


client = tweepy.Client(
    consumer_key=os.environ["X_CONSUMER_KEY"],
    consumer_secret=os.environ["X_CONSUMER_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)

def check_if_update_via_llm(old_content, new_content):
    """
    Uses LLM to decide if the new content is a significant update 
    or just a rephrase of the old content.
    """
    
    try:
        response = llm_update.chat.completions.create(
            model="gpt-3.5-turbo", # Use a cheap model for this check
            messages=[{"role": "user", "content": update_prompt.format(
                old_content=old_content,
                new_content=new_content)}],
            max_tokens=10
        )
        answer = response.choices[0].message.content.strip().upper()
        return answer == "UPDATE"
    except Exception as e:
        print(f"LLM Check Failed: {e}")
        return False # Fail safe: Assume duplicate to avoid spam

def process_news_item(news_url, tweet_content):
    """
    Decides whether to Save (and email) or Skip the news item.
    """
    
    # --- STEP 1: Vector Search (The "Broad Net") ---
    # Get last 50 posts to check against
    docs = db.collection('posts')\
             .order_by('created_at', direction=firestore.Query.DESCENDING)\
             .limit(50)\
             .stream()
    
    stored_embeddings = []
    stored_docs = []
    
    for doc in docs:
        data = doc.to_dict()
        if 'embedding' in data:
            stored_embeddings.append(data['embedding'])
            stored_docs.append(data) # Keep text for LLM check
            
    # If DB is empty, just save it
    if not stored_embeddings:
        return save_to_db(news_url, tweet_content)

    # Encode new content
    new_embedding = embedding_model.encode([tweet_content])[0]

    # Calculate similarity
    scores = cosine_similarity([new_embedding], stored_embeddings)[0]
    
    # Find the single most similar old post
    max_score_index = np.argmax(scores)
    max_score = scores[max_score_index]
    most_similar_post = stored_docs[max_score_index]

    print(f"Similarity Score: {max_score} vs '{most_similar_post['tweet_content'][:30]}...'")

    # --- DECISION LOGIC ---
    
    # Case A: Totally new topic (Low similarity)
    if max_score < 0.75:
        print("New Topic detected.")
        return save_to_db(news_url, tweet_content, new_embedding.tolist())

    # Case B: Very similar (Potential Duplicate OR Update)
    # We define a "Zone of Ambiguity" between 0.75 and 0.98
    # If it's > 0.98, it's almost certainly a pure copy-paste, so ignore it.
    elif 0.75 <= max_score < 0.98:
        print("High similarity detected. Asking LLM if this is an update...")
        
        is_update = check_if_update_via_llm(
            most_similar_post['tweet_content'], 
            tweet_content
        )
        
        if is_update:
            print("LLM says: It's an UPDATE! Saving...")
            return save_to_db(news_url, tweet_content, new_embedding.tolist())
        else:
            print("LLM says: It's a DUPLICATE. Skipping.")
            return None

    # Case C: Exact Match (> 0.98)
    else:
        print("Exact duplicate detected. Skipping.")
        return None

def save_to_db(news_url, tweet_content, embedding_list):
    """Helper to write to Firestore"""
    doc_ref = db.collection('posts').document(news_url.replace("/", "_"))
    doc_ref.set({
        "news_url": news_url,
        "tweet_content": tweet_content,
        "embedding": embedding_list,
        "status": "pending",
        "created_at": firestore.SERVER_TIMESTAMP
    })
    return doc_ref.id

def send_email(doc_id, content):
    """Sends an email with an APPROVE link."""
    sender_email = os.environ["GMAIL_USER"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    receiver_email = os.environ["MY_EMAIL"]

    if os.environ.get("TEST_MODE") == "True":
        print("\n" + "="*30)
        print(f"🧪 TEST MODE: Email would be sent to {receiver_email}")
        print(f"🔗 APPROVAL LINK: http://localhost:8080/approve?id={doc_id}")
        print("="*30 + "\n")
        return
    
    # The Cloud Run URL will be available after deployment
    base_url = os.environ["SERVICE_URL"] 
    approve_link = f"{base_url}/approve?id={doc_id}"

    msg = MIMEMultipart()
    msg['Subject'] = "📢 Approve New X Post"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    html = f"""
    <h3>New News Summary Generated</h3>
    <p>{content}</p>
    <br>
    <a href="{approve_link}" 
       style="padding: 10px 20px; background-color: #1DA1F2; color: white; text-decoration: none; border-radius: 5px;">
       ✅ CLICK TO POST ON X
    </a>
    """
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

@app.route('/approve')
def approve():
    """Logic that runs when you click the email link."""
    doc_id = request.args.get('id')
    if not doc_id:
        return "Missing ID", 400

    doc_ref = db.collection('posts').document(doc_id)
    doc = doc_ref.get()

    if not doc.exists:
        return "Post not found", 404
    
    data = doc.to_dict()
    if data['status'] == 'posted':
        return "Already posted!", 200
    
    try:
        if os.environ.get("TEST_MODE") == "True":
            print(f"🧪 TEST MODE: Tweet would be posted: {data['tweet_content']}")
            # Still update DB to test that logic
            doc_ref.update({"status": "posted"}) 
            return "<h1>Test Success! Tweet 'simulated' and DB updated.</h1>"
            
        client.create_tweet(text=data['tweet_content'])
        doc_ref.update({"status": "posted"})
        return "<h1>Success! Post is live on X.</h1>"
    except Exception as e:
        return f"Error: {e}", 500
    # Post to X
    try:
        client.create_tweet(text=data['tweet_content'])
        doc_ref.update({"status": "posted"})
        return "<h1>Success! Post is live on X.</h1>"
    except Exception as e:
        return f"Error posting to X: {e}", 500

@app.route('/run-bot', methods=['POST'])
def run_bot():
    """Route triggered by Cloud Scheduler to run the scraping logic."""
    
    # INSERT YOUR SCRAPING & LLM LOGIC HERE
    # For example:
    # news_list = scrape_news() 
    # for news in news_list:
    #     summary = generate_llm_summary(news['text'])
    #     doc_id = save_to_db(news['url'], summary)
    #     if doc_id:
    #         send_email(doc_id, summary)
    
    return "Bot run initiated", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))