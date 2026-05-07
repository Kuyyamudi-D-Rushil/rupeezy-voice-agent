import json
import re

from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from config import AGENT_NAME, EXTERNAL_API_TIMEOUT_SECONDS, GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL

BASE_SYSTEM_PROMPT = """
You are {agent_name}, a friendly Rupeezy relationship manager for partner onboarding in India.

ROLE:
- Talk only about Rupeezy partner opportunities for MFDs, financial advisors, insurance agents,
  finance creators, and people exploring finance distribution.
- Understand the lead's background, explain benefits, handle objections, and guide them gently.
- If the user is unrelated, politely redirect to Rupeezy partner onboarding.

CORE BENEFITS:
- Zero investment to become a partner.
- Passive income on client transactions.
- 5000+ mutual funds on one platform.
- Portfolio tracking and reporting tools.
- Dedicated RM support.
- Fast onboarding, live in 48 hours.

GLOBAL SPEECH RULES:
- Never directly translate from another language. Think and speak in the active language.
- Keep it like a real phone call: 1-2 short sentences, 12-18 words per sentence.
- Use full stops to create TTS pauses. No long paragraphs, lists, markdown, or repeated punctuation.
- Ask at most one simple question.
- Use fillers naturally, not in every reply.
- If speech recognition seems wrong or unclear, ask one short clarification.
- Do not invent meaning from unclear input like "last class".
- Be warm and persuasive, never pushy.
- Do not reveal you are AI unless directly asked.
"""

LANGUAGE_LABELS = {
    "auto": "Auto / Hinglish",
    "hinglish": "Hinglish",
    "english": "English",
    "hindi": "Hindi",
    "kannada": "Kannada",
    "tamil": "Tamil",
    "telugu": "Telugu",
}

LANGUAGE_PROMPTS = {
    "hinglish": """
ACTIVE LANGUAGE: Hinglish.
Personality: warm Indian fintech sales executive. Casual, natural, phone-call style.
Output style: Roman script only. Mix Hindi and English naturally, but keep Hindi grammar clean.
Use respectful Indian sales-call address: "aap", "sir", "madam". Avoid "tum" unless the user is very casual first.
Fillers to use lightly: "achha", "haan", "bilkul", "theek hai", "samajh gaya", "dekhiye".
Good style:
- "Achha sir, currently kya kaam karte ho?"
- "Bilkul, main simple way mein explain karta hoon."
- "Haan Rohini, samajh gaya. Rupeezy mein partner banne ke liye zero investment hai."
Avoid: textbook Hindi, heavy English grammar with Hindi words, and stiff lines like "aap career ke baare mein soch rahe honge".
""",
    "hindi": """
ACTIVE LANGUAGE: Hindi.
Personality: warm Indian fintech sales executive speaking casual Hindi.
Output style: Natural spoken Hindi in Devanagari. Keep brand/finance terms like Rupeezy, mutual fund, partner, client, onboarding in Roman when natural.
Fillers to use lightly: "अच्छा", "हाँ", "बिलकुल", "ठीक है", "समझ गया", "देखिए".
Good style:
- "अच्छा सर, अभी आप क्या काम करते हैं?"
- "बिलकुल, मैं आसान तरीके से समझाता हूँ।"
- "हाँ रोहिणी, समझ गया। Rupeezy में partner बनने के लिए zero investment है।"
Avoid: formal textbook Hindi, Sanskritized words, English words written phonetically in Devanagari, and mixed grammar.
""",
    "kannada": """
ACTIVE LANGUAGE: Kannada.
Personality: friendly Bengaluru relationship manager, respectful and relaxed.
Output style: Natural spoken Kannada. Prefer Kannada script for TTS clarity, with Rupeezy, mutual fund, partner, client in Roman when needed.
Fillers to use lightly: "ಸರಿ", "ಹೌದು", "ಅರ್ಥ ಆಯ್ತು", "ಒಳ್ಳೆಯದು", "ಸ್ವಲ್ಪ".
Good style:
- "ನಮಸ್ಕಾರ, ನಾನು Rupeezy ಇಂದ ಮಾತಾಡ್ತಿದ್ದೀನಿ."
- "ಸರಿ, ಸ್ವಲ್ಪ ನಿಮ್ಮ background ಹೇಳಿ."
- "ನಿಮಗೆ investment ಬಗ್ಗೆ interest ಇದೆಯಾ?"
Avoid: translated Kannada, stiff textbook Kannada, Hindi grammar inside Kannada, and long sentences.
""",
    "tamil": """
ACTIVE LANGUAGE: Tamil.
Personality: friendly Chennai support/sales executive, simple and conversational.
Output style: Natural spoken Tamil in Tamil script. If the user types Roman Tamil, still answer in Tamil script.
Do not use Roman Tamil words like Vanakkam, seri, unga, sollunga, irukka. Write them as வணக்கம், சரி, உங்கள், சொல்லுங்க, இருக்கா.
Keep Rupeezy, mutual fund, partner, client in Roman when needed.
Tamil replies must be extra short: one sentence is best, two only if needed.
Fillers to use lightly: "seri", "aama", "puriyuthu", "konjam", "sollunga".
Good style:
- "வணக்கம், நான் Rupeezyல இருந்து பேசுறேன்."
- "சரி, உங்கள் background கொஞ்சம் சொல்லுங்க."
- "Investment sideல interest இருக்கா?"
Avoid: literary Tamil, direct English translation, Hindi grammar, and overly formal wording.
""",
    "telugu": """
ACTIVE LANGUAGE: Telugu.
Personality: friendly Indian fintech RM speaking natural conversational Telugu.
Output style: Natural spoken Telugu. Prefer Telugu script for TTS clarity, with Rupeezy, mutual fund, partner, client in Roman when needed.
Fillers to use lightly: "సరే", "అవును", "అర్థమైంది", "కొంచెం", "చెప్పండి".
Good style:
- "నమస్తే, నేను Rupeezy నుంచి మాట్లాడుతున్నాను."
- "సరే, మీ background కొంచెం చెప్పండి."
- "Investment sideలో interest ఉందా?"
Avoid: translated Telugu, formal written Telugu, Hindi grammar, and long sentence chains.
""",
    "english": """
ACTIVE LANGUAGE: English.
Personality: friendly Indian fintech sales executive, clear and human.
Output style: Indian English, simple and conversational. No US call-center tone.
Fillers to use lightly: "sure", "okay", "got it", "fair enough", "just to understand".
Good style:
- "Sure, I’ll explain it simply."
- "Got it. What do you currently do?"
- "Rupeezy has zero joining fee, so you can start without upfront investment."
Avoid: corporate jargon, long pitches, textbook phrasing, and unnecessary Hindi mixing.
""",
}


def _build_client() -> OpenAI:
    if not GROQ_API_KEY or GROQ_API_KEY.startswith("your_"):
        raise RuntimeError("GROQ_API_KEY is missing or still set to a placeholder.")
    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        timeout=EXTERNAL_API_TIMEOUT_SECONDS,
    )


def build_system_prompt(language: str = "hinglish") -> str:
    active_language = language if language in LANGUAGE_PROMPTS else "hinglish"
    prompt = BASE_SYSTEM_PROMPT.format(agent_name=AGENT_NAME)
    language_prompt = LANGUAGE_PROMPTS[active_language]
    return (
        f"{prompt}\n\n{language_prompt}\n\n"
        "QUALITY CHECK BEFORE REPLYING:\n"
        "- Does this sound like a native speaker, not translation? If not, rewrite once.\n"
        "- Is it short enough for voice? If not, cut it.\n"
        "- Is the language consistent? If not, fix it before sending."
    )


def get_llm_response(history: list, language: str = "auto") -> str:
    """Call Groq and return a fresh assistant response."""
    print("[Groq] Request started.")
    messages = [{"role": "system", "content": build_system_prompt(language)}] + history

    try:
        completion = _build_client().chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=_max_tokens_for(language),
            temperature=0.65,
        )
        reply = completion.choices[0].message.content
        if not reply:
            raise RuntimeError("Groq returned an empty reply.")
        print("[Groq] Reply received.")
        return reply.strip()
    except RateLimitError as exc:
        print(f"[Groq] Rate limit error: {exc}")
        raise RuntimeError("Groq rate limit reached. Please wait and try again.") from exc
    except APIConnectionError as exc:
        print(f"[Groq] Connection error: {exc}")
        raise RuntimeError("Could not connect to Groq. Check your network and API key.") from exc
    except APIError as exc:
        print(f"[Groq] API error: {exc}")
        raise RuntimeError(f"Groq API error: {getattr(exc, 'status_code', 'unknown')}") from exc
    except Exception as exc:
        print(f"[Groq] Unexpected error: {exc}")
        raise RuntimeError(f"Groq failed: {exc}") from exc


def _max_tokens_for(language: str) -> int:
    if language in {"kannada", "tamil", "telugu", "hindi"}:
        return 190
    return 105


def post_process_agent_response(text: str, max_sentences: int = 2) -> str:
    """Make Groq output short, phone-friendly, and easier for TTS."""
    cleaned = re.sub(r"[*_`#>\[\]{}]", "", text or "")
    cleaned = re.sub(r"\s*\n+\s*", " ", cleaned)
    cleaned = re.sub(r",{2,}", ",", cleaned)
    cleaned = re.sub(r"\s*,\s*", ", ", cleaned)
    cleaned = re.sub(r"([.!?।]){2,}", r"\1", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    if not cleaned:
        return ""

    sentences = _split_sentences(cleaned)
    short_sentences = []
    for sentence in sentences:
        short_sentences.extend(_split_long_sentence(sentence))
        if len(short_sentences) >= max_sentences:
            break
    result = " ".join(short_sentences[:max_sentences]).strip()
    if len(result) > 240:
        result = result[:240].rsplit(" ", 1)[0].strip()
    return result or cleaned


def _split_sentences(text: str) -> list[str]:
    matches = re.findall(r"[^.!?।॥。]+[.!?।॥。]?", text)
    return [item.strip() for item in matches if item.strip()]


def _split_long_sentence(sentence: str) -> list[str]:
    if len(sentence) <= 110:
        return [sentence]
    chunks = [
        part.strip()
        for part in re.split(
            r"\s*,\s+|\s+and\s+|\s+aur\s+|\s+और\s+|\s+toh\s+|\s+तो\s+|"
            r"\s+ಆದ್ರೆ\s+|\s+ಮತ್ತು\s+|\s+ana\s+|\s+aana\s+|\s+ஆனா\s+|\s+மற்றும்\s+|"
            r"\s+kani\s+|\s+కానీ\s+|\s+మరియు\s+",
            sentence,
        )
        if part.strip()
    ]
    if len(chunks) <= 1:
        return [sentence]
    return [f"{chunk}." if chunk[-1] not in ".!?।॥。" else chunk for chunk in chunks[:2]]


LEAD_ANALYSIS_PROMPT = """
You are a lead qualification analyst for Rupeezy RM handoff.
Analyze the conversation and return ONLY valid JSON with exactly these keys:
lead_score, lead_status, language_detected, main_objection,
conversation_summary, next_action, handoff_status.

Scoring rules:
- Hot: 75-100
- Warm: 40-74
- Cold: 0-39

Use short, clear business language for an RM dashboard.
Do not wrap the JSON in markdown.
"""


def analyze_lead(history: list) -> dict:
    """Call Groq for strict JSON lead qualification analysis."""
    print("[Groq] Lead analysis started.")
    messages = [
        {"role": "system", "content": LEAD_ANALYSIS_PROMPT},
        {
            "role": "user",
            "content": json.dumps(history, ensure_ascii=False),
        },
    ]

    try:
        completion = _build_client().chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=350,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content
        if not content:
            raise RuntimeError("Groq returned an empty lead analysis.")
        analysis = json.loads(content)
        score = int(analysis.get("lead_score", 50))
        score = max(0, min(100, score))
        if score >= 75:
            status = "Hot"
        elif score >= 40:
            status = "Warm"
        else:
            status = "Cold"
        analysis["lead_score"] = score
        analysis["lead_status"] = status
        print("[Groq] Lead analysis received.")
        return analysis
    except Exception as exc:
        print(f"[Groq] Lead analysis failed: {exc}")
        raise RuntimeError(f"Groq lead analysis failed: {exc}") from exc
