import ollama

MODELS = ["llama3.1", "llama3.2"]

# run `ollama serve` in a terminal

def model():
    # check which models are actually available locally
    available = [m.model for m in ollama.list().models]
    supported = [m for m in MODELS if any(m in a for a in available)]
    if not supported:
        print("No supported models found. Make sure Ollama is running and pull a model:")
        print("  ollama pull llama3.1")
        exit(1)

    print("The available models are:")
    for i, name in enumerate(supported, start=1):
        print(f"\t{i}. {name}")

    choice = int(input(f"Choose your model [1-{len(supported)}]: "))
    if choice not in range(1, len(supported) + 1):
        print("Invalid model number.")
        exit(1)

    model = supported[choice - 1]
    print("Your chosen model is:", model)

    return model

def chat(model_name: str):

    chat_log = []
    assistant_response = ""

    while True:
        prompt = input("Ask something: ")
        if prompt.lower() in ["exit", "bye", "goodbye", "quit"]:
            break

        chat_log.append({"role": "user", "content": prompt})
        response = ollama.chat(model=model_name, messages=chat_log)
        assistant_response = response["message"]["content"]

        print(f"{model_name}: {assistant_response}")
        chat_log.append({"role": "assistant", "content": assistant_response})
        
    return chat_log, assistant_response

if __name__ == "__main__":
    model = model()
    chat_log, assistant_response = chat(model)