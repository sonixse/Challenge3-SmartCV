import ollama

MODELS = ["llama3", "llama3.1", "llama3.2"]

def model():
    available = [m.model for m in ollama.list().models]
    supported = [m for m in MODELS if any(m in a for a in available)]
    if not supported:
        print("No supported models found. Make sure Ollama is running and pull a model:")
        print("  ollama pull llama3.1")
        exit(1)

    return supported

def respond(message, history, selected_model):
    log = []
    for entry in history:
        if isinstance(entry, dict):
            role = entry["role"]
            content = entry["content"]

            if isinstance(content, list):
                content = " ".join(c.get("text", "") for c in content)
            log.append({"role": role, "content": content})
        else:
            user_msg, assistant_msg = entry
            log.append({"role": "user", "content": user_msg})
            if assistant_msg:
                log.append({"role": "assistant", "content": assistant_msg})

    if isinstance(message, list):
        message = " ".join(c.get("text", "") for c in message)

    log.append({"role": "user", "content": message})
    response = ollama.chat(model=selected_model, messages=log)
    return response["message"]["content"]