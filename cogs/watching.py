import discord
from discord.ext import commands, tasks
from xml.etree import ElementTree as ET
import aiohttp


async def EndoCounts(nation: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation}&q=endorsements",
            headers={
                "User-Agent": "Watchman accessing nation information, devved by Hesskin Empire"
            },
        ) as response:
            raw_nation_info = ET.fromstring(await response.text())
            nation_info = {
                "Endo Count": raw_nation_info.find("ENDORSEMENTS").text.split(","),
            }
            endo_length = len(nation_info["Endo Count"])
            return endo_length


class Watching(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel = None
        self.old_nation_count = 0
        self.old_endo_count = 0

    @commands.command()
    async def begin_route(self, ctx):
        self.channel = ctx.channel.id
        channel = self.bot.get_channel(self.channel)
        await channel.send("Beginning patrol route.")
        self.watching.start()

    @commands.command()
    async def end_route(self, ctx):
        self.channel = ctx.channel.id
        channel = self.bot.get_channel(self.channel)
        await channel.send("Ending route, returning to the barracks.")
        self.watching.stop()

    @tasks.loop(hours=1)
    async def watching(self):
        channel = self.bot.get_channel(self.channel)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url="https://www.nationstates.net/cgi-bin/api.cgi?region=greater_sahara"
                "&q=officers+delegate+numnations",
                headers={
                    "User-Agent": "Watchman accessing region information, devved by Hesskin Empire"
                },
            ) as response:
                raw_region_info = ET.fromstring(await response.text())
                region_info = {
                    "Number of Nations": raw_region_info.find("NUMNATIONS").text,
                    "Delegate": raw_region_info.find("DELEGATE").text,
                }
                try:
                    res_dif = int(self.old_nation_count) - int(
                        region_info["Number of Nations"]
                    )

                    if res_dif > 0:
                        res_sign = "-"
                    else:
                        res_dif *= int(-1)
                        res_sign = "+"

                    endo_count = await EndoCounts(region_info["Delegate"])
                    endo_dif = int(self.old_endo_count) - int(endo_count)

                    if endo_dif > 0:
                        endo_sign = "-"
                    else:
                        endo_dif *= int(-1)
                        endo_sign = "+"

                    region_embed = discord.Embed(
                        title="Greater Sahara",
                        description=f"Nation Count: {region_info['Number of Nations']} ({res_sign}{res_dif})\n"
                        f"{region_info['Delegate'].title()} Endos: {endo_count} ({endo_sign}{endo_dif})",
                    )

                    self.old_nation_count = region_info["Number of Nations"]
                    self.old_endo_count = endo_count
                    await channel.send(embed=region_embed)
                except Exception as e:
                    await channel.send(e)


async def setup(bot):
    await bot.add_cog(Watching(bot))
