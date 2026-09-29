import os
import socket
import sys
import tempfile

import gradio as gr

from agent import run_agent
from branding import avatar_path, favicon_path, logo_data_uri
from config import (
    BASE_DIR,
    EVIDENCE_DIR,
    GUI_CONCURRENCY_LIMIT,
    GUI_HOST,
    GUI_PORT,
    MAX_PROMPT_CHARS,
    OLLAMA_MODEL,
)

FONT_LINKS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
"""

LOGO_LEGS_SVG = """
<svg class="gc-logo-legs" viewBox="-25 -25 310 310">
    <path d="M 150.2 79.9 Q 176.1 63.2 189.1 35.3 Q 164.4 12.8 153.0 -18.7"/>
    <path d="M 177.7 104.6 Q 212.9 102.4 244.9 87.6 Q 235.3 50.6 244.6 13.5"/>
    <path d="M 181.4 146.7 Q 213.6 162.8 249.2 157.3 Q 260.8 192.1 260.2 228.7"/>
    <path d="M 158.6 175.8 Q 174.8 202.4 202.8 216.4 Q 192.5 250.7 164.6 273.1"/>
    <path d="M 109.8 79.9 Q 83.3 62.2 69.1 33.7 Q 93.5 11.5 106.8 -18.7"/>
    <path d="M 82.3 104.6 Q 46.0 104.5 13.6 88.3 Q 24.4 50.9 16.1 12.8"/>
    <path d="M 78.6 146.7 Q 46.2 159.9 11.2 158.3 Q -3.0 194.0 2.5 232.0"/>
    <path d="M 101.4 175.8 Q 85.8 202.5 57.0 213.6 Q 68.3 249.1 95.0 275.0"/>
</svg>
"""

CHAT_ICON_SVG = (
    '<svg class="gc-panel-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M4 5.5C4 4.67 4.67 4 5.5 4H18.5C19.33 4 20 4.67 20 5.5V14.5C20 15.33 19.33 16 18.5 16H9L5 19.5V16H5.5'
    'C4.67 16 4 15.33 4 14.5V5.5Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>'
)

THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.rose,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
).set(
    body_background_fill="#0a0e17",
    body_background_fill_dark="#0a0e17",
    background_fill_primary="#0a0e17",
    background_fill_primary_dark="#0a0e17",
    background_fill_secondary="#111827",
    background_fill_secondary_dark="#111827",
    border_color_primary="rgba(255,255,255,0.08)",
    border_color_primary_dark="rgba(255,255,255,0.08)",
    body_text_color="#e7ebf3",
    body_text_color_dark="#e7ebf3",
    body_text_color_subdued="#8b93a7",
    body_text_color_subdued_dark="#8b93a7",
    block_background_fill="#131b2c",
    block_background_fill_dark="#131b2c",
    block_border_color="rgba(255,255,255,0.09)",
    block_border_color_dark="rgba(255,255,255,0.09)",
    block_radius="16px",
    block_shadow="0 12px 32px rgba(4,6,14,0.55)",
    block_shadow_dark="0 12px 32px rgba(4,6,14,0.55)",
    block_label_background_fill="#1a2440",
    block_label_background_fill_dark="#1a2440",
    block_label_text_color="#c7cfe0",
    block_label_text_color_dark="#c7cfe0",
    block_title_text_color="#e7ebf3",
    block_title_text_color_dark="#e7ebf3",
    input_background_fill="#0d1320",
    input_background_fill_dark="#0d1320",
    input_border_color="rgba(255,255,255,0.14)",
    input_border_color_dark="rgba(255,255,255,0.14)",
    input_radius="12px",
    button_primary_background_fill="linear-gradient(135deg, #b3283d, #7f1d2d)",
    button_primary_background_fill_dark="linear-gradient(135deg, #b3283d, #7f1d2d)",
    button_primary_background_fill_hover="linear-gradient(135deg, #c73349, #8f2334)",
    button_primary_background_fill_hover_dark="linear-gradient(135deg, #c73349, #8f2334)",
    button_primary_text_color="#ffffff",
    button_primary_text_color_dark="#ffffff",
    button_primary_border_color="#b3283d",
    button_primary_border_color_dark="#b3283d",
    button_primary_shadow="0 4px 14px rgba(179,40,61,0.45)",
    color_accent="#b3283d",
    color_accent_soft="rgba(179,40,61,0.15)",
    color_accent_soft_dark="rgba(179,40,61,0.15)",
)

CUSTOM_CSS = """
.gc-header {
    display: flex; align-items: center; gap: 18px;
    padding: 22px 28px; margin: -1px -1px 22px -1px;
    background: radial-gradient(circle at 15% 20%, rgba(179,40,61,0.22), transparent 55%), #0d1320;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 18px;
}
.gc-logo-wrap {
    position: relative; width: 170px; height: 170px; flex-shrink: 0;
}
.gc-logo-wrap::before {
    content: ""; position: absolute; inset: 8px; border-radius: 50%;
    background: conic-gradient(from 0deg, transparent 0%, rgba(201,162,75,0.55) 12%, transparent 24%);
    -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 3px), #000 calc(100% - 2px));
    mask: radial-gradient(farthest-side, transparent calc(100% - 3px), #000 calc(100% - 2px));
    opacity: 0.85;
}
.gc-logo-legs {
    position: absolute; inset: 0; width: 100%; height: 100%;
    overflow: visible;
}
.gc-logo-legs path {
    fill: none; stroke: #f6cb2f; stroke-width: 9;
    stroke-linecap: round; stroke-linejoin: round;
    filter: drop-shadow(0 2px 3px rgba(4,6,14,0.55));
}
.gc-logo {
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
    width: 64px; height: 64px; border-radius: 50%;
    border: 2px solid #c9a24b;
    box-shadow: 0 0 0 4px rgba(201,162,75,0.12), 0 8px 20px rgba(4,6,14,0.6);
    z-index: 1;
}
@media (prefers-reduced-motion: no-preference) {
    .gc-logo-wrap::before { animation: gc-scan 9s linear infinite; }
    .gc-logo-legs { animation: gc-breathe 4.5s ease-in-out infinite; }
    .gc-fade-in { animation: gc-rise 0.6s cubic-bezier(0.16, 1, 0.3, 1) both; }
    .gc-fade-in.gc-fade-in-delay { animation-delay: 0.08s; }
    .gc-logo:hover { animation: gc-logo-spin 0.9s linear infinite; }
}
@keyframes gc-scan { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes gc-breathe { 0%, 100% { opacity: 1; } 50% { opacity: 0.82; } }
@keyframes gc-rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes gc-logo-spin {
    from { transform: translate(-50%, -50%) rotate(0deg); }
    to { transform: translate(-50%, -50%) rotate(360deg); }
}
.gc-title-block { display: flex; flex-direction: column; gap: 2px; }
.gc-wordmark {
    font-family: 'Caveat', cursive; font-weight: 700;
    font-size: 2.6rem; line-height: 1;
    background: linear-gradient(90deg, #e7ebf3, #c9a24b 60%, #b3283d);
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.gc-tagline {
    font-family: 'Inter', sans-serif; font-size: 0.92rem;
    color: #8b93a7; letter-spacing: 0.01em;
}
.gc-meta {
    font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
    color: #6c7591; margin-top: 6px;
}
.gc-meta code { color: #d7a6ad; background: rgba(179,40,61,0.12); padding: 1px 6px; border-radius: 5px; }

.gc-panel-heading {
    font-family: 'Caveat', cursive; font-weight: 700; font-size: 1.4rem;
    color: #c9a24b; margin: 0 0 8px 4px; display: flex; align-items: center; gap: 8px;
}
.gc-panel-icon {
    width: 18px; height: 18px; flex-shrink: 0; color: #c9a24b; opacity: 0.9;
}

#gc-panel-toolbar {
    align-items: center; justify-content: space-between; gap: 8px;
    margin-bottom: 8px;
}
#gc-panel-toolbar .gc-panel-heading { margin: 0; }

#gc-download-btn {
    width: 116px !important; flex-basis: 116px !important; flex-grow: 0 !important; flex-shrink: 0 !important;
    flex-wrap: nowrap !important; white-space: nowrap !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    color: #8b93a7 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important; font-weight: 400 !important;
    letter-spacing: 0.03em; text-transform: none !important;
    padding: 4px 10px !important; min-height: 0 !important; height: auto !important;
    border-radius: 8px !important; box-shadow: none !important;
    transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}
#gc-download-btn img { width: 13px !important; height: 13px !important; opacity: 0.85; }
#gc-download-btn:hover {
    color: #c9a24b !important;
    background: rgba(201,162,75,0.1) !important;
    border-color: rgba(201,162,75,0.3) !important;
}
#gc-download-btn:active { transform: translateY(1px); }
#gc-download-btn:focus-visible { outline: 2px solid rgba(201,162,75,0.65); outline-offset: 2px; }

#gc-msg-input textarea,
#gc-msg-input input {
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
#gc-msg-input textarea:focus,
#gc-msg-input input:focus {
    border-color: rgba(201,162,75,0.55) !important;
    box-shadow: 0 0 0 3px rgba(201,162,75,0.16) !important;
}

#gc-send-btn {
    min-width: 110px; border-radius: 12px !important;
    transition: transform 0.15s ease, box-shadow 0.2s ease, filter 0.2s ease;
}
#gc-send-btn:hover:not(:disabled) { filter: brightness(1.06); }
#gc-send-btn:active:not(:disabled) { transform: translateY(1px) scale(0.98); }
#gc-send-btn:disabled { opacity: 0.55; cursor: not-allowed; }
#gc-send-btn:focus-visible,
#gc-msg-input textarea:focus-visible,
#gc-msg-input input:focus-visible {
    outline: 2px solid rgba(201,162,75,0.65); outline-offset: 2px;
}

#gc-tool-log { margin-top: 18px; }
#gc-tool-log > .label-wrap {
    font-family: 'Caveat', cursive; font-weight: 700; font-size: 1.3rem;
    color: #c9a24b; transition: color 0.15s ease;
}
#gc-tool-log > .label-wrap span { text-transform: none; }
#gc-tool-log > .label-wrap svg { color: #c9a24b; }
#gc-tool-log > .label-wrap:hover { color: #dcb662; }

#gc-chatbot code,
#gc-tool-log code {
    color: #f6d365 !important;
    background: #242c3e !important;
    border: 1px solid rgba(246, 211, 101, 0.22);
    border-radius: 5px;
    padding: 1px 5px;
}

#gc-chatbot pre,
#gc-tool-log pre {
    color: #dce5f4 !important;
    background: #080d17 !important;
    border: 1px solid rgba(255,255,255,0.12);
}

#gc-chatbot pre code,
#gc-tool-log pre code {
    color: #dce5f4 !important;
    background: transparent !important;
    border: 0;
    padding: 0;
}

.gc-footer {
    text-align: center; font-family: 'Caveat', cursive; font-size: 1.05rem;
    color: #5c6584; margin-top: 18px; padding-bottom: 4px;
}

#gc-chatbot ::-webkit-scrollbar,
#gc-tool-log ::-webkit-scrollbar {
    width: 10px; height: 10px;
}
#gc-chatbot ::-webkit-scrollbar-track,
#gc-tool-log ::-webkit-scrollbar-track { background: #0d1320; }
#gc-chatbot ::-webkit-scrollbar-thumb,
#gc-tool-log ::-webkit-scrollbar-thumb {
    background: rgba(201,162,75,0.35); border-radius: 8px; border: 2px solid #0d1320;
}
#gc-chatbot ::-webkit-scrollbar-thumb:hover,
#gc-tool-log ::-webkit-scrollbar-thumb:hover { background: rgba(201,162,75,0.55); }
#gc-chatbot, #gc-tool-log { scrollbar-color: rgba(201,162,75,0.35) #0d1320; scrollbar-width: thin; }

footer { display: none !important; }
"""


def _local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _format_tool_event(kind: str, payload: dict) -> str:
    if kind == "tool_call":
        return f"**&rarr; `{payload['name']}`**\n```json\n{payload['arguments']}\n```"
    return f"**&larr; result**\n```json\n{payload['result']}\n```"


def _content_to_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
        return "\n".join(p for p in parts if p)
    return "" if content is None else str(content)


TRANSCRIPT_DIR = os.path.join(tempfile.gettempdir(), "glisson-transcripts")


def _transcript_path(session_hash: str | None) -> str:
    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    safe_id = session_hash or "session"
    return os.path.join(TRANSCRIPT_DIR, f"glisson-transcript-{safe_id}.txt")


def _update_transcript(chat_history, request: gr.Request):
    lines = []
    for message in chat_history or []:
        speaker = "You" if message.get("role") == "user" else "Glisson Crawler"
        lines.append(f"{speaker}:\n{_content_to_text(message.get('content'))}\n")
    path = _transcript_path(request.session_hash)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def _lock_inputs():
    return gr.update(interactive=False), gr.update(interactive=False)


def _unlock_inputs():
    return gr.update(value="", interactive=True), gr.update(interactive=True)


def respond(user_message, chat_history, request: gr.Request):
    if not user_message.strip():
        yield chat_history or [], "_(tool calls will appear here)_"
        return

    if len(user_message) > MAX_PROMPT_CHARS:
        yield (
            chat_history or [],
            f"Prompt is too long: {len(user_message):,} characters. "
            f"Maximum is {MAX_PROMPT_CHARS:,}.",
        )
        return

    chat_history = chat_history or []
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": ""})

    log_lines = []
    prior_turns = [
        {"role": m["role"], "content": _content_to_text(m["content"])}
        for m in chat_history[:-2]
        if m["role"] in ("user", "assistant")
    ]

    try:
        for kind, payload in run_agent(user_message, prior_turns, session_id=request.session_hash):
            if kind == "final":
                chat_history[-1]["content"] = payload
            else:
                log_lines.append(_format_tool_event(kind, payload))
            yield chat_history, "\n\n---\n\n".join(log_lines) or "_(tool calls will appear here)_"
    except Exception as e:
        chat_history[-1]["content"] = f"Something went wrong on this request ({type(e).__name__}: {e}). Try again."
        yield chat_history, "\n\n---\n\n".join(log_lines) or "_(tool calls will appear here)_"


def build_app() -> gr.Blocks:
    logo_uri = logo_data_uri()

    with gr.Blocks(title="Glisson Crawler") as demo:
        gr.HTML(f"""
        <div class="gc-header gc-fade-in">
            <div class="gc-logo-wrap">
                {LOGO_LEGS_SVG}
                <img class="gc-logo" src="{logo_uri}" alt="Glisson Crawler">
            </div>
            <div class="gc-title-block">
                <span class="gc-wordmark">Glisson Crawler</span>
                <span class="gc-tagline">an agentic forensics assistant, built for the classroom</span>
                <span class="gc-meta">model <code>{OLLAMA_MODEL}</code> &middot; evidence <code>{EVIDENCE_DIR}</code></span>
            </div>
        </div>
        """)

        with gr.Row(elem_id="gc-panel-toolbar"):
            gr.HTML(
                f'<div class="gc-panel-heading gc-fade-in gc-fade-in-delay">{CHAT_ICON_SVG} the conversation</div>',
            )
            download_btn = gr.DownloadButton(
                "transcript",
                icon=os.path.join(BASE_DIR, "assets", "download.svg"),
                size="sm",
                variant="secondary",
                scale=0,
                min_width=0,
                elem_id="gc-download-btn",
            )
        chatbot = gr.Chatbot(
            height=480,
            show_label=False,
            avatar_images=(None, avatar_path()),
            buttons=["copy", "copy_all"],
            elem_id="gc-chatbot",
        )
        with gr.Row():
            msg = gr.Textbox(
                show_label=False,
                placeholder="e.g. Calculate the SHA512 hash of File_5",
                scale=5,
                elem_id="gc-msg-input",
            )
            send_btn = gr.Button("Send", variant="primary", scale=1, elem_id="gc-send-btn")

        with gr.Accordion("tool activity log", open=False, elem_id="gc-tool-log"):
            tool_log = gr.Markdown(value="_(tool calls will appear here)_")

        gr.HTML('<div class="gc-footer">silence is happiness</div>')

        msg.submit(_lock_inputs, None, [msg, send_btn]).then(
            respond, [msg, chatbot], [chatbot, tool_log]
        ).then(_update_transcript, chatbot, download_btn).then(_unlock_inputs, None, [msg, send_btn])

        send_btn.click(_lock_inputs, None, [msg, send_btn]).then(
            respond, [msg, chatbot], [chatbot, tool_log]
        ).then(_update_transcript, chatbot, download_btn).then(_unlock_inputs, None, [msg, send_btn])

    return demo


if __name__ == "__main__":
    try:
        print(f"Starting on http://{_local_ip()}:{GUI_PORT}  (also http://localhost:{GUI_PORT} on this machine)")
        build_app().queue(default_concurrency_limit=GUI_CONCURRENCY_LIMIT).launch(
            server_name=GUI_HOST,
            server_port=GUI_PORT,
            favicon_path=favicon_path(),
            theme=THEME,
            css=CUSTOM_CSS,
            head=FONT_LINKS,
            allowed_paths=[TRANSCRIPT_DIR],
        )
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\nGlisson Crawler failed to start: {type(e).__name__}: {e}\n")
        input("Press Enter to close this window...")
        sys.exit(1)
