import os
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Apna CURRENT NEW token yahan paste karo
TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 YouTube Downloader Ready!\n\n"
        "🔗 Pehle YouTube video ka link bhejo."
    )

#python -c "import requests; t='8965075110:AAF2BzpBIinAAEibWXNH3hrbwWBEIVkoLYc'; r=requests.get(f'https://api.telegram.org/bot{t}/getMe',timeout=10); print(r.text)"
# =========================
# RECEIVE YOUTUBE LINK
# =========================

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = update.message.text.strip()

    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text(
            "❌ Please valid YouTube link bhejo."
        )
        return

    # URL save karna
    context.user_data["youtube_url"] = url

    keyboard = [
        [
            InlineKeyboardButton("360p", callback_data="360"),
            InlineKeyboardButton("480p", callback_data="480"),
        ],
        [
            InlineKeyboardButton("720p", callback_data="720"),
            InlineKeyboardButton("1080p", callback_data="1080"),
        ],
        [
            InlineKeyboardButton(
                "Best Available",
                callback_data="best"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎬 Quality select karo:",
        reply_markup=reply_markup
    )


# =========================
# QUALITY SELECTED
# =========================

async def quality_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    quality = query.data

    # Saved URL
    url = context.user_data.get("youtube_url")

    if not url:
        await query.edit_message_text(
            "❌ YouTube link nahi mila.\n"
            "Please dobara link bhejo."
        )
        return

    await query.edit_message_text(
        f"✅ {quality} selected!\n\n"
        f"⏳ Downloading... Please wait."
    )

    # =========================
    # QUALITY FORMAT
    # =========================

    if quality == "best":
        format_code = "bestvideo+bestaudio/best"

    else:
        format_code = (
            f"bestvideo[height<={quality}]"
            f"+bestaudio/best[height<={quality}]"
        )

    options = {
        "format": format_code,

        "outtmpl": os.path.join(
            DOWNLOAD_DIR,
            "%(title)s.%(ext)s"
        ),

        "merge_output_format": "mp4",

        "noplaylist": True,

        "quiet": False,
    }

    try:

        # =========================
        # DOWNLOAD
        # =========================

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            filename = ydl.prepare_filename(info)

        # FFmpeg merge ke baad MP4
        filename = os.path.splitext(filename)[0] + ".mp4"

        # =========================
        # CHECK FILE
        # =========================

        if not os.path.isfile(filename):

            await query.message.reply_text(
                "❌ Download ho gaya, "
                "lekin MP4 file nahi mili."
            )

            return

        # =========================
        # FILE SIZE
        # =========================

        file_size = os.path.getsize(filename)

        file_size_mb = file_size / (1024 * 1024)

        await query.message.reply_text(
            f"✅ Download complete!\n\n"
            f"🎬 Quality: {quality}\n"
            f"📦 Size: {file_size_mb:.1f} MB\n\n"
            f"📤 Sending video..."
        )

        # =========================
        # SEND VIDEO AS DOCUMENT
        # =========================

        with open(filename, "rb") as video:

            await query.message.reply_document(
                document=video,
                read_timeout=600,
                write_timeout=600,
                connect_timeout=60
            )

        await query.message.reply_text(
            "✅ Video successfully sent!"
        )

        # =========================
        # DELETE FILE
        # =========================

        try:
            os.remove(filename)
        except Exception:
            pass

        # URL clear
        context.user_data.pop(
            "youtube_url",
            None
        )

    except Exception as e:

        print("\n========== ERROR ==========")
        print(e)
        print("===========================\n")

        await query.message.reply_text(
            f"❌ Download/Send failed:\n\n"
            f"{str(e)[:1500]}"
        )


# =========================
# BOT SETUP
# =========================

app = Application.builder().token(TOKEN).build()


# /start
app.add_handler(
    CommandHandler(
        "start",
        start
    )
)


# YouTube link
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        receive_link
    )
)


# Quality button
app.add_handler(
    CallbackQueryHandler(
        quality_selected
    )
)


print("Bot is running...")


app.run_polling()