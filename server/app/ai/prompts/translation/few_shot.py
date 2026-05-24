from __future__ import annotations

from app.ai.prompts.base import ChatMessage


def few_shot_translation_examples() -> list[ChatMessage]:
    # Keep examples short and translation-only. Telugu is written with escapes
    # to avoid accidental mojibake on Windows consoles/editors.
    return [
        ChatMessage(role="user", content="Target language: Telugu\nTranslate the text below. Output ONLY the translated text:\n\nHello, how are you?"),
        ChatMessage(role="assistant", content="\u0c39\u0c32\u0c4b, \u0c2e\u0c40\u0c30\u0c41 \u0c0e\u0c32\u0c3e \u0c09\u0c28\u0c4d\u0c28\u0c3e\u0c30\u0c41?"),
        ChatMessage(role="user", content="Target language: Telugu\nTranslate the text below. Output ONLY the translated text:\n\nHey Im Lokesh"),
        ChatMessage(role="assistant", content="\u0c39\u0c3e\u0c2f\u0c4d, \u0c28\u0c47\u0c28\u0c41 \u0c32\u0c4b\u0c15\u0c47\u0c37\u0c4d"),
        ChatMessage(role="user", content="Target language: Telugu\nTranslate the text below. Output ONLY the translated text:\n\nHey I love Druvija"),
        ChatMessage(role="assistant", content="\u0c39\u0c3e\u0c2f\u0c4d, \u0c28\u0c3e\u0c15\u0c41 \u0c26\u0c4d\u0c30\u0c41\u0c35\u0c3f\u0c1c\u0c3e \u0c05\u0c02\u0c1f\u0c47 \u0c1a\u0c3e\u0c32\u0c3e \u0c07\u0c37\u0c4d\u0c1f\u0c02"),
        ChatMessage(role="user", content="Target language: Hindi\nTranslate the text below. Output ONLY the translated text:\n\n\u0c39\u0c3e\u0c2f\u0c4d, \u0c28\u0c47\u0c28\u0c41 \u0c35\u0c47\u0c26\u0c28\u0c3f. \u0c28\u0c47\u0c28\u0c41 \u0c1a\u0c3e\u0c32\u0c3e \u0c1a\u0c26\u0c41\u0c35\u0c41\u0c24\u0c3e\u0c28\u0c41."),
        ChatMessage(role="assistant", content="\u0939\u093e\u092f, \u092e\u0948\u0902 \u0935\u0947\u0926\u0928\u0940 \u0939\u0942\u0901\u0964 \u092e\u0948\u0902 \u092c\u0939\u0941\u0924 \u092a\u0922\u093c\u0924\u0940 \u0939\u0942\u0901\u0964"),
        ChatMessage(role="user", content="Target language: English\nTranslate the text below. Output ONLY the translated text:\n\n\u0c39\u0c3e\u0c2f\u0c4d, \u0c28\u0c47\u0c28\u0c41 \u0c35\u0c47\u0c26\u0c28\u0c3f. \u0c28\u0c47\u0c28\u0c41 \u0c1a\u0c3e\u0c32\u0c3e \u0c1a\u0c26\u0c41\u0c35\u0c41\u0c24\u0c3e\u0c28\u0c41."),
        ChatMessage(role="assistant", content="Hi, I am Vedani. I read a lot."),
    ]
