import datetime
import traceback
import cnlunar
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8891359619:AAEI3bvAv9nK0zE-DFuvGqzrnD3iI-qf1d4"

# វចនានុក្រមបកប្រែមេឃ និងដី (Stems & Branches) ជាភាសាខ្មែរ
STEMS_KHMER = {
    "甲": "ឈើ-យ៉ាង (កាប)", "乙": "ឈើ-យីន (អ៊ិត)",
    "丙": "ភ្លើង-យ៉ាង (ពិត)", "丁": "ភ្លើង-យីន (ទិញ)",
    "戊": "ដី-យ៉ាង (អ៊ូ)", "己": "ដី-យីន (ជី)",
    "庚": "មាស-យ៉ាង (កឹង)", "辛": "មាស-យីន (ស៊ីន)",
    "壬": "ទឹក-យ៉ាង (រ៉េន)", "癸": "ទឹក-យីន (គុយ)"
}

BRANCHES_KHMER = {
    "子": "ជូត (កណ្តុរ)", "丑": "ឆ្លូវ (គោ)", "寅": "ខាល (ខ្លា)", "卯": "ថោះ (ទន្សាយ)",
    "辰": "រោង (នាគ)", "巳": "ម្សាញ់ (ពស់)", "午": "មមី (សេះ)", "未": "មមែ (ពពែ)",
    "申": "វក (ស្វា)", "酉": "រកា (មាន់)", "戌": "ច (ឆ្កែ)", "亥": "កុរ (ជ្រូក)"
}

ZODIAC_ANIMALS = ["ជូត (កណ្តុរ)", "ឆ្លូវ (គោ)", "ខាល (ខ្លា)", "ថោះ (ទន្សាយ)", 
                  "រោង (នាគ)", "ម្សាញ់ (ពស់)", "មមី (សេះ)", "មមែ (ពពែ)", 
                  "វក (ស្វា)", "រកា (មាន់)", "ច (ឆ្កែ)", "កុរ (ជ្រូក)"]

GUA_DATA = {
    1: {"group": "កើត ៤ ទិស", "element": "ទឹក", "good": "អាគ្នេយ៍, កើត, ជើង, ត្បូង", "bad": "លិច, ពាយ័ព្យ, និរតី, ឦសាន"},
    2: {"group": "លិច ៤ ទិស", "element": "ដី", "good": "ឦសាន, លិច, ពាយ័ព្យ, និរតី", "bad": "កើត, អាគ្នេយ៍, ជើង, ត្បូង"},
    3: {"group": "កើត ៤ ទិស", "element": "ឈើ", "good": "ត្បូង, ជើង, អាគ្នេយ៍, កើត", "bad": "និរតី, ឦសាន, លិច, ពាយ័ព្យ"},
    4: {"group": "កើត ៤ ទិស", "element": "ឈើ", "good": "ជើង, ត្បូង, កើត, អាគ្នេយ៍", "bad": "ឦសាន, និរតី, ពាយ័ព្យ, លិច"},
    6: {"group": "លិច ៤ ទិស", "element": "មាស", "good": "លិច, ឦសាន, និរតី, ពាយ័ព្យ", "bad": "អាគ្នេយ៍, កើត, ត្បូង, ជើង"},
    7: {"group": "លិច ៤ ទិស", "element": "មាស", "good": "ពាយ័ព្យ, និរតី, ឦសាន, លិច", "bad": "កើត, អាគ្នេយ៍, ជើង, ត្បូង"},
    8: {"group": "លិច ៤ ទិស", "element": "ដី", "good": "និរតី, ពាយ័ព្យ, លិច, ឦសាន", "bad": "អាគ្នេយ៍, កើត, ត្បូង, ជើង"},
    9: {"group": "កើត ៤ ទិស", "element": "ភ្លើង", "good": "កើត, អាគ្នេយ៍, ជើង, ត្បូង", "bad": "ពាយ័ព្យ, លិច, ឦសាន, និរតី"}
}

def translate_pillar(pillar_str: str) -> str:
    if not pillar_str or len(pillar_str) < 2:
        return str(pillar_str)
    stem = pillar_str[0]
    branch = pillar_str[1]
    stem_kh = STEMS_KHMER.get(stem, stem)
    branch_kh = BRANCHES_KHMER.get(branch, branch)
    return f"{pillar_str} ({stem_kh} + {branch_kh})"

def calculate_gua(year: int, gender: str) -> int:
    sum_digits = sum(int(d) for d in str(year)[-2:])
    while sum_digits > 9:
        sum_digits = sum(int(d) for d in str(sum_digits))
    gua = (10 - sum_digits) if gender == "ប្រុស" else (sum_digits + 5) if year < 2000 else (9 - sum_digits) if gender == "ប្រុស" else (sum_digits + 6)
    while gua > 9:
        gua = sum(int(d) for d in str(gua))
    if gua == 5:
        gua = 2 if gender == "ប្រុស" else 8
    return gua

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.strip().split()
        if len(parts) == 3:
            date_str, time_str, gender = parts
        elif len(parts) == 2:
            date_str, gender = parts
            time_str = "12:00"
        else:
            await update.message.reply_text("ទម្រង់បញ្ចូល៖ `1986-09-10 08:30 ប្រុស` ឬ `1986-09-10 ប្រុស`", parse_mode="Markdown")
            return

        if gender not in ["ប្រុស", "ស្រី"]:
            await update.message.reply_text("សូមបញ្ជាក់ភេទឱ្យត្រូវ៖ `ប្រុស` ឬ `ស្រី`")
            return

        if ":" in time_str and len(time_str.split(":")[0]) == 1:
            time_str = "0" + time_str

        dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        try:
            lunar = cnlunar.Lunar(dt, godType='8char')
        except Exception:
            lunar = cnlunar.Lunar(dt)

        year_p = getattr(lunar, 'year8Char', None) or getattr(lunar, 'yearGanZhi', '')
        month_p = getattr(lunar, 'month8Char', None) or getattr(lunar, 'monthGanZhi', '')
        day_p = getattr(lunar, 'day8Char', None) or getattr(lunar, 'dayGanZhi', '')
        hour_p = getattr(lunar, 'twohour8Char', None) or getattr(lunar, 'twohourGanZhi', '')

        if year_p and len(year_p) >= 2 and year_p[1] in BRANCHES_KHMER:
            zodiac = BRANCHES_KHMER[year_p[1]]
        else:
            zodiac = ZODIAC_ANIMALS[(dt.year - 4) % 12]

        day_master = day_p[0] if len(day_p) > 0 else ""
        self_element = STEMS_KHMER.get(day_master, day_master)

        gua = calculate_gua(dt.year, gender)
        gua_info = GUA_DATA[gua]

        res = (
            f"🔮 *លទ្ធផលវិភាគ BaZi & ហុងស៊ុយពេញលេញ*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 *ព័ត៌មានកំណើត៖* {date_str} ម៉ោង {time_str} ({gender})\n"
            f"• សត្វឆ្នាំកំណើត៖ *{zodiac}*\n"
            f"• ធាតុប្រចាំខ្លួន (Day Master)៖ *{self_element}*\n\n"
            f"🏛 *សសរទាំង ៤ (Four Pillars)៖*\n"
            f"• សសរឆ្នាំ (Year)៖ `{translate_pillar(year_p)}`\n"
            f"• សសរខែ (Month)៖ `{translate_pillar(month_p)}`\n"
            f"• សសរថ្ងៃ (Day - ខ្លួនឯង)៖ `{translate_pillar(day_p)}`\n"
            f"• សសរម៉ោង (Hour)៖ `{translate_pillar(hour_p)}`\n\n"
            f"🧭 *ទិសដៅហុងស៊ុយ (BaZhai)៖*\n"
            f"• លេខក្វា៖ *{gua}* (ធាតុ {gua_info['element']})\n"
            f"• ក្រុមទិស៖ *{gua_info['group']}*\n"
            f"• ទិសសំណាង៖ {gua_info['good']}\n"
            f"• ទិសគ្រោះ៖ {gua_info['bad']}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💡 *ធាតុ `{self_element}` ជាធាតុស្នូលសម្រាប់ជ្រើសរើសពណ៌ និងរៀបចំផ្ទះ។*"
        )
        await update.message.reply_text(res, parse_mode="Markdown")

    except Exception:
        print("ERROR DETAILS:", traceback.format_exc())
        await update.message.reply_text("ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ! ឧទាហរណ៍៖ `1986-09-10 08:30 ប្រុស`", parse_mode="Markdown")

if __name__ == "__main__":
    # បន្ថែម Timeout ឱ្យវែងការពារបញ្ហាអ៊ីនធឺណិតខ្សោយ
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze))
    print("Bot កំពុងដំណើរការ...")
    app.run_polling()