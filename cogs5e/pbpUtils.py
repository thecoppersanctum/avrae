"""
Created on Jan 13, 2017

@author: andrew
"""
from math import sqrt

import discord
from discord.ext import commands

from cogs5e.models import embeds
from utils.argparser import argparse
from utils.functions import clean_content


class PBPUtils(commands.Cog):
    """Commands to help streamline playing-by-post over Discord."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def echo(self, ctx, *, msg):
        """Echos a message."""
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.send(f"{ctx.author.display_name}: {clean_content(msg, ctx)}")

    @commands.command()
    async def techo(self, ctx, seconds: int, *, msg):
        """Echos a message, and deletes it after a few seconds."""
        try:
            await ctx.message.delete()
        except:
            pass

        seconds = min(max(0, seconds), 600)

        await ctx.send(f"{ctx.author.display_name}: {clean_content(msg, ctx)}", delete_after=seconds)

    @commands.command()
    async def embed(self, ctx, *, args):
        """Creates and prints an Embed.
        __Valid Arguments__
        -title <title>
        -desc <description text>
        -thumb <image url>
        -image <image url>
        -footer <footer text>
        -f "<Field Title>|<Field Text>[|inline]"
            (e.g. "Donuts|I have 15 donuts|inline" for an inline field, or "Donuts|I have 15 donuts" for one with its own line.)
        -color <hex color>
        -t <timeout (0..600)>
        """
        try:
            await ctx.message.delete()
        except:
            pass

        embed = embeds.EmbedWithAuthor(ctx)
        args = argparse(args)
        embed.title = args.last('title')
        embed.description = args.last('desc')
        embed.set_thumbnail(url=args.last('thumb', '') if 'http' in str(args.last('thumb')) else '')
        embed.set_image(url=args.last('image', '') if 'http' in str(args.last('image')) else '')
        embed.set_footer(text=args.last('footer', ''))
        try:
            embed.colour = int(args.last('color', "0").strip('#'), base=16)
        except:
            pass

        embeds.add_fields_from_args(embed, args.get('f'))

        timeout = 0
        if 't' in args:
            try:
                timeout = min(max(args.last('t', type_=int), 0), 600)
            except:
                pass

        if timeout:
            await ctx.send(embed=embed, delete_after=timeout)
        else:
            await ctx.send(embed=embed)

    @commands.command()
    async def br(self, ctx):
        """Prints a scene break."""
        try:
            await ctx.message.delete()
        except:
            pass

        await ctx.send("``` ```")

    @commands.command(hidden=True)
    async def pythag(self, ctx, num1: int, num2: int):
        """Performs a pythagorean theorem calculation to calculate diagonals."""
        await ctx.send(sqrt(num1 ** 2 + num2 ** 2))


def setup(bot):
    bot.add_cog(PBPUtils(bot))
