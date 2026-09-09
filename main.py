
import os
import re
import io
from flask import Flask
from threading import Thread
from PIL import Image
import pytesseract
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Flask App for Keeping Render Web Service Alive
web_app = Flask('')

@web_app.route('/')
def home():
    return "2D Telegram Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# မြန်မာဂဏန်းများကို အင်္ဂလိပ်ဂဏန်းသို့ ပြောင်းပေးသည့် Function
def convert_mm_digits(text: str) -> str:
    mm_digits = {'၀':'0', '၁':'1', '၂':'2', '၃':'3', '၄':'4', '၅':'5', '၆':'6', '၇':'7', '၈':'8', '၉':'9'}
    for mm, en in mm_digits.items():
        text = text.replace(mm, en)
    return text

# 2D စာရင်း စစ်ဆေးတွက်ချက်သည့် Function
def parse_2d_text(text: str):
    text = convert_mm_digits(text)
    lines = text.strip().split('\n')
    results = []
    grand_total = 0

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        # ၁။ အပူး စာရင်း စစ်ဆေးခြင်း
        if "အပူး" in line_str or "double" in line_str.lower():
            match = re.search(r'(\d+)', line_str)
            if match:
                amount = int(match.group(1))
                subtotal = 10 * amount
                grand_total += subtotal
                results.append(f"• အပူး (10 ကွက်) x {amount} = {subtotal:,} ကျပ်")
                continue

        # ၂။ R (အကွက်လှည့်) ပါမပါ စစ်ဆေးခြင်း
        r_amount = 0
        r_match = re.search(r'[Rr]\s*(\d+)', line_str)
        if r_match:
            r_amount = int(r_match.group(1))
            clean_line = re.sub(r'[Rr]\s*\d+', '', line_str)
        else:
            clean_line = line_str

        # သင်္ကေတပေါင်းစုံ (*, ., /, -, space) များကို space အဖြစ် ပြောင်းလဲခြင်း
        normalized = re.sub(r'[\*\.\/\-\s]+', ' ', clean_line).strip()
        tokens = normalized.split()

        nums = []
        amounts = []

        for item in tokens:
            if item.isdigit():
                if len(item) == 2:
                    nums.append(item)
                else:
                    amounts.append(int(item))

        if nums and amounts:
            base_amount = amounts[0]
            
            direct_subtotal = len(nums) * base_amount
            grand_total += direct_subtotal
            num_str = ", ".join(nums)
            results.append(f"• {num_str} ({len(nums)} ကွက်) x {base_amount} = {direct_subtotal:,} ကျပ်")

            if r_amount > 0:
                rev_nums = [n[::-1] for n in nums]
                rev_subtotal = len(rev_nums) * r_amount
                grand_total += rev_subtotal
                rev_str = ", ".join(rev_nums)
                results.append(f"  └ R: {rev_str} ({len(rev_nums)} ကွက်) x {r_amount} = {rev_subtotal:,} ကျပ်")

    return results, grand_total

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 မင်္ဂလာပါ! 2D စာရင်းများ သို့မဟုတ် ဓါတ်ပုံများကို ပို့ပေးပါ။")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = ""

    if update.message.photo:
        if update.message.caption:
            user_text = update.message.caption
        else:
            try:
                photo_file = await update.message.photo[-1].get_file()
                photo_bytes = await photo_file.download_as_bytearray()
                image = Image.open(io.BytesIO(photo_bytes))
                user_text = pytesseract.image_to_string(image)
            except Exception:
                user_text = ""
    else:
        user_text = update.message.text

    if not user_text:
        await update.message.reply_text("❌ စာရင်း စာသား မတွေ့ပါ။ ဓါတ်ပုံနှင့်အတူ စာရင်း (Caption) တွဲရေးပေးပါ။")
        return

    results, total = parse_2d_text(user_text)
    if not results:
        await update.message.reply_text("❌ စာရင်း ပုံစံ မတွေ့ပါ။ ဥပမာ - '01*03*05.07.09.3000.R2000' ဟု ပို့ပေးပါ။")
        return

    reply_msg = "📝 **တွက်ချက်ပြီး စာရင်း**\n\n" + "\n".join(results) + f"\n\n💰 **စုစုပေါင်း = {total:,} ကျပ်**"
    await update.message.reply_text(reply_msg, parse_mode="Markdown")

if __name__ == '__main__':
    # Start Web Server Thread
    server_thread = Thread(target=run_flask)
    server_thread.start()

    # Start Telegram Bot
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_message))
    app.run_polling()
