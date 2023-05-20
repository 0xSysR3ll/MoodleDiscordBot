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
    if current_date.weekday() == 5:
        await send_week_events(None, channel)
    elif current_date.weekday() != 0 and current_date.hour == 8:
        await send_today_events(None, channel)
        
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    print(f"Updating calendar...")
    download_calendar(calendar_url)
    print("Syncing commands...")
    await bot.sync_commands()
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

async def send_today_events(ctx, channel):
    today = arrow.now().format('YYYY-MM-DD')
    events = parse_calendar(today, today)
    # Get all unique words in event names
    event_name_words = set(word for event in events for word in event.name.split())

    # Check for "DISTANCIEL" and "PRESENTIEL" in event names
    event_mode = []
    if "DISTANCIEL" in event_name_words:
        event_mode.append("DISTANCIEL")
    if "PRESENTIEL" in event_name_words:
        event_mode.append("PRESENTIEL")
    if len(events) == 0:
        message = "Bonjour ! Il n'y a pas de cours de prévu aujourd'hui ! 📅"
        if ctx is not None:
            await ctx.defer(invisible=True)
            await ctx.respond(message)
        else:
            await channel.send(message)
    else:
        # Group events by day
        events_by_day = defaultdict(list)
        for event in events:
            events_by_day[event.begin.format('YYYY-MM-DD')].append(event)
        # Create the embed title
        embed_title = "📅 Agenda d'aujourd'hui"
        if event_mode:
            embed_title += f" ({', '.join(event_mode)})"

        # Create an embed
        embed = discord.Embed(title=embed_title, color=discord.Color.orange())

        # Add a field for each day
        for day, events in sorted(events_by_day.items(), key=lambda item: arrow.get(item[0], 'YYYY-MM-DD')):
            events_str = ""
            for event in sorted(events, key=lambda e: e.begin):
                if "DISTANCIEL" in event.name or "PRESENTIEL" in event.name:
                    continue
                description = f"Description: {event.description}\n" if event.description else ""
                lieu = f"Lieu: {event.location}\n" if event.location else ""
                events_str += f"\n**{event.name}**\nDe {event.begin.format('HH:mm')} à {event.end.format('HH:mm')}\n{description}{lieu}"
            embed.add_field(name=f"{arrow.get(day, 'YYYY-MM-DD').format('dddd D MMMM YYYY', locale='fr').capitalize()}", value=events_str, inline=True)
        
        if ctx is not None:
            await ctx.defer(invisible=True)
            await ctx.respond(embed=embed)
        else:
            await channel.send(embed=embed)

@bot.command(name='today', description="Sends today's events.")
async def today_command(ctx):
    await send_today_events(ctx, ctx.channel)

@bot.command(name='tomorrow', description="Sends tomorrow's events.")
async def tomorrow_command(ctx):
    tomorrow = arrow.now().shift(days=+1).format('YYYY-MM-DD')
    events = parse_calendar(tomorrow, tomorrow)
    # Get all unique words in event names
    event_name_words = set(word for event in events for word in event.name.split())

    # Check for "DISTANCIEL" and "PRESENTIEL" in event names
    event_mode = []
    if "DISTANCIEL" in event_name_words:
        event_mode.append("DISTANCIEL")
    if "PRESENTIEL" in event_name_words:
        event_mode.append("PRESENTIEL")
    if len(events) == 0:
        await ctx.defer(invisible=True)
        await ctx.respond("Bonjour ! Il n'y a pas de cours de prévu demain ! 📅")
    else:
        # Group events by day
        events_by_day = defaultdict(list)
        for event in events:
            events_by_day[event.begin.format('YYYY-MM-DD')].append(event)
        # Create the embed title
        embed_title = "📅 Agenda pour demain"
        if event_mode:
            embed_title += f" ({', '.join(event_mode)})"

        # Create an embed
        embed = discord.Embed(title=embed_title, color=discord.Color.orange())

        # Add a field for each day
        for day, events in sorted(events_by_day.items(), key=lambda item: arrow.get(item[0], 'YYYY-MM-DD')):
            events_str = ""
            for event in sorted(events, key=lambda e: e.begin):
                if "DISTANCIEL" in event.name or "PRESENTIEL" in event.name:
                    continue
                description = f"Description: {event.description}\n" if event.description else ""
                lieu = f"Lieu: {event.location}\n" if event.location else ""
                events_str += f"\n**{event.name}**\nDe {event.begin.format('HH:mm')} à {event.end.format('HH:mm')}\n{description}{lieu}"
            embed.add_field(name=f"{arrow.get(day, 'YYYY-MM-DD').format('dddd D MMMM YYYY', locale='fr').capitalize()}", value=events_str, inline=True)
        
        await ctx.defer(invisible=True)
        await ctx.respond(embed=embed)


@bot.command(name='week', description="Sends this week's events.")
async def week_command(ctx):
    await send_week_events(ctx, ctx.channel)

# Refactor the logic into a separate function
async def send_week_events(ctx, channel):
    today = arrow.now().format('YYYY-MM-DD')
    week = arrow.now().shift(days=+7).format('YYYY-MM-DD')
    events = parse_calendar(today, week)
    # Get all unique words in event names
    event_name_words = set(word for event in events for word in event.name.split())

    # Check for "DISTANCIEL" and "PRESENTIEL" in event names
    event_mode = []
    if "DISTANCIEL" in event_name_words:
        event_mode.append("DISTANCIEL")
    if "PRESENTIEL" in event_name_words:
        event_mode.append("PRESENTIEL")
    if len(events) == 0:
        message = "Bonjour ! Il n'y a pas de cours de prévu cette semaine ! 📅"
        if ctx is not None:
            await ctx.defer(invisible=True)
            await ctx.respond(message)
        else:
            await channel.send(message)
    else:
        # Group events by day
        events_by_day = defaultdict(list)
        for event in events:
            events_by_day[event.begin.format('YYYY-MM-DD')].append(event)
        # Create the embed title
        embed_title = "📅 Agenda de la semaine"
        if event_mode:
            embed_title += f" ({', '.join(event_mode)})"

        # Create an embed
        embed = discord.Embed(title=embed_title, color=discord.Color.orange())

        # Add a field for each day
        for day, events in sorted(events_by_day.items(), key=lambda item: arrow.get(item[0], 'YYYY-MM-DD')):
            events_str = ""
            for event in events:
                if "DISTANCIEL" in event.name or "PRESENTIEL" in event.name:
                    continue
                description = f"Description: {event.description}\n" if event.description else ""
                lieu = f"Lieu: {event.location}\n" if event.location else ""
                events_str += f"\n**{event.name}**\nDe {event.begin.format('HH:mm')} à {event.end.format('HH:mm')}\n{description}{lieu}"
            embed.add_field(name=f"{arrow.get(day, 'YYYY-MM-DD').format('dddd D MMMM YYYY', locale='fr').capitalize()}", value=events_str, inline=True)

        if ctx is not None:
            await ctx.defer(invisible=True)
            await ctx.respond(embed=embed)
        else:
            await channel.send(embed=embed)


@bot.command(name='3days', description="Sends the events for the next 3 days.")
async def threedays_command(ctx):
    today = arrow.now().format('YYYY-MM-DD')
    threedays = arrow.now().shift(days=+3).format('YYYY-MM-DD')
    events = parse_calendar(today, threedays)
    # Get all unique words in event names
    event_name_words = set(word for event in events for word in event.name.split())

    # Check for "DISTANCIEL" and "PRESENTIEL" in event names
    event_mode = []
    if "DISTANCIEL" in event_name_words:
        event_mode.append("DISTANCIEL")
    if "PRESENTIEL" in event_name_words:
        event_mode.append("PRESENTIEL")
    if len(events) == 0:
        await ctx.defer(invisible=True)
        await ctx.respond(f"Bonjour ! Il n'y a pas de cours de prévu les 3 prochains jours ! 📅")
    else:
        # Group events by day
        events_by_day = defaultdict(list)
        for event in events:
            events_by_day[event.begin.format('YYYY-MM-DD')].append(event)
        # Create the embed title
        embed_title = "📅 Agenda pour les 3 prochains jours"
        if event_mode:
            embed_title += f" ({', '.join(event_mode)})"

        # Create an embed
        embed = discord.Embed(title=embed_title, color=discord.Color.orange())

        # Add a field for each day
        for day, events in sorted(events_by_day.items(), key=lambda item: arrow.get(item[0], 'YYYY-MM-DD')):
            events_str = ""
            for event in sorted(events, key=lambda e: e.begin):
                if "DISTANCIEL" in event.name or "PRESENTIEL" in event.name:
                    continue
                description = f"Description: {event.description}\n" if event.description else ""
                lieu = f"Lieu: {event.location}\n" if event.location else ""
                events_str += f"\n**{event.name}**\nDe {event.begin.format('HH:mm')} à {event.end.format('HH:mm')}\n{description}{lieu}"
            embed.add_field(name=f"{arrow.get(day, 'YYYY-MM-DD').format('dddd D MMMM YYYY', locale='fr').capitalize()}", value=events_str, inline=True)

        await ctx.defer(invisible=True)
        await ctx.respond(embed=embed)

bot.run(discord_token)