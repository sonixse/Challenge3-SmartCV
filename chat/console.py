import os
from groq import Groq
from dotenv import load_dotenv

MODELS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]

def model():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    gpt = Groq(api_key=api_key)

    print("The available models are:")
    for i, name in enumerate(MODELS, start=1):
        print(f"\t{i}. {name}")

    choice = int(input(f"Choose your model [1-{len(MODELS)}]: "))
    if choice not in range(1, len(MODELS) + 1):
        print("Invalid model number.")
        exit(1)

    model = MODELS[choice - 1]
    print("Your chosen model is:", model)

    return gpt, model

def chat(gpt,model):
    chat_log = []
    while True:
        prompt = input("Ask something: ")
        if prompt.lower() in ["exit", "bye", "goodbye", "quit"]:
            break

        chat_log.append({"role": "user", "content": prompt})
        response = gpt.chat.completions.create(model=model, messages=chat_log)
        assistant_response = response.choices[0].message.content
        print(f"{model}: {assistant_response}")
        chat_log.append({"role": "assistant", "content": assistant_response})
        
    return chat_log, response, assistant_response

if __name__ == "__main__":
    gpt, model = model()
    chat_log, response, assistant_response = chat(gpt, model)