import discord
from discord.ext import tasks
from modules.config import Config
from modules.framagenda import *
from ics import Calendar
import arrow
from collections import defaultdict

config = Config('config/config.yml')  # Create the Config instance
config.load()  # Load the config file

discord_token = config.get_config('discord', 'token')
discord_channel = config.get_config('discord', 'channel')
discord_guild = config.get_config('discord', 'guild')
calendar_url = config.get_config('calendar', 'url')

bot = discord.Bot(guild_ids=[discord_guild]) # this is the only parameter that is not optional

@tasks.loop(hours=24)
async def daily_task():
    # Get current date
    current_date = arrow.now()
    channel = bot.get_channel(discord_channel)
    # Check if it's Monday (0 means Monday)
    today = arrow.now().format('YYYY-MM-DD')
    week = arrow.now().shift(days=+7).format('YYYY-MM-DD')
    if current_date.weekday() == 0 and current_date.hour == 8:
        await send_events(None, channel, today, week, "pour cette semaine")
    elif current_date.weekday() != 0 and current_date.hour == 8:
        await send_events(None, channel, today, today, 'pour aujourd\'hui')

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    print(f"Connected to {len(bot.guilds)} guilds!")
    print(f"Updating calendar...")
    download_calendar(calendar_url)
    print("Syncing commands...")
    await bot.sync_commands(force=True)
    print("Done!")
    print(f"Starting daily task...")
    daily_task.start()
    print("Done!")

@bot.command(name='ping', description="Sends the bot's latency.") # this decorator makes a slash command
async def ping_command(ctx):
    # Perform the latency calculation
    latency = round(bot.latency * 1000)
    # Edit the loading message with the actual response
    await ctx.respond(f"Pong! ({latency}ms)")

async def send_events(ctx, channel, start_date, end_date, time_range):
    events = parse_calendar(start_date, end_date)
    # Get all unique words in event names
    event_name_words = set(word for event in events for word in event.name.split())

    # Check for "DISTANCIEL" and "PRESENTIEL" in event names
    event_mode = []
    if "DISTANCIEL" in event_name_words:
        event_mode.append("DISTANCIEL")
    if "PRESENTIEL" in event_name_words:
        event_mode.append("PRESENTIEL")

    if len(events) == 0:
        embed_title = f"📅 Agenda {time_range}"
        embed_description = f"Bonjour ! Il n'y a pas de cours prévu {time_range} !"
        embed = discord.Embed(title=embed_title, description=embed_description, color=discord.Color.blue())
    else:
        events_by_day = defaultdict(list)
        for event in events:
            events_by_day[event.begin.format('YYYY-MM-DD')].append(event)

        embed_title = f"📅 Agenda {time_range}"
        if event_mode:
            embed_title += f" ({', '.join(event_mode)})"

        embed = discord.Embed(title=embed_title, color=discord.Color.orange())

        for day, events in sorted(events_by_day.items(), key=lambda item: arrow.get(item[0], 'YYYY-MM-DD')):
            events_str = ""
            for event in sorted(events, key=lambda e: e.begin):
                if "DISTANCIEL" in event.name or "PRESENTIEL" in event.name:
                    continue
                description = f"Description: {event.description}\n" if event.description else ""
                location = f"Lieu: {event.location}\n" if event.location else ""
                events_str += f"\n**{event.name}**\De {event.begin.format('HH:mm')} à {event.end.format('HH:mm')}\n{description}{location}"
            embed.add_field(name=arrow.get(day, 'YYYY-MM-DD').format('dddd D MMMM YYYY', locale='fr').capitalize(), value=events_str, inline=True)

    if ctx is not None and isinstance(ctx, discord.Interaction):
        # If this is an interaction, send the actual response
        await ctx.send(embed=embed)
    else:
        await channel.send(embed=embed)

@bot.command(name='today', description="Sends today's events.")
async def today_command(ctx):
    await ctx.defer(ephemeral=True)  # Defer the interaction
    today = arrow.now().format('YYYY-MM-DD')
    time_range = "pour aujourd'hui"
    await ctx.respond('Traitement de la demande en cours... :hourglass_flowing_sand:')
    await send_events(ctx, ctx.channel, today, today, time_range)

@bot.command(name='tomorrow', description="Sends tomorrow's events.")
async def tomorrow_command(ctx):
    await ctx.defer(ephemeral=True)  # Defer the interaction
    tomorrow = arrow.now().shift(days=+1).format('YYYY-MM-DD')
    time_range = "pour demain"
    await ctx.respond('Traitement de la demande en cours... :hourglass_flowing_sand:')
    await send_events(ctx, ctx.channel, tomorrow, tomorrow, time_range)

@bot.command(name='3days', description="Sends the events for the next 3 days.")
async def threedays_command(ctx):
    await ctx.defer(ephemeral=True)  # Defer the interaction
    today = arrow.now().format('YYYY-MM-DD')
    threedays = arrow.now().shift(days=+3).format('YYYY-MM-DD')
    time_range = "pour les 3 prochains jours"
    await ctx.respond('Traitement de la demande en cours... :hourglass_flowing_sand:')
    await send_events(ctx, ctx.channel, today, threedays, time_range)

@bot.command(name='week', description="Sends this week's events.")
async def week_command(ctx):
    await ctx.defer(ephemeral=True)  # Defer the interaction
    today = arrow.now().format('YYYY-MM-DD')
    week = arrow.now().shift(days=+7).format('YYYY-MM-DD')
    time_range = "pour cette semaine"
    await ctx.respond('Traitement de la demande en cours... :hourglass_flowing_sand:')
    await send_events(ctx, ctx.channel, today, week, time_range)

bot.run(discord_token)