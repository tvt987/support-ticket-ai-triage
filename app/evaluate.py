"""Small, reproducible baseline evaluation on synthetic cases."""
from .core import classify

CASES = [
    ("Refund pending", "I requested a refund for my order.", "refund"),
    ("Delivery delay", "Where is the parcel tracking update?", "delivery"),
    ("Cannot login", "My account password is not working.", "account"),
    ("Damaged item", "The product arrived broken.", "product"),
    ("General question", "I have a question about your company.", "other"),
]


if __name__ == "__main__":
    correct = 0
    for subject, message, expected in CASES:
        actual = classify(subject, message).category
        correct += actual == expected
        print(f"{subject}: expected={expected} actual={actual}")
    print(f"Baseline category accuracy: {correct}/{len(CASES)} on synthetic fixtures")
