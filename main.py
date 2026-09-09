
import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

def convert_mm_digits(text: str) -> str:
    mm_digits = {'၀':'0', '၁':'1', '၂':'2', '၃':'3', '၄':'4', '၅':'5', '၆':'6', '၇':'7', '၈':'8', '၉':'9'}
    for mm, en in mm_digits.items():
        text = text.replace(mm, en)
    return text

def parse_2d_text(text: str):
    text = convert_mm_digits(text)
    lines = text.strip().split('\n')
    results = []
    grand_total = 0

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        if "အပူး" in line_str or "double" in line_str.lower():
            match = re.search(r'(\d+)', line_str)
            if match:
                amount = int(match.group(1))
                subtotal = 10 * amount
                grand_total += subtotal
                results.append(f"• အပူး (10 ကွက်) x {amount} = {subtotal:,} ကျပ်")
                continue

        r_match = re.search(r'(\d{2})\s*[Rr]\s*(\d+)', line_str)
        if r_match:
            num, amount = r_match.group(1), int(r_match.group(2))
            rev_num = num[::-1]
            subtotal = 2 * amount
            grand_total += subtotal
            results.append(f"• {num}, {rev_num} (2 ကွက်) x {amount} = {subtotal:,} ကျပ်")
            continue

        norm_match = re.search(r'(\d{2})[\s\/\-,\.]+(\d+)', line_str)
        if norm_match:
            num, amount = norm_match.group(1), int(norm_match.group(2))
            grand_total += amount
            results.append(f"• {num} x {amount} = {amount:,} ကျပ်")
            continue

    return results, grand_total

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 မင်္ဂလာပါ! Viber မှ Share လိုက်သော 2D စာရင်းများကို ပို့ပေးပါ။")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results, total = parse_2d_text(update.message.text)
    if not results:
        await update.message.reply_text("❌ စာရင်း ပုံစံ မတွေ့ပါ။ ဥပမာ - '25R 500' ဟု ပို့ပေးပါ။")
        return
    reply_msg = "📝 **တွက်ချက်ပြီး စာရင်း**\n\n" + "\n".join(results) + f"\n\n💰 **စုစုပေါင်း = {total:,} ကျပ်**"
    await update.message.reply_text(reply_msg, parse_mode="Markdown")

if __name__ == '__main__':
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
      
