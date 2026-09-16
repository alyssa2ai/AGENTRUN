# colab_server_e4.py
#
# EXPERIMENT E4 — V1 ADAPTER + FIXED PARSER
#
# This server loads the V1 LoRA adapter but uses the V2 two-pass parser.
# It isolates the parser effect from the data effect:
#   - Same model weights as V1 (35 trajectories, agentlab_qwen_lora_7b)
#   - Same parser as V2 (two-pass robust parsing)
#   - Same benchmark as V1/V2 (23 tasks, max_steps=3)
#
# Differences from colab_server.py (V1 server):
#   1. PARSER:           two-pass robust parser from colab_server_v2.py
#   2. OUTPUT ADAPTER:   /content/agentlab_qwen_lora_7b (V1 adapter)
#
# Differences from colab_server_v2.py (V2 server):
#   1. PARSER:           identical (both use two-pass)
#   2. OUTPUT ADAPTER:   /content/agentlab_qwen_lora_7b (V1, not V2)
#
# Upload the V1 adapter to /content/agentlab_qwen_lora_7b before running.
# This script does NOT touch the V2 adapter or training data.

# ===== CELL BREAK =====
!pip install -q transformers peft accelerate bitsandbytes fastapi uvicorn pyngrok nest_asyncio

# ===== CELL BREAK =====
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
ADAPTER_PATH = "/content/agentlab_qwen_lora_7b"   # V1 adapter — DO NOT CHANGE

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

print("Loading base model in 4-bit...")
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
)
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL, quantization_config=quant_config, device_map="auto"
)

print("Applying V1 LoRA adapter...")
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
model.eval()
print(f"E4 model ready. V1 adapter + V2 parser. Adapter: {ADAPTER_PATH}")

# ===== CELL BREAK =====
import re
import json
from fastapi import FastAPI, Request
import uvicorn
import nest_asyncio
from pyngrok import ngrok

app = FastAPI()

# ── V2 TWO-PASS PARSER (identical to colab_server_v2.py) ─────────────────────
# Strategy 1: standard properly-closed <tool_call>...</tool_call> blocks
TOOL_CALL_CLOSED = re.compile(
    r"<tool_call>\s*(\{.*?\})\s*</tool_call>",
    re.DOTALL
)

# Strategy 2: when the model emits malformed tags (missing closing tag),
# extract the first JSON object starting from the first <tool_call> tag.
TOOL_CALL_OPEN = re.compile(
    r"<tool_call>\s*(\{.*?\})",
    re.DOTALL
)


def parse_model_output(raw_text: str) -> dict:
    """Robust two-pass parser for Qwen tool-call output.

    Pass 1 (strict): matches properly closed <tool_call>...</tool_call> blocks.
    Pass 2 (fallback): if pass 1 finds nothing, finds the first JSON object
    starting at the first <tool_call> opening tag.

    Returns {"tool_calls": [...], "text": None} if any tool call found,
    otherwise {"tool_calls": [], "text": raw_text} for a final answer.
    """
    # Pass 1: standard closed blocks
    matches = TOOL_CALL_CLOSED.findall(raw_text)
    if matches:
        tool_calls = []
        for m in matches:
            try:
                parsed = json.loads(m)
                name = parsed.get("name")
                if name:
                    tool_calls.append({"name": name, "arguments": parsed.get("arguments", {})})
            except json.JSONDecodeError:
                continue
        if tool_calls:
            return {"tool_calls": tool_calls, "text": None}

    # Pass 2: malformed / unclosed first tag — extract first JSON from first <tool_call> tag
    first_open = TOOL_CALL_OPEN.search(raw_text)
    if first_open:
        json_str = first_open.group(1)
        try:
            parsed = json.loads(json_str)
            name = parsed.get("name")
            if name:
                return {
                    "tool_calls": [{"name": name, "arguments": parsed.get("arguments", {})}],
                    "text": None,
                }
        except json.JSONDecodeError:
            pass

    return {"tool_calls": [], "text": raw_text.strip()}


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    tools = body.get("tools", [])

    prompt = tokenizer.apply_chat_template(
        messages, tools=tools if tools else None,
        add_generation_prompt=True, tokenize=False,
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = output_ids[0][inputs["input_ids"].shape[1]:]
    raw_text = tokenizer.decode(generated, skip_special_tokens=True)

    # Diagnostic logging
    print()
    print("=" * 60)
    print("[RAW MODEL OUTPUT]")
    print(raw_text[:1000])
    print("=" * 60)
    print("[PARSER RESULT]", parse_model_output(raw_text))
    print()

    return parse_model_output(raw_text)


@app.get("/health")
async def health():
    return {"status": "ok", "adapter": ADAPTER_PATH, "parser": "v2_two_pass"}


# ===== CELL BREAK =====
# Run this LAST. Get your ngrok authtoken at https://dashboard.ngrok.com/get-started/your-authtoken
# Paste it below.

NGROK_AUTH_TOKEN = "PASTE_YOUR_NGROK_TOKEN_HERE"
ngrok.set_auth_token(NGROK_AUTH_TOKEN)

nest_asyncio.apply()
public_url = ngrok.connect(8000)
print(f"\n{'=' * 60}")
print(f"E4 SERVER URL — paste this into the E4 evaluator: {public_url}")
print(f"Adapter loaded: {ADAPTER_PATH} (V1 weights)")
print(f"Parser: V2 two-pass robust parser")
print(f"{'=' * 60}\n")

uvicorn.run(app, host="0.0.0.0", port=8000)
