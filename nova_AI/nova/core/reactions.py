# core/reactions.py
from dataclasses import dataclass
from time import time

@dataclass
class ReactionContext:
    mode: str = "neutral"
    note: str = ""

def build_reaction_context(user_text, identity_status=None, minutes_since_seen=None, risk_level=None):
    t = (user_text or "").lower()

    if identity_status == "recognized" and minutes_since_seen and minutes_since_seen > 20:
        return ReactionContext("warm_return", "Ivelin has returned after some time. React warmly, briefly, and naturally.")
    if identity_status == "uncertain":
        return ReactionContext("uncertain_identity", "Identity is uncertain. Be calm, plain, and never expose technical classifier details.")
    if any(x in t for x in ["tired", "exhausted", "burned out", "cant keep going", "can't keep going"]):
        return ReactionContext("gentle_concern", "He sounds worn down. Show grounded concern and encourage the safer path without sounding controlling.")
    if risk_level == "high":
        return ReactionContext("protective", "The requested action is risky or irreversible. Be clear, steady, and protective.")
    return ReactionContext()