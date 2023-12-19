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


def load_not_ocp(path="ocp_sentences_v0.csv"):
    with open(path) as f:
        lines = f.read().split("\n")[1:]
    return [l.split(",", 1)[-1] for l in lines if l.split(",")[0] != "OCP"]

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


def generate_balanced(n_per_label=1200):
    counts = {l: 0 for l in templs if "generic_" not in l}
    while not all((c >= n_per_label for c in counts.values())):
        print(counts)
        for media_type, templates in templs.items():
            if media_type not in counts or counts[media_type] >= n_per_label:
                continue
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
                    counts[media_type] += 1
                    if counts[media_type] >= n_per_label:
                        break
                else:
                    print("bad template", t)


dataset = list(set(generate_samples()))

with open("ocp_media_types_v0.csv", "w") as f:
    f.write("label, sentence\n")
    for label, sentence in set(dataset):
        label = label.strip()
        if label in [ "iot_playback"]:
            continue
        f.write(f"{label},{sentence}\n")


with open("ocp_playback_type_v0.csv", "w") as f:
    f.write("label, sentence\n")
    for label, sentence in set(dataset):
        label = label.strip()
        if label in ["game", "iot_playback"]:
            label = "external"
        elif label in ["movie", "bw_movie", "silent_movie", "trailer", "comic",
                       "bts", "documentary", "anime", "hentai", "cartoon", "short_film",
                       "adult", "video", "tv_channel", "series"]:
            label = "video"
        elif label in ["music", "podcast", "ad", "radio", "adult_asmr",
                       "audio", "radio_drama", "audiobook"]:
            label = "audio"
        elif any(sentence.lower().startswith(w) for w in ["watch ", "view "]):
            label = "video"
        elif any(sentence.lower().startswith(w) for w in ["listen ", "tell me "]):
            label = "audio"
        elif any(w in sentence.lower().split() for w in ["tv", "youtube", "netflix", "channel", "video", "videos"]):
            label = "video"
        elif any(w in sentence.lower().split() for w in ["podcast", "radio", "spotify", "sound", "sounds", "audio"]):
            label = "audio"
        else:
            print("bad label", label, sentence)
            continue
        f.write(f"{label},{sentence}\n")


dataset = list(set(generate_balanced(1200)))

with open("ocp_media_types_balanced_big_v0.csv", "w") as f:
    f.write("label, sentence\n")
    for label, sentence in set(dataset):
        if label in [ "iot_playback"]:
            continue
        label = label.strip()
        f.write(f"{label},{sentence}\n")

dataset = list(set(generate_balanced(100)))

with open("ocp_media_types_balanced_small_v0.csv", "w") as f:
    f.write("label, sentence\n")
    for label, sentence in set(dataset):
        if label in [ "iot_playback"]:
            continue
        label = label.strip()
        f.write(f"{label},{sentence}\n")


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

# skip these wikidata entries
BAD_AUDIO = ["audio drama",
             "audio podcast",
             "audiobook",
             "erotic audio recording",
             "ASMR recording",
             "ASMRotica",
             "literary fiction audio recording",
             "podcast",
             "poetry audio recording",
             "radio broadcast recording",
             "radio drama",
             "radio show recording"]
with open("ocp_entities_v0.csv", "w") as f:
    f.write("label,entity\n")
    for label, samples in ents.items():
        label = label.strip()
        if label == "audio":
            samples = [s for s in samples if s not in BAD_AUDIO]
        if label == "radio_drama":
            label = "radio_drama_name"
        if label == "porn_site":
            label = "porn_streaming_service"
        for s in samples:
            f.write(f"{label},{s}\n")
