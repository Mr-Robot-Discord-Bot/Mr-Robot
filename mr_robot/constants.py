from os import getenv


class Client:
    name = "Mr Robot"
    token = getenv("BOT_TOKEN")
    log_file_name = "mr-robot.log"
    db_name = "mr-robot.db"
    github_db_repo = getenv("GIT_DB_REPO")
    github_token = getenv("GIT_TOKEN")
    github_bot_repo = "https://github.com/Mr-Robot-Discord-Bot/Mr-Robot/"
    support_server = "55TQeTvU6f"
    version = getenv("VERSION")
    nsfw_api = getenv("NSFW_API")
    gemini_api_key = getenv("AI_API_KEY")
    on_join_webook = getenv("ON_JOIN_WEBHOOK")


class ButtonCustomId:
    delete = "message_delete:"
