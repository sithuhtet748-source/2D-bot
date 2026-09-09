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
    await update.message.reply_text("👋 မင်္ဂလာပါ! Viber မှ Share လိုက်သော 2D စာရင်း သို့မဟုတ် ဓါတ်ပုံများကို ပို့ပေးပါ။")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = ""

    if update.message.photo:
        # Caption ပါရင် Caption ကို ဦးစားပေးယူခြင်း
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
    import os
import re
import io
from flask import Flask
from threading import Thread
from PIL import Image
import easyocr
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# EasyOCR Reader setup (English only for numbers and standard separators)
reader = easyocr.Reader(['en'], gpu=False)

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
    await update.message.reply_text("👋 မင်္ဂလာပါ! Viber မှ Share လိုက်သော 2D စာရင်း သို့မဟုတ် လက်ရေးစာရွက် ဓါတ်ပုံများကို ပို့ပေးပါ။")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = ""

    # ဓါတ်ပုံဖြစ်ပါက OCR သုံး၍ စာသားပြောင်းယူခြင်း
    if update.message.photo:
        await update.message.reply_text("🔍 ဓါတ်ပုံထဲမှ လက်ရေးစာရင်းများကို ဖတ်ရှုနေပါသည်။ ခဏစောင့်ပေးပါ...")
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # EasyOCR ဖြင့် ဓါတ်ပုံထဲမှ စာသားဖတ်ခြင်း
        ocr_results = reader.readtext(bytes(photo_bytes), detail=0)
        user_text = "\n".join(ocr_results)
        
        # Caption ပါလာပါကလည်း ထည့်သွင်းခြင်း
        if update.message.caption:
            user_text += "\n" + update.message.caption
    else:
        user_text = update.message.text

    if not user_text:
        await update.message.reply_text("❌ စာရင်း စာသား မတွေ့ပါ။")
        return

    results, total = parse_2d_text(user_text)
    if not results:
        await update.message.reply_text("❌ စာရင်း ပုံစံ ခွဲခြား၍ မရပါ။ စာရွက်ပုံ ပိုမို ရှင်းလင်းစွာ ရိုက်ပေးပါ သို့မဟုတ် စာအဖြစ် ပို့ပေးပါ။")
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
    import os
import re
from flask import Flask
from threading import Thread
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

        # ၁။ အပူး စာရင်း စစ်ဆေးခြင်း (ဥပမာ - အပူး 500 / double 500)
        if "အပူး" in line_str or "double" in line_str.lower():
            match = re.search(r'(\d+)', line_str)
            if match:
                amount = int(match.group(1))
                subtotal = 10 * amount
                grand_total += subtotal
                results.append(f"• အပူး (10 ကွက်) x {amount} = {subtotal:,} ကျပ်")
                continue

        # ၂။ `*`, `.`, `/`, `-` စတာတွေကို separator အဖြစ် ညီမျှအောင် ပြောင်းလဲခြင်း
        # R သီးသန့် ပါမပါ ခွဲထုတ်ခြင်း
        r_amount = 0
        r_match = re.search(r'[Rr]\s*(\d+)', line_str)
        if r_match:
            r_amount = int(r_match.group(1))
            clean_line = re.sub(r'[Rr]\s*\d+', '', line_str)
        else:
            clean_line = line_str

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
    await update.message.reply_text("👋 မင်္ဂလာပါ! Viber မှ Share လိုက်သော 2D စာရင်း သို့မဟုတ် ဓါတ်ပုံများကို ပို့ပေးပါ။")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # စာသား (Text) သို့မဟုတ် ဓါတ်ပုံ၏ Caption ကို ဖတ်ယူခြင်း
    user_text = update.message.text or update.message.caption

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
    
    # Text ရော Photo (Caption ပါ) ပါ လက်ခံအောင် ပြင်ဆင်ထားခြင်း
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_message))
    
    app.run_polling()
    import os
import re
from flask import Flask
from threading import Thread
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

        # ၁။ အပူး စာရင်း စစ်ဆေးခြင်း (ဥပမာ - အပူး 500 / double 500)
        if "အပူး" in line_str or "double" in line_str.lower():
            match = re.search(r'(\d+)', line_str)
            if match:
                amount = int(match.group(1))
                subtotal = 10 * amount
                grand_total += subtotal
                results.append(f"• အပူး (10 ကွက်) x {amount} = {subtotal:,} ကျပ်")
                continue

        # ၂။ `*`, `.`, `/`, `-` စတာတွေကို separator အဖြစ် ညီမျှအောင် ပြောင်းလဲခြင်း
        # R သီးသန့် ပါမပါ ခွဲထုတ်ခြင်း
        r_amount = 0
        r_match = re.search(r'[Rr]\s*(\d+)', line_str)
        if r_match:
            r_amount = int(r_match.group(1))
            # R အပိုင်းကို စာသားထဲက ခဏဖယ်ထုတ်ထားမည်
            clean_line = re.sub(r'[Rr]\s*\d+', '', line_str)
        else:
            clean_line = line_str

        # သင်္ကေတပေါင်းစုံ (*, ., /, -, space) များကို space တစ်ခုတည်းအဖြစ် ပြောင်းလဲခြင်း
        normalized = re.sub(r'[\*\.\/\-\s]+', ' ', clean_line).strip()
        tokens = normalized.split()

        # ဂဏန်း ၂ လုံးပါသော 2D ဂဏန်းများနှင့် ငွေပမာဏကို သီးခြားခွဲထုတ်ခြင်း
        nums = []
        amounts = []

        for item in tokens:
            if item.isdigit():
                if len(item) == 2:
                    nums.append(item)
                else:
                    amounts.append(int(item))

        # ဂဏန်းရော ငွေပမာဏပါ ပါဝင်မှ တွက်ချက်မည်
        if nums and amounts:
            base_amount = amounts[0] # ပထမဆုံး တွေ့သော ငွေပမာဏ
            
            # မူရင်းဂဏန်းများ တွက်ချက်ခြင်း
            direct_subtotal = len(nums) * base_amount
            grand_total += direct_subtotal
            num_str = ", ".join(nums)
            results.append(f"• {num_str} ({len(nums)} ကွက်) x {base_amount} = {direct_subtotal:,} ကျပ်")

            # R (အကွက်လှည့်) ပါဝင်ပါက ထပ်မံတွက်ချက်ခြင်း
            if r_amount > 0:
                rev_nums = [n[::-1] for n in nums]
                rev_subtotal = len(rev_nums) * r_amount
                grand_total += rev_subtotal
                rev_str = ", ".join(rev_nums)
                results.append(f"  └ R: {rev_str} ({len(rev_nums)} ကွက်) x {r_amount} = {rev_subtotal:,} ကျပ်")

    return results, grand_total

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 မင်္ဂလာပါ! Viber မှ Share လိုက်သော 2D စာရင်းများကို ပို့ပေးပါ။")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results, total = parse_2d_text(update.message.text)
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

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
