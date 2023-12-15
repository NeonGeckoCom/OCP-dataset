import os.path

import random
from unidecode import unidecode


def load_entities(path, lang):
    ents = { }

    # non wikidata entity list - manually maintained by users
    for e in os.listdir(f"{path}/manual_entities/{lang}"):
        with open(f"{path}/manual_entities/{lang}/{e}") as f:
            samples = f.read().split("\n")
            ents[e.replace(".entity", "").split("_Q")[0]] = samples

    # from sparql queries - auto generated
    for f in os.listdir(f"{path}/sparql_ocp/{lang}"):
        if not f.endswith(".entity"):
            continue
        # normalize and map to slots
        n = f.replace(".entity", "").split("_Q")[0]

        if n not in ents:
            ents[n] = []
        with open(f"{path}/sparql_ocp/{lang}/{f}") as fi:
            for s in fi.read().split("\n"):
                if s:
                    s = unidecode(s)
                    ents[n].append(s)

    return ents


def load_templates(path, lang):
    path = f"{path}/templates/{lang}"
    ents = {}
    with open(f"{path}/generic.intent") as f:
        GENERIC = f.read().split("\n")
    with open(f"{path}/generic_video.intent") as f:
        GENERIC2 = f.read().split("\n")
    for f in os.listdir(path):
        if f == "generic.intent":
            continue
        n = f.replace(".intent", "")
        if n not in ents:
            ents[n] = []
        with open(f"{path}/{f}") as fi:
            for s in fi.read().split("\n"):
                if s.startswith("#") or not s.strip():
                    continue
                ents[n].append(s)
        if n not in ["game", "movie", "series", "short_film", "silent_movie",
                     "video", "tv_channel", "comic", "bw_movie", "bts",
                     "anime", "cartoon"]:
            for g in GENERIC:
                ents[n].append(g.replace("{query}", "{" + n + "_genre}"))
                ents[n].append(g.replace("{query}", "{" + n + "_name}"))
        if n in ["movie", "series", "short_film", "silent_movie",
                 "video", "tv_channel", "comic", "bw_movie", "bts",
                 "anime", "cartoon"]:
            for g in GENERIC2:
                ents[n].append(g.replace("{query}", "{" + n + "_genre}"))
                ents[n].append(g.replace("{query}", "{" + n + "_name}"))
    return ents


p = os.path.dirname(__file__)
lang = "en"
ents = load_entities(p, lang)
templs = load_templates(p, lang)


# gen dataset, templates gathered manually from chatgpt
def generate_samples():
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


dataset = list(generate_samples())

with open("ocp_media_types_v0.csv", "w") as f:
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

with open("ocp_entities_v0.csv", "w") as f:
    f.write("label,entity\n")
    for label, samples in ents.items():
        if label == "radio_drama":
            label = "radio_drama_name"
        if label == "porn_site":
            label = "porn_streaming_service"
        for s in samples:
            f.write(f"{label},{s}\n")
