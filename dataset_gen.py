import os.path
import random

from ocp_nlp.features import KeywordFeatures

dataset = []


# gen dataset, templates gathered manually from chatgpt
def generate_samples(p, lang):
    m = KeywordFeatures(lang)
    ents = m.load_entities(p)
    templs = m.load_templates(p)

    for media_type, templates in templs.items():
        for t in templates:
            t = t.rstrip(".!?,;:")
            words = t.split()
            slots = [w for w in words if w.startswith("{") and w.endswith("}")]
            if slots and any(s[1:-1] not in ents for s in slots):
                continue
            for ent, samples in ents.items():
                if ent in t:
                    if not samples:
                        break
                    t = t.replace("{" + ent + "}", random.choice(samples))

            if "{" not in t:
                yield media_type, t
            else:
                print("bad template", t)


p = os.path.dirname(__file__)
lang = "en"
for i in range(1):  # N times each template
    dataset += list(generate_samples(p, lang))

with open(f"{os.path.dirname(p)}/dataset.csv", "w") as f:
    f.write("label, sentence\n")
    for label, sentence in set(dataset):
        f.write(f"{label}, {sentence}\n")

# dedup files
for root, folders, files in os.walk(os.path.dirname(__file__)):
    for f in files:
        if not f.endswith(".entity") and not f.endswith(".intent"):
            continue
        print(f"{root}/{f}")
        with open(f"{root}/{f}") as fi:
            lines = set(fi.read().split("\n"))
        with open(f"{root}/{f}", "w") as fi:
            fi.write("\n".join(sorted(lines)))


m = KeywordFeatures(lang)
ents = m.load_entities(p)


with open("ocp_entities.csv", "w") as f:
    f.write("label,entity\n")
    for ent, samples in ents.items():
        for s in samples:
            f.write(f"{ent},{s}\n")