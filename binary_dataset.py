import random
import json

# OVOS datasets from https://github.com/OpenVoiceOS/ovos-datasets
csv_path = f"/home/miro/PycharmProjects/OCP_sprint/OCP-dataset/dataset.csv"
q1 = f"/home/miro/PycharmProjects/OCP_sprint/OCP-dataset/yes_no.txt"
q2 = "/home/miro/PycharmProjects/OCP_sprint/OCP-dataset/raw_questions_0.7.0a1.txt"
q3 = "/home/miro/PycharmProjects/OCP_sprint/OCP-dataset/mycroft_simple_intents_v0.1.json"
q4 = "/home/miro/PycharmProjects/OCP_sprint/OCP-dataset/core_intents_v0.1(1).csv"
skips = ["bark-skill", "fairytalez-skill", "youtube-skill", "futurism-cartoons", "xkcd", "spotify-skill",
         "twitch-streams"  "moviemaster", "skystream", "bitchute-skill"]

with open(q1) as f:
    questions = f.read().split("\n")
with open(q2) as f:
    questions += [q.split(" ", 1)[1] for q in f.read().split("\n")]
with open(q3) as f:
    data = json.load(f)["en"]
    for intent, samples in data.items():
        if any(s in intent for s in skips):
            continue
        questions += samples
with open(q4) as f:
    questions += [q.split(",")[1] for q in f.read().split("\n")[1:]]

questions = list(set(questions))

with open(csv_path) as f:
    pb = [s.split(",")[1] for s in f.read().split("\n")[1:] if s.strip()]

print(len(questions), len(pb))

lines = [f"other,{l}" for l in questions] + [f"OCP,{l}" for l in pb]
random.shuffle(lines)
with open("ocp_sentences_v0.csv", "w") as f:
    f.write("intent_type,utterance\n")
    for l in lines:
        f.write(l + "\n")