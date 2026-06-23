import gradio as gr
from generate import model, respond

supported_models = model()

custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Inter', sans-serif !important;
    box-sizing: border-box;
}

/* ── Full-page dark background ── */
html, body {
    background: #0d0d0f !important;
    margin: 0;
    padding: 0;
}

.gradio-container {
    background: #0d0d0f !important;
    width: 100% !important;
    max-width: 860px !important;
    margin: 0 auto !important;
    padding: 0 16px !important;
}

/* ── Responsive container ── */
@media (max-width: 600px) {
    .gradio-container {
        padding: 0 8px !important;
    }

    .header-title {
        font-size: 1.5rem !important;
    }

    .header-sub {
        font-size: 0.78rem !important;
    }
}

/* ── Model dropdown ── */
label span {
    color: #8080a8 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}

select, .wrap-inner {
    background: #1a1a2e !important;
    border: 1px solid #2e2e50 !important;
    border-radius: 10px !important;
    color: #c8c8e8 !important;
}

/* ── Input textbox ── */
textarea {
    background: #1a1a2e !important;
    border: 1px solid #2e2e50 !important;
    border-radius: 12px !important;
    color: #e0e0f8 !important;
    font-size: 0.95rem !important;
    width: 100% !important;
}

textarea:focus {
    border-color: #6c63ff !important;
    box-shadow: 0 0 0 3px rgba(108, 99, 255, 0.18) !important;
    outline: none !important;
}

/* ── Send button ── */
button.primary {
    background: linear-gradient(135deg, #6c63ff 0%, #a855f7 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    color: #fff !important;
    transition: opacity 0.2s ease !important;
    white-space: nowrap !important;
}

/* ── Chatbot container (div only, not inner spans) ── */
div.chatbot {
    background: #0b0b14 !important;
    border: 1px solid #1a1a30 !important;
    border-radius: 24px !important;
    width: 100% !important;
    padding: 12px 8px !important;
}

/* ── Message animation ── */
.message {
    animation: fadeUp 0.22s ease-out !important;
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── User bubble ── */
.message-row:has(div[data-testid="user"]) {
    max-width: 78% !important;
    align-self: flex-end !important;
    margin-left: auto !important;
}

div[data-testid="user"] {
    background: linear-gradient(145deg, #5e54ed, #7c3aed) !important;
    box-shadow: 0 4px 20px rgba(94, 84, 237, 0.4), inset 0 1px 0 rgba(255,255,255,0.12) !important;
    color: #f5f4ff !important;
    border-radius: 22px 22px 5px 22px !important;
    padding: 13px 20px !important;
    font-size: 0.94rem !important;
    line-height: 1.6 !important;
    overflow-wrap: break-word !important;
    word-break: normal !important;
    letter-spacing: 0.01em !important;
}

/* ── Bot bubble ── */
.message-row:has(div[data-testid="bot"]) {
    max-width: 78% !important;
    align-self: flex-start !important;
    margin-right: auto !important;
}

div[data-testid="bot"] {
    background: #111120 !important;
    border: 1px solid #1f1f3d !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04) !important;
    color: #d0d0ee !important;
    border-radius: 22px 22px 22px 5px !important;
    padding: 14px 20px !important;
    font-size: 0.94rem !important;
    line-height: 1.72 !important;
    overflow-wrap: break-word !important;
    word-break: normal !important;
}

/* ── Code inside bot responses ── */
div[data-testid="bot"] pre {
    background: #080812 !important;
    border: 1px solid #22224a !important;
    border-left: 1px solid #22224a !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    overflow-x: auto !important;
    font-size: 0.83rem !important;
    margin: 10px 0 !important;
}

div[data-testid="bot"] code {
    background: rgba(124, 58, 237, 0.15) !important;
    border: 1px solid rgba(124, 58, 237, 0.25) !important;
    border-radius: 5px !important;
    padding: 2px 7px !important;
    font-size: 0.87em !important;
    color: #b89dff !important;
}

/* ── Textbox (the pill input) ── */
textarea {
    background: #111120 !important;
    border: 1.5px solid #22223a !important;
    border-radius: 16px !important;
    color: #e8e8ff !important;
    font-size: 0.96rem !important;
    line-height: 1.5 !important;
    padding: 14px 18px !important;
    width: 100% !important;
    resize: none !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

textarea::placeholder {
    color: #3a3a60 !important;
}

textarea:focus {
    border-color: #6c63ff !important;
    box-shadow:
        0 0 0 3px rgba(108, 99, 255, 0.15),
        0 8px 30px rgba(108, 99, 255, 0.1) !important;
    outline: none !important;
}

/* ── Send button ── */
button.primary {
    background: linear-gradient(135deg, #6c63ff 0%, #7c3aed 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: #fff !important;
    padding: 10px 20px !important;
    box-shadow: 0 4px 15px rgba(108, 99, 255, 0.4) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease !important;
    white-space: nowrap !important;
}

button.primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(108, 99, 255, 0.55) !important;
}

button.primary:active {
    transform: translateY(0px) !important;
    opacity: 0.9 !important;
}

/* ── Secondary buttons ── */
button.secondary {
    background: #111120 !important;
    border: 1px solid #22223a !important;
    border-radius: 8px !important;
    color: #6060a0 !important;
    transition: border-color 0.15s, color 0.15s !important;
}

button.secondary:hover {
    border-color: #6c63ff !important;
    color: #a0a0e0 !important;
}

/* ── Mobile ── */
@media (max-width: 480px) {
    div[data-testid="user-message"],
    div[data-testid="bot-message"] {
        max-width: 92% !important;
        font-size: 0.88rem !important;
        padding: 11px 15px !important;
    }
    textarea { font-size: 0.9rem !important; padding: 12px 14px !important; }
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2a50; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #4a4a80; }

/* ── Remove vertical line inside messages ── */
div[data-testid="user"] *,
div[data-testid="bot"] * {
    border-left: none !important;
}

div[data-testid="user"] p,
div[data-testid="bot"] p {
    margin: 0 0 0.4em 0 !important;
}

div[data-testid="user"] p:last-child,
div[data-testid="bot"] p:last-child {
    margin-bottom: 0 !important;
}

/* ── Hide Gradio footer ── */
footer { display: none !important; }
"""

with gr.Blocks(title="Chat") as demo:

    gr.HTML("""
        <div style="
            text-align: center;
            padding: clamp(1rem, 4vw, 1.8rem) 1rem 0.8rem;
        ">
            <h1 class="header-title" style="
                font-size: clamp(1.4rem, 5vw, 2.1rem);
                font-weight: 700;
                background: linear-gradient(135deg, #6c63ff, #a855f7, #ec4899);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 0 0 0.3rem 0;
                font-family: 'Inter', sans-serif;
            ">SmartCV Assessor</h1>
            <p class="header-sub" style="
                color: #4a4a70;
                font-size: clamp(0.75rem, 2.5vw, 0.85rem);
                margin: 0;
                font-family: 'Inter', sans-serif;
            ">Powered by Ollama</p>
        </div>
    """)

    with gr.Row():
        model_selector = gr.Dropdown(
            choices=supported_models,
            value=supported_models[0],
            label="Model",
            interactive=True,
            scale=1,
        )

    gr.ChatInterface(
        fn=respond,
        additional_inputs=[model_selector],
        chatbot=gr.Chatbot(
            height=460,
            placeholder=(
                "<div style='color:#2e2e50; text-align:center; padding:3rem;"
                " font-family:Inter,sans-serif;'>Send a message to start chatting ✦</div>"
            ),
            show_label=False,
            avatar_images=(
                None,
                "https://api.dicebear.com/7.x/bottts-neutral/svg?seed=groq&backgroundColor=6c63ff",
            ),
        ),
        textbox=gr.Textbox(
            placeholder="Message Ollama...",
            show_label=False,
            lines=1,
            submit_btn="Send ↑",
        ),
        fill_width=True,
    )

if __name__ == "__main__":
    demo.launch(css=custom_css)
