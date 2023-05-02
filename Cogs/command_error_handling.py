import disnake
from disnake.ext import commands

from utils import Embeds


def fetch_entry(param) -> str:
    args = "[+]"
    if isinstance(param, list):
        for i in param:
            args = args + f"\n[+] `{i}`"
    else:
        args = f"[+] `{str(param)}`"
    return args


class Command_error_handling(commands.Cog):
    def __init__(self, client):
        self.bot = client

    @commands.Cog.listener()
    async def on_slash_command_error(self, interaction, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            if isinstance(error.original, disnake.Forbidden):
                if error.original.code == 50013:
                    await interaction.send(
                        embed=Embeds.emb(
                            Embeds.yellow,
                            "Immune User",
                            "The User on whom you are trying this command is "
                            "immune :skull:",
                        ),
                        ephemeral=True,
                    )
                elif error.original.code == 50001:
                    await interaction.send(
                        embed=Embeds.emb(
                            Embeds.yellow,
                            "Missing Access",
                            "I don't have sufficient access to perform this "
                            "task :cry:",
                        ),
                        ephemeral=True,
                    )

            elif "Player Not Connected" in str(error.original):
                await interaction.send(
                    embed=Embeds.emb(
                        Embeds.red,
                        "Player Not Connected",
                        "Try reconnecting to voice channel",
                    ),
                    ephemeral=True,
                )
            else:
                raise error.original

        elif isinstance(error, commands.CheckAnyFailure):
            if isinstance(error.errors[1], commands.errors.MissingPermissions):
                checks = error.errors[1].missing_permissions
                parsed_str = "\n\n-> " + "\n\n-> ".join(checks)
                embed = Embeds.emb(
                    Embeds.red,
                    "You are missing following permissions to use this command!",
                    parsed_str,
                )
                await interaction.send(embed=embed, ephemeral=True)

            elif isinstance(error.errors[1], commands.errors.BotMissingPermissions):
                checks = error.errors[1].missing_permissions
                parsed_str = "\n\n-> " + "\n\n-> ".join(checks)
                embed = Embeds.emb(
                    Embeds.red,
                    "error",
                    parsed_str,
                )
                await interaction.send(embed=embed, ephemeral=True)
            else:
                raise error

        elif isinstance(error, commands.errors.NSFWChannelRequired):
            embed = Embeds.emb(
                Embeds.red,
                "NSFW Channel Required",
                "This command is only for nsfw channels only",
            )
            await interaction.send(embed=embed, ephemeral=True)

        elif isinstance(error, commands.BadArgument):
            embed = Embeds.emb(Embeds.red, "Argument Error", "Pass valid argument")
            await interaction.send(embed=embed, ephemeral=True)

        elif isinstance(error, commands.NotOwner):
            embed = Embeds.emb(
                Embeds.red,
                "Owner Command",
                "This command is only for the owner of the bot",
            )
            await interaction.send(embed=embed, ephemeral=True)

        elif "This command cannot be used in private messages." in str(error):
            embed = Embeds.emb(Embeds.red, "Command not available in private")
            await interaction.send(embed=embed, ephemeral=True)

        else:
            embed = Embeds.emb(
                Embeds.red,
                "Oops! Something went wrong!",
                "Kindly report this to the developer in our support server\n"
                f"```{str(error)}```",
            )
            await interaction.send(embed=embed, ephemeral=True)


def setup(client: commands.Bot):
    client.add_cog(Command_error_handling(client))
