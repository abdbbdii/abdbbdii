import requests
import json
import re
import datetime


class GitHubAPI:

    GH_API_ENDPOINT = "https://api.github.com/"

    @staticmethod
    def get_user(username):
        return requests.get(GitHubAPI.GH_API_ENDPOINT + f"users/{username}").json()

    @staticmethod
    def get_repos(username):
        return requests.get(GitHubAPI.GH_API_ENDPOINT + f"users/{username}/repos").json()


class ABDGHMD:
    def __init__(self):
        self.md = ""

    def write(self, text, centered=True, summary="", sep='\n\n'):
        if centered:
            self.md += '<div align="center">\n\n'
        if summary:
            self.md += f"<details><summary>{summary}</summary>\n\n"
        self.md += text.strip() + sep
        if summary:
            self.md += "</details>\n\n"
        if centered:
            self.md += "</div>\n\n"

    @staticmethod
    def heading(text):
        return open("assets/md/heading_template.md").read().strip().replace(r"{heading}", text)

    @staticmethod
    def _list_dict_to_list_list(data):
        """
        Converts a list of dictionaries into a list of lists where the first list contains the keys,
        and subsequent lists contain the corresponding values.
        If a value is a list, it joins the elements with a space.
        """
        if not data:
            return []

        headers = list(data[0].keys())

        def format_value(value):
            if isinstance(value, list):
                return " ".join(map(str, value))
            return str(value)

        values = [[format_value(value) for value in item.values()] for item in data]
        return [headers] + values

    @staticmethod
    def _list_dict_to_transformed_list(data):
        """
        Transforms a list of dictionaries into a list of lists where each inner list
        contains the values corresponding to the same key across all dictionaries.
        """
        if not data:
            return []
        grouped_dict = {key: [] for key in data[0]}
        for item in data:
            for key, value in item.items():
                grouped_dict[key].append(str(value))
        return [grouped_dict[key] for key in grouped_dict]

    @staticmethod
    def table(data, centered=False, header=True):
        """
        Creates a Markdown table from a list of lists.
        The first inner list is treated as the header.
        """
        if not data:
            return ""
        head = f"| {' | '.join(data[0])} |\n"
        separator = "| " + " | ".join([":---:" if centered else "---" for _ in data[0]]) + " |\n"
        rows = "".join([f"| {' | '.join(row)} |\n" for row in data[1:]])
        if header:
            return head + separator + rows
        return head + rows

    @staticmethod
    def _start_end(text, max=20):
        if len(text) > max:
            return text[: max - 5] + "..." + text[-5:]
        return text

    def __str__(self):
        return self.md.strip()

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.md.strip())

import requests

def fetch_anilist(username):
    md = ABDGHMD()
    url = "https://graphql.anilist.co"
    query = """
    query ($username: String) {
      MediaListCollection(userName: $username, type: ANIME) {
        lists {
          entries {
            media {
              title {
                romaji
                english
              }
              siteUrl
              coverImage {
                large
              }
            }
            status
          }
        }
      }
    }
    """
    variables = {"username": username}
    response = requests.post(url, json={"query": query, "variables": variables}).json()

    if 'data' not in response or not response['data'] or 'MediaListCollection' not in response['data']:
        return "Error: Unable to fetch data from AniList. Please check the username or try again later."

    lists = response['data']['MediaListCollection']['lists']
    if not lists:
        return "No anime lists found for this user."

    for lst in lists:
        animes = []
        for entry in lst['entries']:
            media = entry['media']
            title = media['title']['english'] or media['title']['romaji']
            animes.append({
                "Title": ABDGHMD._start_end(title, max=20),
                "poster": f"[![{title}]({media['coverImage']['large']})]({media['siteUrl']})",
            })

        # Group anime by status
        status = entry['status'].replace("_", " ").title()
        temp_tables = ABDGHMD()
        max_len = 4
        for i in range(0, len(animes), max_len):
            temp_tables.write(
                ABDGHMD.table(ABDGHMD._list_dict_to_transformed_list(animes[i : i + max_len]), 
                centered=True, 
                header=True if i == 0 else False
            ), 
            centered=False, 
            sep="\n"
        )
        md.write(str(temp_tables), centered=False, summary=status)

    return str(md)
    
def get_anime(username):
    md = ABDGHMD()
    r = requests.get("https://hianime-to-myanimelist.vercel.app/get_json_list", params={"username": username, "offset_inc": 1000}).json()
    for cat, raw_animes in r.items():
        animes = []
        for anime in raw_animes:
            animes.append(
                {
                    "Title": ABDGHMD._start_end(anime["title"], max=20),
                    "poster": f"[![{anime['title']}]({anime['main_picture']['medium']})](https://myanimelist.net/anime/{anime['id']})",
                }
            )
        temp_tables = ABDGHMD()
        max_len = 4
        for i in range(0, len(animes), max_len):
            temp_tables.write(ABDGHMD.table(ABDGHMD._list_dict_to_transformed_list(animes[i : i + max_len]), centered=True, header=True if i == 0 else False), centered=False, sep="\n")
        md.write(str(temp_tables), centered=False, summary=cat.replace("_", " ").title())
    return str(md)


def get_games(username):
    md = ABDGHMD()
    statuses = [
        "beaten",
        "playing",
        "yet",
        "toplay",
        "dropped",
        "owned",
    ]
    for status in statuses:
        games = []
        i = 1
        while True:
            r = requests.get(f"https://api.rawg.io/api/users/{username}/games", params={"page": i, "statuses": status, "page_size": 100, "ordering": "-released"}).json()
            for game in r["results"]:
                games.append(
                    {
                        "Title": ABDGHMD._start_end(game["name"], max=20),
                        "Poster": f"![{game['name']}]({'https://media.rawg.io/media/crop/600/400/'+ '/'.join(game['background_image'].split("/")[-3:])})",
                    }
                )
            if r.get("next") is None:
                break
            i += 1
        if not games:
            continue
        temp_tables = ABDGHMD()
        max_len = 3
        for i in range(0, len(games), max_len):
            temp_tables.write(ABDGHMD.table(ABDGHMD._list_dict_to_transformed_list(games[i : i + max_len]), centered=True, header=True if i == 0 else False), centered=False, sep="\n")
        md.write(str(temp_tables), centered=False, summary=status.title())
    return str(md)


def get_code_buddies(code_buddies):
    buddies = []
    for buddy in code_buddies:
        r = GitHubAPI.get_user(buddy)
        buddies.append(
            {
                "Name": r["name"],
                "Avatar": f"[![@{r['login']}](https://github.com/{r['login']}.png?size=150)]({r['html_url']})",
                "GitHub": f"[@{r['login']}]({r['html_url']})",
            }
        )
    return ABDGHMD._list_dict_to_transformed_list(buddies)


def get_projects(username):

    def snake_to_title(s: str) -> str:
        s = s.replace("-", " ").replace("_", " ")
        return ' '.join(word[0].upper() + word[1:] if word else '' for word in s.split(' '))


    def camel_to_title(s: str) -> str:
        if "LaTeX" in s:
            return s
        return re.sub(r'([a-z])([A-Z])', r'\1 \2', s)

    suffix = ":add"
    projects = []
    repos = GitHubAPI.get_repos(username)
    for repo in repos:
        if repo["description"] and repo["description"].strip().endswith(suffix):
            projects.append(
                {
                    "Project": f"[{camel_to_title(snake_to_title(repo['name']))}]({repo['html_url']})",
                    "Description": repo["description"].rstrip(suffix).strip(),
                    "Created": repo["created_at"].split("T")[0],
                }
            )
    projects.sort(key=lambda x: x["Created"], reverse=True)
    return projects


def make_markdown():
    md = ABDGHMD()

    md.write(open("assets/md/header.md", encoding="utf-8").read())
    md.write(open("assets/md/description.md", encoding="utf-8").read())
    # md.write(ABDGHMD.heading("Education & Certifications"))
    # md.write(open("assets/md/education.md", encoding="utf-8").read(), centered=False)
    # md.write(open("assets/md/certifications.md", encoding="utf-8").read(), centered=False)
    # md.write(ABDGHMD.heading("GitHub Stats"))
    md.write(ABDGHMD.heading("Languages & Tools"))
    md.write("Whether it’s `Python`, `C`, or `JavaScript`, I’m fluent in *\"I’ll Google it real quick.\"* 👀")
    md.write(open("assets/md/github_stats.md", encoding="utf-8").read())
    md.write(ABDGHMD.table(ABDGHMD._list_dict_to_list_list(json.load(open("assets/json/langs_tools.json")))))
    md.write(ABDGHMD.heading("Projects & Repositories"))
    md.write("Here lives my ideas, my chaos, and my *\"I’ll finish this later\"* promises. 💡")
    md.write(ABDGHMD.table(ABDGHMD._list_dict_to_list_list(get_projects("abdbbdii"))))
    md.write(ABDGHMD.heading("Hobbies & Interests"))
    md.write(open("assets/md/hobbies.md", encoding="utf-8").read(), centered=False)
    md.write(ABDGHMD.heading("Anime List"))
    md.write("I’m starting to think my *\"Planning to watch\"* list and my *\"Issues\"* tab are the same thing. 😐")
    md.write(open("assets/md/anilist.md", encoding="utf-8").read())
    md.write(fetch_anilist("abdbbdii"), centered=False)
    md.write(ABDGHMD.heading("Game List"))
    md.write("I’m not a pro gamer, I’m a *professional respawner*. 💀")
    md.write(get_games("abdbbdii"), centered=False)
    md.write(ABDGHMD.heading("Meet my Code Buddies!"))
    md.write("From clean code to genius ideas, they’re the real MVPs of the dev world. 😎")
    md.write(ABDGHMD.table(get_code_buddies(json.load(open("assets/json/code_buddies.json"))), centered=True))
    # md.write(ABDGHMD.heading("Connect with Me"))
    md.write(ABDGHMD.heading("Support Me"))
    md.write(open("assets/md/supportme.md", encoding="utf-8").read())
    request = requests.Request("GET", "https://abd-utils-server.vercel.app/service/trigger-workflow/", params={"owner": "abdbbdii", "repo": "abdbbdii", "event": "update-readme", "redirect_uri": "https://github.com/abdbbdii"}).prepare().url
    md.write(f"[![Click to Update](https://img.shields.io/badge/Update-Last_Updated:_{str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')).replace(' ','_').replace('-', '--')}_UTC-ffffff?style=for-the-badge&color=080808)]({request})")
    md.write(open("assets/md/footer.md", encoding="utf-8").read())

    md.save("README.md")


if __name__ == "__main__":
    make_markdown()
