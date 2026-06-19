import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODELS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]


def model():
    """Initialize the Groq client and return it with the default model."""
    gpt = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return gpt, MODELS[0]


def chat(gpt, default_model):
    """Return a respond function compatible with gr.ChatInterface."""
    chat_log = []

    def respond(message, history, selected_model):
        """Called by Gradio on every user message."""
        log = []
        for entry in history:
            # Gradio 6 passes history as dicts: {"role": ..., "content": ...}
            if isinstance(entry, dict):
                log.append({"role": entry["role"], "content": entry["content"]})
            else:
                # fallback: tuple format (user_msg, assistant_msg)
                user_msg, assistant_msg = entry
                log.append({"role": "user", "content": user_msg})
                if assistant_msg:
                    log.append({"role": "assistant", "content": assistant_msg})
        log.append({"role": "user", "content": message})

        response = gpt.chat.completions.create(model=selected_model, messages=log)
        reply = response.choices[0].message.content
        chat_log.append({"role": "user", "content": message})
        chat_log.append({"role": "assistant", "content": reply})
        return reply

    return chat_log, None, respond
