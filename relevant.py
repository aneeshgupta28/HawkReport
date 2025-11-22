from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from datetime import datetime
from utils.news import fetch_rss
from utils import prompts, structure
load_dotenv()



current_time = datetime.now().isoformat()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5)

llm_structured = llm.with_structured_output(structure.RelevancyList)

prompt = prompts.relevant_prompt

print(prompt)

