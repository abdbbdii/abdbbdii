import requests
import json


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

    def write(self, text, centered=True, summary=""):
        if centered:
            self.md += '<div align="center">\n\n'
        if summary:
            self.md += f"<details><summary>{summary}</summary>\n\n"
        self.md += text.strip() + "\n\n"
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
    def table(data, centered=False):
        """
        Creates a Markdown table from a list of lists.
        The first inner list is treated as the header.
        """
        if not data:
            return ""
        header = f"| {' | '.join(data[0])} |\n"
        separator = "| " + " | ".join([":---:" if centered else "---" for _ in data[0]]) + " |\n"
        rows = "".join([f"| {' | '.join(row)} |\n" for row in data[1:]])
        return header + separator + rows

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


def get_anime(username):
    md = ABDGHMD()
    r = requests.get("https://hianime-to-myanimelist.vercel.app/get_json_list", params={"username": username, "offset_inc": 1000}).json()
    for cat, raw_animes in r.items():
        animes = []
        for anime in raw_animes:
            animes.append(
                {
                    "Title": ABDGHMD._start_end(anime["title"], max=20),
                    "poster": f"![{anime['title']}]({anime['main_picture']['medium']})",
                }
            )
        temp_tables = ABDGHMD()
        max_len = 4
        for i in range(0, len(animes), max_len):
            temp_tables.write(ABDGHMD.table(ABDGHMD._list_dict_to_transformed_list(animes[i : i + max_len]), centered=True))
        md.write(str(temp_tables), centered=False, summary=cat.replace("_", " ").title())
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
    prefix = ":add"
    projects = []
    repos = GitHubAPI.get_repos(username)
    for repo in repos:
        if repo["description"] and repo["description"].strip().endswith(prefix):
            projects.append(
                {
                    "Project": f"[{repo['name']}]({repo['html_url']})",
                    "Description": repo["description"].rstrip(prefix).strip(),
                    "Created": repo["created_at"].split("T")[0],
                }
            )
    projects.sort(key=lambda x: x["Created"], reverse=True)
    return projects


def make_markdown():
    md = ABDGHMD()

    md.write(open("assets/md/header.md", encoding="utf-8").read())
    md.write(open("assets/md/description.md", encoding="utf-8").read())
    md.write(ABDGHMD.heading("Education & Certifications"))
    md.write(open("assets/md/education.md", encoding="utf-8").read(), centered=False)
    md.write(open("assets/md/certifications.md", encoding="utf-8").read(), centered=False)
    md.write(ABDGHMD.heading("Languages & Tools"))
    md.write(ABDGHMD.table(ABDGHMD._list_dict_to_list_list(json.load(open("assets/json/langs_tools.json")))))
    md.write(ABDGHMD.heading("Projects & Repositories"))
    md.write(ABDGHMD.table(ABDGHMD._list_dict_to_list_list(get_projects("abdbbdii"))))
    md.write(ABDGHMD.heading("GitHub Stats"))
    md.write(open("assets/md/github_stats.md", encoding="utf-8").read())
    md.write(ABDGHMD.heading("Hobbies & Interests"))
    md.write(open("assets/md/hobbies.md", encoding="utf-8").read(), centered=False)
    md.write(ABDGHMD.heading("My Anime List"))
    md.write(get_anime("abdbbdii"), centered=False)
    md.write(ABDGHMD.heading("Meet my Code Buddies!"))
    md.write(ABDGHMD.table(get_code_buddies(json.load(open("assets/json/code_buddies.json"))), centered=True))
    # md.write(ABDGHMD.heading("Connect with Me"))
    md.write(ABDGHMD.heading("Support Me"))
    md.write(open("assets/md/supportme.md", encoding="utf-8").read())
    md.write(open("assets/md/footer.md", encoding="utf-8").read())

    md.save("README.md")


if __name__ == "__main__":
    make_markdown()