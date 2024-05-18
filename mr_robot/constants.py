from os import getenv


class Client:
    name = "Mr Robot"
    token = getenv("BOT_TOKEN")
    github_db_repo = getenv("GIT_DB_REPO")
    github_token = getenv("GIT_TOKEN")
    github_bot_repo = "https://github.com/Mr-Robot-Discord-Bot/Mr-Robot/"
    support_server = "SUPPORT SERVER"
    version = getenv("VERSION")
