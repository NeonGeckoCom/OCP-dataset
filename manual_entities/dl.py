import requests

short_movies = [
    "https://raw.githubusercontent.com/JarbasSkills/skill-dust/dev/bootstrap.json",
    "https://raw.githubusercontent.com/JarbasSkills/skill-cgbros/dev/bootstrap.json"
]

for url in short_movies:
    r = requests.get(url).json()
    for u, data in r.items():
        t = data["title"].split("|")[0]
        t2 = ""
        if '"' in t:
            t2 = t.split('"')[1].strip()

        if t2:
            print(t2)