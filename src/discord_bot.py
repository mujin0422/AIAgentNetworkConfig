"""
discord_bot.py — Discord Bot điều khiển Network AI Assistant từ xa
Chạy: python -m src.discord_bot

Yêu cầu: pip install discord.py python-dotenv
"""

import os
import sys
import asyncio
import logging
from discord.ui import View, Button

# Đảm bảo project root trong PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
import discord
from discord.ext import commands

from src.main import process_query_async, initializeSystem

# Load biến môi trường
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
DISCORD_PREFIX = os.getenv("DISCORD_PREFIX", "!net")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

pending_sessions = {}

# --- Cấu hình Intents ---
intents = discord.Intents.default()
intents.message_content = True

# Tăng heartbeat timeout để tránh warning khi LLM chạy lâu
bot = commands.Bot(
    command_prefix=DISCORD_PREFIX + " ",
    intents=intents,
    heartbeat_timeout=150.0  # Tăng lên 150 giây
)


@bot.event
async def on_ready():
    """Khi bot đã kết nối Discord thành công"""
    logger.info(f"Bot đã đăng nhập với tên: {bot.user}")
    logger.info(f"Prefix lệnh: '{DISCORD_PREFIX}'")

    # Khởi tạo hệ thống AI Agent (blocking → chạy trong thread)
    logger.info("Đang khởi tạo Network AI Agent...")
    success = await asyncio.to_thread(initializeSystem)

    if success:
        logger.info("[OK] Network AI Agent đã sẵn sàng!")
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="mạng GNS3 | !net <lệnh>"
            )
        )
    else:
        logger.error("[FAIL] Khởi tạo Agent thất bại. Kiểm tra GNS3 và config.")
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="LỖI KHỞI TẠO — kiểm tra log"
            ),
            status=discord.Status.dnd
        )


@bot.event
async def on_message(message: discord.Message):
    """Xử lý tin nhắn trực tiếp (không cần prefix nếu trong channel đúng)"""
    if message.author == bot.user:
        return

    if message.content.startswith(DISCORD_PREFIX + " "):
        await bot.process_commands(message)
        return

    if DISCORD_CHANNEL_ID:
        try:
            target_channel_id = int(DISCORD_CHANNEL_ID)
            if message.channel.id == target_channel_id:
                await handle_network_query(message, message.content)
                return
        except ValueError:
            pass

    await bot.process_commands(message)


class ApprovalView(View):
    def __init__(self, interrupt_msg: str, user_id: int, thread_id: str, timeout=120):
        super().__init__(timeout=timeout)
        self.interrupt_msg = interrupt_msg
        self.user_id = user_id
        self.thread_id = thread_id
        self.response = None

    @discord.ui.button(label="✅ ĐỒNG Ý", style=discord.ButtonStyle.success, emoji="✅")
    async def approve(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Bạn không phải người yêu cầu!", ephemeral=True)
            return
        self.response = "yes"
        self.stop()
        pending_sessions[self.thread_id] = "yes"
        await interaction.response.send_message(
            "✅ **Đã đồng ý!** Đang thực thi lệnh cấu hình...",
            ephemeral=True
        )

    @discord.ui.button(label="❌ TỪ CHỐI", style=discord.ButtonStyle.danger, emoji="❌")
    async def deny(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Bạn không phải người yêu cầu!", ephemeral=True)
            return
        self.response = "no"
        self.stop()
        pending_sessions[self.thread_id] = "no"
        await interaction.response.send_message(
            "❌ **Đã từ chối!** Hủy lệnh cấu hình.",
            ephemeral=True
        )


async def handle_network_query(message: discord.Message, query: str):
    """Xử lý truy vấn mạng từ Discord"""
    thread_id = f"discord_{message.author.id}_{message.channel.id}"

    processing_msg = await message.reply("🔄 **Đang xử lý yêu cầu...**")

    async def on_interrupt(interrupt_msg: str):
        """Callback khi cần xác nhận từ user"""
        pending_sessions.pop(thread_id, None)
        view = ApprovalView(interrupt_msg, message.author.id, thread_id)
        confirm_msg = await message.reply(
            f"⚠️ **CẢNH BÁO BẢO MẬT**\n```\n{interrupt_msg}\n```\nBạn có đồng ý thực thi không?",
            view=view
        )
        try:
            await view.wait()
            result = pending_sessions.pop(thread_id, "no")
            await confirm_msg.delete()
            return result
        except Exception:
            pending_sessions.pop(thread_id, None)
            await confirm_msg.delete()
            return "no"

    try:
        result = await process_query_async(
            query=query,
            thread_id=thread_id,
            on_interrupt=on_interrupt
        )

        await processing_msg.delete()

        if len(result) > 1900:
            for i in range(0, len(result), 1900):
                await message.reply(result[i:i+1900])
        else:
            await message.reply(result)

    except Exception as e:
        await processing_msg.delete()
        await message.reply(f"❌ **Lỗi:** {str(e)}")


@bot.command(name="net")
async def net_command(ctx: commands.Context, *, query: str):
    """Lệnh: !net <câu hỏi>"""
    await handle_network_query(ctx.message, query)


@bot.command(name="status")
async def status_command(ctx: commands.Context):
    """Lệnh: !net status — Kiểm tra trạng thái hệ thống"""
    from src.core_engine import get_device_info
    device = get_device_info()
    status_msg = (
        "**Bot đang hoạt động**\n"
        f"• Thiết bị: `{device.hostname if device else 'Chưa cấu hình'}`\n"
        f"• Loại: `{device.device_type if device else 'N/A'}`\n"
        f"• Prefix: `{DISCORD_PREFIX}`\n"
        f"• Channel ID: `{DISCORD_CHANNEL_ID or 'Bất kỳ'}`"
    )
    await ctx.reply(status_msg)


def main():
    if not DISCORD_TOKEN:
        logger.error("Thiếu DISCORD_BOT_TOKEN! Hãy tạo file .env và thêm token.")
        print("\nLỗi: Không tìm thấy DISCORD_BOT_TOKEN trong .env")
        sys.exit(1)

    logger.info("Khởi động Discord Bot...")
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
