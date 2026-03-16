import os
import re
import asyncio
import subprocess
import tempfile
import ollama
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, TypeHandler, filters, ContextTypes
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from tools.lobster import lobster_stream
except ImportError:
    lobster_stream = None

import json
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from groq import Groq

# Constants
SESSION_FILE = "/tmp/lobster_sessions.json"
VERSION = "1.0.5-PERSISTENT"

def save_sessions(data):
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Failed to save sessions: {e}")

def load_sessions():
    if not os.path.exists(SESSION_FILE):
        return {}
    try:
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load sessions: {e}")
        return {}

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ALLOWED_USER_ID = os.environ.get("TELEGRAM_ALLOWED_USER_ID")
MINIMAX_MODEL = os.environ.get("MINIMAX_MODEL", "minimax-coding-plan/MiniMax-M2.5")
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

OLLAMA_VISION_MODEL = "qwen3.5:9b"

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Lobster session data: user_id -> dict
SESSION_DATA = {}

async def describe_image_ollama(image_path: str, is_frame: bool = False) -> str:
    """Uses local Ollama Vision model to describe an image."""
    prompt = "Describe this image in detail." if not is_frame else "Describe the key action or context in this single video frame."
    try:
        response = await asyncio.to_thread(
            ollama.generate,
            model=OLLAMA_VISION_MODEL,
            prompt=prompt,
            images=[image_path]
        )
        return response.get('response', 'No description generated.')
    except Exception as e:
        return f"[Vision Error: {str(e)}]"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    if ALLOWED_USER_ID and str(update.effective_user.id) != ALLOWED_USER_ID:
        await update.message.reply_text("Unauthorized user.")
        return
    await update.message.reply_text(
        "🟢 Connected to OpenCode workspace via Minimax.\n"
        "Send me text, images, voice notes, or files to start coding!\n"
        "Use /watch to find movies or TV shows."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text and multi-modal inputs from Telegram, forwarding to OpenCode CLI."""
    user_id = str(update.effective_user.id)
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        await update.message.reply_text("Unauthorized user.")
        return

    # Send initial acknowledgment
    status_msg = await update.message.reply_text("⏳ Received input. Processing media...")

    text_prompt = update.message.text or update.message.caption or ""
    files_downloaded = []

    # Handle Photo Input
    if update.message.photo:
        await status_msg.edit_text(f"👁️ Analyzing image with {OLLAMA_VISION_MODEL}...")
        photo_file = await update.message.photo[-1].get_file()
        file_ext = ".jpg"
        temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext)
        os.close(temp_fd)
        await photo_file.download_to_drive(temp_path)
        
        description = await describe_image_ollama(temp_path)
        text_prompt += f"\n\n[Attached Image Content Analysis]:\n{description}"
        os.remove(temp_path)

    # Handle Video Input
    if update.message.video or update.message.animation:
        await status_msg.edit_text(f"🎞️ Extracting keyframes and analyzing video with {OLLAMA_VISION_MODEL}...")
        video_file = await update.message.video.get_file() if update.message.video else await update.message.animation.get_file()
        
        # Download video to temp
        v_fd, v_path = tempfile.mkstemp(suffix=".mp4")
        os.close(v_fd)
        await video_file.download_to_drive(v_path)
        
        # Extract 3 keyframes evenly spaced
        frames_dir = tempfile.mkdtemp()
        try:
            # ffmpeg command to extract 3 frames using select filter
            subprocess.run([
                "ffmpeg", "-i", v_path, "-vf", "fps=1/2", "-vframes", "3", f"{frames_dir}/frame_%03d.jpg"
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            frame_files = sorted([os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith('.jpg')])
            
            video_description = "\n\n[Attached Video Event Timeline Analysis]:"
            for i, frame_path in enumerate(frame_files):
                desc = await describe_image_ollama(frame_path, is_frame=True)
                video_description += f"\n- Frame {i+1}: {desc}"
            
            text_prompt += video_description
            
        except Exception as e:
            text_prompt += f"\n\n[Video Processing Failed: {str(e)}]"
            
        # Cleanup video files
        import shutil
        os.remove(v_path)
        shutil.rmtree(frames_dir, ignore_errors=True)

    # Handle Document Input
    if update.message.document:
        doc_file = await update.message.document.get_file()
        filename, file_ext = os.path.splitext(update.message.document.file_name)
        temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext, prefix=filename + "_")
        os.close(temp_fd)
        await doc_file.download_to_drive(temp_path)
        files_downloaded.append(temp_path)

    # Handle Voice Notes (Audio)
    if update.message.voice:
        try:
            voice_file = await update.message.voice.get_file()
            temp_fd, temp_path = tempfile.mkstemp(suffix=".ogg")
            os.close(temp_fd)
            await voice_file.download_to_drive(temp_path)
            
            if groq_client:
                await status_msg.edit_text("🎙️ Transcribing voice note via Groq...")
                # Run synchronous API call in a thread pool to avoid blocking the event loop
                def transcribe_audio(path):
                    with open(path, "rb") as file:
                        transcription = groq_client.audio.transcriptions.create(
                          file=(path, file.read()),
                          model="whisper-large-v3",
                          response_format="text",
                        )
                    return transcription

                # Fast transcription using Groq Whisper Large
                transcription_text = await asyncio.to_thread(transcribe_audio, temp_path)
                
                # We append the transcribed text to the prompt, rather than sending the raw audio file
                if text_prompt:
                    text_prompt += f"\n[Voice Note Transcription]: {transcription_text}"
                else:
                    text_prompt = transcription_text

                # Optional: clean up the local audio file since we got the text
                os.remove(temp_path)
            else:
                # If no Groq API key is provided, just pass the audio file to open code
                files_downloaded.append(temp_path)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error processing voice note: {str(e)}")

    if not text_prompt and not files_downloaded:
        await status_msg.edit_text("❌ No actionable input found.")
        return

    # Construct the final prompt to pass to OpenCode CLI
    full_prompt = text_prompt
    if files_downloaded:
        full_prompt += "\n\nAttached files for reference (absolute paths):\n" + "\n".join(files_downloaded)

    await status_msg.edit_text(
        f"🚀 Passing prompt to OpenCode (Model: {MINIMAX_MODEL})...\n"
        f"Please wait while the agent works. This may take a minute."
    )

    # Command line formulation based on opencode --help
    cmd = [
        "opencode",
        "run",
        "-c",
        "--model", MINIMAX_MODEL,
        full_prompt
    ]

    # Execute the agent command
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        # Capture the output from the CLI
        output_data = bytearray()
        while True:
            chunk = await process.stdout.read(4096)
            if not chunk:
                break
            output_data.extend(chunk)

        await process.wait()
        
        output_text = output_data.decode("utf-8", errors="replace")
        # Strip ANSI escape codes from terminal output
        output_text = ANSI_ESCAPE.sub('', output_text).strip()

        if not output_text:
            output_text = "(No output returned from OpenCode)"

        # Sanitize FIRST to remove JSON blocks completely
        output_text = _sanitize_opencode_output(output_text)

        # THEN truncate for Telegram limit
        if len(output_text) > 4000:
            output_text = "...[Truncated]...\n" + output_text[-3900:]

        await update.message.reply_text(output_text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error executing opencode CLI: {str(e)}")


# --- Lobster Streaming Handlers ---

async def watch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"DEBUG: watch_command triggered by {update.effective_user.id}")
    if lobster_stream is None:
        await update.message.reply_text("Lobster stream module not available.")
        return
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Please provide a search query: /watch breaking bad")
        return
    try:
        status_msg = await update.message.reply_text(f"🔍 Searching for '{query}'...")
        results = await asyncio.to_thread(lobster_stream.search, query)
        user_id = str(update.effective_user.id)
        if user_id not in SESSION_DATA: SESSION_DATA[user_id] = {}
        SESSION_DATA[user_id]['media_results'] = results
        save_sessions(SESSION_DATA)
        await handle_search_results(update, context, results, status_msg)
    except Exception:
        logger.exception("Search error")
        await update.message.reply_text("❌ Error during search.")

async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if lobster_stream is None: return
    status_msg = await update.message.reply_text(f"🔥 Fetching trending content...")
    results = await asyncio.to_thread(lobster_stream.get_trending)
    await handle_search_results(update, context, results, status_msg)

async def recent_movies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if lobster_stream is None: return
    status_msg = await update.message.reply_text(f"🆕 Fetching recent movies...")
    results = await asyncio.to_thread(lobster_stream.get_recent, "movie")
    await handle_search_results(update, context, results, status_msg)

async def recent_tv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if lobster_stream is None: return
    status_msg = await update.message.reply_text(f"🆕 Fetching recent TV shows...")
    results = await asyncio.to_thread(lobster_stream.get_recent, "tv")
    await handle_search_results(update, context, results, status_msg)


# --- Web Search Handler ---


def _escape_markdown(text: str) -> str:
    """Escape special Markdown characters for Telegram."""
    if not text:
        return ""
    # Escape Telegram Markdown special characters
    # Order matters: escape backslash first
    special_chars = ['\\', '*', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, '\\' + char)
    return text


def _sanitize_opencode_output(text: str) -> str:
    """Sanitize OpenCode CLI output - strip raw JSON, Unicode escapes, scraped content artifacts."""
    if not text:
        return ""

    import re
    import html

    # 1. Decode Unicode escape sequences
    text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)
    text = text.replace('\u00a0', ' ')
    text = text.replace('\u2022', '-')
    text = text.replace('\u2019', "'")
    text = text.replace('\u2018', "'")
    text = text.replace('\u201c', '"')
    text = text.replace('\u201d', '"')

    # 2. Decode HTML entities
    text = html.unescape(text)

    # 2b. Remove shell prompts and command lines
    # Examples: "> build · MiniMax-M2.5", "$ SEARXNG_BASE_URL=... python3 ..."
    lines = text.split('\n')
    result_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip shell prompts like: "> build · MiniMax-M2.5" or "> build"
        if stripped.startswith('> ') and ('·' in stripped or len(stripped) < 50):
            continue
        # Skip command lines starting with $ or # that look like shell commands
        if stripped.startswith('$ ') or stripped.startswith('# '):
            # Only skip if it looks like a command (contains python, node, npm, etc.)
            if any(cmd in stripped.lower() for cmd in ['python', 'node', 'npm', 'curl', 'pip', 'pip3', 'opencode', 'searxng']):
                continue
        result_lines.append(line)
    text = '\n'.join(result_lines)

    # 3. Extract URLs from JSON before stripping
    urls = re.findall(r'"url":\s*"([^"]+)"', text)
    # Also extract from markdown links [text](url)
    md_urls = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
    urls.extend([u[1] for u in md_urls])  # Get the URL part from markdown
    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen and url.startswith('http'):
            seen.add(url)
            unique_urls.append(url)

    # 4. Remove raw JSON blocks - line by line approach
    lines = text.split('\n')
    result_lines = []
    skip_mode = False
    brace_count = 0

    for line in lines:
        stripped = line.strip()

        # Detect JSON start - any line starting with { or [
        if not skip_mode and (stripped.startswith('{') or stripped.startswith('[')):
            skip_mode = True
            brace_count = stripped.count('{') - stripped.count('}')
            brace_count += stripped.count('[') - stripped.count(']')
            # If this single line is the whole JSON, don't skip
            if brace_count == 0 and stripped.endswith(('}', ']')):
                skip_mode = False
                result_lines.append(line)
            continue

        # Track braces to find end of JSON block
        if skip_mode:
            brace_count += stripped.count('{') - stripped.count('}')
            brace_count += stripped.count('[') - stripped.count(']')
            if brace_count <= 0 and stripped in ['}', ']', '},', '],']:
                skip_mode = False
            continue

        result_lines.append(line)

    text = '\n'.join(result_lines)

    # 4. Strip common scraped page garbage
    garbage = [
        'About Press Copyright Contact us Creators',
        '© 2026 Google LLC',
        'Advertise Developers Terms Privacy Policy & Safety',
        'ZonePlayerLeague',
        'NBA Playoffs Stats Stats Per Game',
        'Career comparison Season by season',
    ]
    for g in garbage:
        text = text.replace(g, '')

    # Remove stat patterns
    text = re.sub(r'RA\d+\.?\d*%', '', text)
    text = re.sub(r'PAINT\d+\.?\d*%', '', text)
    text = re.sub(r'MID\d+\.?\d*%', '', text)
    text = re.sub(r'LC\d+\.?\d*%', '', text)
    text = re.sub(r'RC\d+\.?\d*%', '', text)
    text = re.sub(r'ATB\d+\.?\d*%', '', text)

    # 5. Remove residual HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # 6. Clean up
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 7. Append sources if we found any URLs
    if unique_urls:
        text += "\n\n---\n**Sources:**\n"
        for i, url in enumerate(unique_urls[:5], 1):  # Limit to 5 sources
            text += f"{i}. {url}\n"

    return text.strip()


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /search command - web search with AI synthesis."""
    user_id = str(update.effective_user.id)
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        await update.message.reply_text("Unauthorized user.")
        return

    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Please provide a search query: /search python tutorials")
        return

    # Basic input sanitization - strip control characters
    query = "".join(c for c in query if ord(c) >= 32 or c in "\n\t")

    # Determine path to web/agent.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    web_agent_path = os.path.join(script_dir, "web", "agent.py")

    if not os.path.exists(web_agent_path):
        await update.message.reply_text("Web agent script not found.")
        return

    status_msg = await update.message.reply_text(f"🔍 Searching for: {query}...")

    try:
        # Run web/agent.py with synthesis enabled
        cmd = [
            sys.executable,
            web_agent_path,
            query,
            "-n", "5",
            "-v", "3",
            "-s",  # Enable synthesis
            "-f", "json"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            await status_msg.edit_text(f"❌ Search failed: {stderr.decode('utf-8', errors='replace')}")
            return

        # Parse JSON output
        try:
            result = json.loads(stdout.decode("utf-8"))
        except json.JSONDecodeError:
            await status_msg.edit_text("❌ Failed to parse search results.")
            return

        # Format output for Telegram
        if result.get("summary"):
            response = f"🔍 *Search: {query}*\n\n"
            response += f"_Source: {result.get('search_provider', 'unknown')}_\n\n"
            response += f"📝 *Summary:*\n{_escape_markdown(result['summary'])}\n\n"
            response += f"📄 *Top Results:*\n"
            for i, r in enumerate(result.get("search_results", [])[:3], 1):
                response += f"{i}. [{_escape_markdown(r['title'])}]({r['url']})\n"
        else:
            response = f"🔍 *Results for: {query}*\n\n"
            for i, r in enumerate(result.get("search_results", [])[:5], 1):
                response += f"{i}. *{_escape_markdown(r['title'])}*\n{r['url']}\n"
                if r.get('snippet'):
                    response += f"_{_escape_markdown(r['snippet'][:100])}..._\n"
                response += "\n"

        # Telegram message length limit
        if len(response) > 4000:
            response = response[:3900] + "...\n_(truncated)_"

        await status_msg.edit_text(response, parse_mode='Markdown', disable_web_page_preview=True)

    except Exception as e:
        logger.exception("Search error")
        await status_msg.edit_text(f"❌ Search error: {str(e)}")


# --- End Web Search Handler ---

async def handle_search_results(update, context, results, status_msg):
    if not results:
        await status_msg.edit_text("❌ No results found.")
        return
    keyboard = []
    for i, res in enumerate(results[:20]):
        keyboard.append([InlineKeyboardButton(f"{res['title']} ({res['media_type'].upper()})", callback_data=f"media_{i}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await status_msg.edit_text("🎬 Select a title:", reply_markup=reply_markup)

async def debug_update_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"RAW UPDATE: {update.to_dict() if hasattr(update, 'to_dict') else str(update)}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = str(update.effective_user.id)
    print(f"DEBUG: button_handler triggered user={user_id} data={data}")
    await query.answer()

    # Refresh sessions from disk to handle multi-process/restarts
    global SESSION_DATA
    SESSION_DATA = load_sessions()
    
    if user_id not in SESSION_DATA:
        SESSION_DATA[user_id] = {}
    session = SESSION_DATA[user_id]

    try:
        if data.startswith("media_"):
            idx = int(data.split("_")[1])
            results = session.get('media_results', [])
            logger.info(f"Media selection: user={user_id}, idx={idx}, results_count={len(results)}")
            if not results or idx >= len(results):
                await query.edit_message_text("❌ Results lost or session expired. Please search again.")
                return
            media = results[idx]
            session['selected_media'] = media
            save_sessions(SESSION_DATA)
            
            if media['media_type'] == 'movie':
                await query.edit_message_text(f"⏳ Extracting stream for '{media['title']}'...")
                stream = await asyncio.to_thread(lobster_stream.get_stream_url, media['media_id'], 'movie')
                if stream and stream.get('video_url'):
                    await query.edit_message_text(f"🎬 **{media['title']}**\n\n[Tap to Watch 🍿]({stream['video_url']})", parse_mode='Markdown', disable_web_page_preview=True)
                else:
                    await query.edit_message_text("❌ Failed to extract stream.")
            else:
                await query.edit_message_text(f"⏳ Fetching seasons for '{media['title']}'...")
                seasons = await asyncio.to_thread(lobster_stream.get_seasons, media['media_id'])
                if not seasons:
                    await query.edit_message_text(f"❌ No seasons found for '{media['title']}'.")
                    return
                session['seasons'] = seasons
                save_sessions(SESSION_DATA)
                keyboard = []
                for i, s in enumerate(seasons):
                    keyboard.append([InlineKeyboardButton(s['name'], callback_data=f"season_{i}")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(f"📺 **{media['title']}** - Select Season:", reply_markup=reply_markup, parse_mode='Markdown')

        elif data.startswith("season_"):
            idx = int(data.split("_")[1])
            seasons = session.get('seasons', [])
            logger.info(f"Season selection: user={user_id}, idx={idx}, seasons_count={len(seasons)}")
            if not seasons or idx >= len(seasons):
                await query.edit_message_text("❌ Season list lost. Please search again.")
                return
            season = seasons[idx]
            session['selected_season'] = season
            media = session.get('selected_media', {})
            save_sessions(SESSION_DATA)
            
            await query.edit_message_text(f"⏳ Fetching episodes for {season['name']}...")
            episodes = await asyncio.to_thread(lobster_stream.get_episodes, season['season_id'])
            if not episodes:
                await query.edit_message_text(f"❌ No episodes found for {season['name']}.")
                return
            session['episodes'] = episodes
            save_sessions(SESSION_DATA)
            
            keyboard = []
            row = []
            for i, ep in enumerate(episodes):
                row.append(InlineKeyboardButton(ep['title'], callback_data=f"ep_{i}"))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
                
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"📺 **{media.get('title', '')}** - {season['name']}\nSelect Episode:", reply_markup=reply_markup, parse_mode='Markdown')

        elif data.startswith("ep_"):
            idx = int(data.split("_")[1])
            episodes = session.get('episodes', [])
            logger.info(f"Episode selection: user={user_id}, idx={idx}, episodes_count={len(episodes)}")
            if not episodes or idx >= len(episodes):
                await query.edit_message_text("❌ Episode list lost. Please search again.")
                return
            episode = episodes[idx]
            media = session.get('selected_media', {})
            season = session.get('selected_season', {})
            
            await query.edit_message_text(f"⏳ Extracting stream for '{episode['title']}'...")
            stream = await asyncio.to_thread(lobster_stream.get_stream_url, media['media_id'], 'tv', data_id=episode['data_id'])
            if stream and stream.get('video_url'):
                txt = f"🎬 **{media.get('title','')}** - {season.get('name','')} - {episode['title']}"
                await query.edit_message_text(f"{txt}\n\n[Tap to Watch 🍿]({stream['video_url']})", parse_mode='Markdown', disable_web_page_preview=True)
            else:
                await query.edit_message_text("❌ Failed to extract stream.")
    except Exception:
        logger.exception("Button error")
        await query.edit_message_text("❌ Interaction error occurred.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"DEBUG: error_handler triggered: {context.error}")
    logger.exception("Exception while handling an update:")

# --- End Lobster Streaming Handlers ---

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN is missing. Please set it in your .env or export it.")
        return

    # Initialize Bot application
    application = Application.builder().token(token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("watch", watch_command))
    application.add_handler(CommandHandler("trending", trending_command))
    application.add_handler(CommandHandler("recent_movies", recent_movies_command))
    application.add_handler(CommandHandler("recent_tv", recent_tv_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(TypeHandler(Update, debug_update_logger), group=-1)
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(error_handler)
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("✅ Starting Telegram-OpenCode Bridge for persistent code sessions...")
    print(f"✅ Utilizing Text Model: {MINIMAX_MODEL}")
    print(f"✅ Utilizing Vision Model: {OLLAMA_VISION_MODEL}")
    
    # Run the bot daemon (drop_pending_updates clears stale Telegram polling conflicts)
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
