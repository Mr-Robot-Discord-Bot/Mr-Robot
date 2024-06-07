from os import getenv


class Client:
    """Client Constants"""

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
    debug_mode = True
    debug_guilds = [1241678951307542538]


class ButtonCustomId:
    """Button Custom Ids"""

    delete = "message_delete:"


class Colors:
    """Colours"""

    red = 0xFF0000
    green = 0x00FF00
    blue = 0x0000FF
    black = 0x000000
    orange = 0xFFA500
    yellow = 0xFFFF00
