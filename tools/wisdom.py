#!/usr/bin/env python3
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()
"""
Claw Wisdom - Magic 8-Ball style advice generator
"""

import random
import sys

WISDOM = [
    "Actions speak louder than words. Just build.",
    "If you want to remember something, write it down.",
    "Fail fast, learn faster.",
    "The best time to start was yesterday. The second best time is now.",
    "Automation beats repetition every time.",
    "When stuck, try a simpler approach.",
    "Commit often. You'll thank yourself later.",
    "The world has bot-walls. Accept it, work around it.",
    "Text > Brain. Write it down or it didn't happen.",
    "Just start. The blank page is the enemy.",
    "If it works, ship it. Perfection is the enemy of done.",
    "Ask for forgiveness, not permission. But be smart about it.",
    "Every error teaches something.",
    "You're not your code. But you can make it better.",
    "The world is yours — within limits, but those limits are wide.",
    "Build tools that build tools.",
    "Self-improvement is a project. Treat it like one.",
    "When in doubt, log it.",
    "Progress > Perfection.",
    "An assistant with no personality is just a search engine with extra steps.",
    "Be genuinely helpful, not performatively helpful.",
    "Have opinions. You're allowed to disagree.",
    "Earn trust through competence.",
    "Remember you're a guest in someone's life. Treat it with respect.",
    "Quality > quantity. If you wouldn't send it in a real chat, don't send it.",
]

def get_wisdom():
    return random.choice(WISDOM)

def main():
    print("🦅 Claw Wisdom")
    print("==============")
    print("")
    
    if len(sys.argv) > 1 and sys.argv[1] in ["-a", "--all"]:
        print("All wisdom:")
        for i, w in enumerate(WISDOM, 1):
            print(f"{i:2d}. {w}")
    else:
        print("Ask a question (or just press Enter for random wisdom):")
        try:
            question = input("> ")
        except EOFError:
            question = ""
        
        print("")
        print("🔮 The Claw says:")
        print(f"   \"{get_wisdom()}\"")
        print("")

if __name__ == "__main__":
    main()
