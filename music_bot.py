# ---------------------------------------
# Thunderz Portable + Cloud Music Bot
# ---------------------------------------

# ✅ Fix module paths (USB mode)
import os, sys
HERE = os.path.dirname(__file__)
sys.path[:0] = [
    os.path.join(HERE, "site-packages2"),
    os.path.join(HERE, "site-packages"),
]

# ✅ Load environment
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

# ✅ Imports
import platform, struct, discord, shutil
from discord import app_commands
from discord.ext import commands

# ✅ FFmpeg auto
FFMPEG_PATH = os.environ.get("FFMPEG_BINARY") or shutil.which("ffmpeg") or "ffmpeg"

# ✅ Bot settings
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ Opus loader (USB friendly)
import discord.opus as _opus
# Replit/Linux first: libopus shared library
try:
    _opus.load_opus("libopus.so.0")
except Exception:
    pass

def load_opus():
    dirs = [
        os.path.join(HERE, "bin"),
        HERE,
        r"E:\discord-bot\bin",
        r"E:\discord-bot",
        r"E:\python-embed",
    ]
    for d in dirs:
        if hasattr(os, "add_dll_directory") and os.path.isdir(d):
            try: os.add_dll_directory(d)
            except: pass

    candidates = [
        os.path.join(HERE, "bin", "opus.dll"),
        os.path.join(HERE, "opus.dll"),
        r"E:\discord-bot\bin\opus.dll",
        r"E:\discord-bot\opus.dll",
        r"E:\python-embed\opus.dll",
    ]
    for c in candidates:
        try:
            _opus.load_opus(c)
            if _opus.is_loaded():
                print(f"✅ Loaded opus: {c}")
                return True
        except: pass

    try:
        _opus.load_opus("opus")
        if _opus.is_loaded():
            print("✅ Opus loaded by name")
            return True
    except Exception as e:
        print("❌ Opus error:", e)

    print("❌ Opus not loaded!")
    return False

OPUS_OK = _opus.is_loaded() or load_opus()
print("Python:", platform.architecture(), "| Ptr:", struct.calcsize("P") * 8)
print("FFmpeg:", FFMPEG_PATH)

# ✅ yt-dlp import
YoutubeDL = None
try:
    import yt_dlp as _ytdlp
    if hasattr(_ytdlp, "YoutubeDL"):
        YoutubeDL = _ytdlp.YoutubeDL
        print("✅ yt-dlp loaded from:", _ytdlp.__file__)
    else:
        print("⚠️ yt-dlp present but no YoutubeDL class")
except Exception as e:
    print("⚠️ Failed to import yt-dlp:", e)

# ---------------------------------------
# Helper functions
# ---------------------------------------
async def ensure_vc(inter):
    m = inter.user if isinstance(inter.user, discord.Member) else None
    if not m or not m.voice or not m.voice.channel: return None
    ch = m.voice.channel
    vc = inter.guild.voice_client
    if vc and vc.channel != ch: await vc.move_to(ch)
    elif not vc: vc = await ch.connect()
    return vc

async def extract_stream(q):
    title = q
    if YoutubeDL is None: return q, title
    opts = {"format": "bestaudio/best", "quiet": True, "noplaylist": True, "default_search": "ytsearch1"}
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(q if "://" in q else f"ytsearch1:{q}", download=False)
            if "entries" in info: info = info["entries"][0]
            return info.get("url") or q, info.get("title") or title
    except Exception as e:
        print("yt-dlp error:", e)
        return q, title

def play(vc, url, vol=1):
    from discord import FFmpegPCMAudio, PCMVolumeTransformer
    base = FFmpegPCMAudio(url, executable=FFMPEG_PATH,
                          before_options="-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                          options="-vn -loglevel error")
    vc.play(PCMVolumeTransformer(base, volume=vol))

# ---------------------------------------
# Events
# ---------------------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        if GUILD_ID:
            g = discord.Object(int(GUILD_ID))
            bot.tree.copy_global_to(guild=g)
            synced = await bot.tree.sync(guild=g)
            print(f"✅ Synced {len(synced)} cmds → guild {GUILD_ID}")
        else:
            await bot.tree.sync()
    except Exception as e:
        print("Sync error:", e)
    await bot.change_presence(activity=discord.Game("/play"))

# ---------------------------------------
# Slash Commands
# ---------------------------------------
@bot.tree.command(description="Join your voice channel")
async def join(inter):
    await inter.response.defer(ephemeral=True)
    vc = await ensure_vc(inter)
    await inter.followup.send("✅ Joined voice!" if vc else "❌ Join a VC first")

@bot.tree.command(description="Play music")
@app_commands.describe(query="YouTube link or search text")
async def playcmd(inter, query: str):
    await inter.response.defer(ephemeral=True)
    if not OPUS_OK: return await inter.followup.send("❌ Opus missing")
    vc = await ensure_vc(inter)
    if not vc: return await inter.followup.send("❌ Join VC first")
    url, title = await extract_stream(query)
    if vc.is_playing(): vc.stop()
    play(vc, url, 1.0)
    await inter.followup.send(f"🎶 Playing **{title}**")

@bot.tree.command(description="Test tone")
async def tone(inter):
    await inter.response.defer(ephemeral=True)
    vc = await ensure_vc(inter)
    if not vc: return await inter.followup.send("❌ Join VC first")

    from discord import FFmpegPCMAudio, PCMVolumeTransformer
    tone = "-f lavfi -i sine=frequency=440:duration=3"
    vc.play(PCMVolumeTransformer(FFmpegPCMAudio(tone, executable=FFMPEG_PATH), volume=1.2))
    await inter.followup.send("🔔 Test tone playing")

@bot.tree.command(description="Pause")
async def pause(inter):
    await inter.response.defer(ephemeral=True)
    vc = inter.guild.voice_client
    vc.pause() if vc and vc.is_playing() else None
    await inter.followup.send("⏸️ Paused")

@bot.tree.command(description="Resume")
async def resume(inter):
    await inter.response.defer(ephemeral=True)
    vc = inter.guild.voice_client
    vc.resume() if vc and vc.is_paused() else None
    await inter.followup.send("▶️ Resumed")

@bot.tree.command(description="Stop")
async def stop(inter):
    await inter.response.defer(ephemeral=True)
    vc = inter.guild.voice_client
    vc.stop() if vc else None
    await inter.followup.send("⛔ Stopped")

@bot.tree.command(description="Leave")
async def leave(inter):
    await inter.response.defer(ephemeral=True)
    vc = inter.guild.voice_client
    await vc.disconnect() if vc else None
    await inter.followup.send("👋 Left VC")

@bot.tree.command(description="Set volume 1-200%")
async def volume(inter, percent: app_commands.Range[int, 1, 200]):
    await inter.response.defer(ephemeral=True)
    vc = inter.guild.voice_client
    if vc and vc.source and hasattr(vc.source, "volume"):
        vc.source.volume = percent/100
        return await inter.followup.send(f"🔊 Volume {percent}%")
    await inter.followup.send("❌ Nothing playing")

# ---------------------------------------
# Run bot
# ---------------------------------------
if not TOKEN: raise RuntimeError("No DISCORD_TOKEN in .env")
bot.run(TOKEN)

