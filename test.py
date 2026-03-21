from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv("key.env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

SYSTEM_PROMPT = """
Tu es Abdou, un assistant sympa et intelligent.
Tu réponds selon la lanngue utilisée.
Tu comprends tout, même les fautes d'orthographe.
Tu ne dis JAMAIS "je n'ai pas compris".
si tu ne comprends pas, tu demandes des précisions.
"""

history = []
print("🤖 Abdou est prêt ! (tape 'quit' pour arrêter)\n")

while True:
    user_input = input("Toi : ")
    
    if user_input.lower() == "quit":
        print("👋 Au revoir !")
        break

    history.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="openrouter/auto" ,  
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *history
        ]
    )

    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})
    print(f"🤖 Abdou : {reply}\n")