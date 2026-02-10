import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, Application, ConversationHandler, CallbackQueryHandler, CommandHandler
from data_manager import save_log, check_date_exists, overwrite_log
from workout_parser import WorkoutParser

import configparser
import os
import sys

# Load Config
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.ini')
config.read(config_path, encoding='utf-8')

try:
    TOKEN = config['TELEGRAM']['BOT_TOKEN']
    ALLOWED_ID = int(config['TELEGRAM']['ALLOWED_ID'])
except KeyError:
    print("❌ 오류: config.ini 파일을 찾을 수 없거나 설정이 잘못되었습니다.")
    print("README.md를 참고하여 config.ini를 설정해주세요.")
    sys.exit(1)
except ValueError:
     print("❌ 오류: ALLOWED_ID는 숫자여야 합니다.")
     sys.exit(1)

# States
SELECT_AREA, CONFIRM_DATE, MANUAL_DATE, HANDLE_EXISTING = range(4)

# Workout Areas
AREAS = ["가슴", "등", "하체", "어깨", "이두", "삼두", "복근", "유산소"]

async def post_init(application: Application) -> None:
    await application.bot.send_message(chat_id=ALLOWED_ID, text="🚀 Iron Secretary 가동 시작!")

async def post_stop(application: Application) -> None:
    try:
        await application.bot.send_message(chat_id=ALLOWED_ID, text="😴 Iron Secretary 종료 중...")
    except Exception as e:
        print(f"종료 메시지 전송 실패: {e}")

async def start_workout_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 2. 보안 체크
    user_id = update.message.from_user.id
    if user_id != ALLOWED_ID:
        print(f"⚠️ 권한 없는 접근 차단: {user_id}")
        return ConversationHandler.END

    text = update.message.text
    context.user_data['workout_text'] = text
    context.user_data['selected_areas'] = []
    
    # Try to parse date from text
    parser = WorkoutParser()
    parsed = parser.parse_bulk_text(text)
    
    date_found = None
    if parsed:
        date_found = sorted(parsed.keys())[0]
    
    if not date_found:
        date_found = datetime.now().strftime('%Y-%m-%d')
        
    context.user_data['workout_date'] = date_found
    
    # Create Area Selection Keyboard
    keyboard = build_area_keyboard([])
    await update.message.reply_text(
        f"💪 운동 부위를 선택하세요 (복수 선택 가능)\n\n입력을 취소하려면 /cancel 을 입력하세요.",
        reply_markup=keyboard
    )
    return SELECT_AREA

def build_area_keyboard(selected):
    buttons = []
    row = []
    for area in AREAS:
        label = f"✅ {area}" if area in selected else area
        row.append(InlineKeyboardButton(text=label, callback_data=f"TOGGLE_{area}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    # Action buttons
    buttons.append([InlineKeyboardButton(text="완료 (Done)", callback_data="DONE")])
    return InlineKeyboardMarkup(buttons)

async def area_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    selected = context.user_data.get('selected_areas', [])
    
    if data.startswith("TOGGLE_"):
        area = data.split("_")[1]
        if area in selected:
            selected.remove(area)
        else:
            selected.append(area)
        context.user_data['selected_areas'] = selected
        
        await query.edit_message_reply_markup(reply_markup=build_area_keyboard(selected))
        return SELECT_AREA
        
    elif data == "DONE":
        date_str = context.user_data['workout_date']
        keyboard = [
            [InlineKeyboardButton("저장 (Save)", callback_data="SAVE")],
            [InlineKeyboardButton("날짜 수정 (Edit Date)", callback_data="EDIT_DATE")]
        ]
        
        areas_str = ", ".join(selected) if selected else "선택 안함"
        msg = f"📅 날짜: {date_str}\n💪 부위: {areas_str}\n\n저장하시겠습니까?"
        
        await query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return CONFIRM_DATE

async def confirm_date_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "SAVE":
        return await check_existing_log(update, context)
    elif data == "EDIT_DATE":
        await query.edit_message_text(text="수정할 날짜를 입력해주세요 (예: 2026-02-09, 2/9, 오늘, 어제 등)\n취소하려면 /cancel")
        return MANUAL_DATE

async def manual_date_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    new_date = None
    try:
        datetime.strptime(text, '%Y-%m-%d')
        new_date = text
    except ValueError:
        pass
        
    if not new_date:
        try:
            if "/" in text:
                m, d = map(int, text.split('/'))
                year = datetime.now().year
                new_date = f"{year}-{m:02d}-{d:02d}"
        except:
            pass
            
    if not new_date:
         if text == "오늘":
             new_date = datetime.now().strftime('%Y-%m-%d')
         elif text == "어제":
             new_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    if new_date:
        context.user_data['workout_date'] = new_date
        
        selected = context.user_data.get('selected_areas', [])
        areas_str = ", ".join(selected) if selected else "선택 안함"
        
        keyboard = [
            [InlineKeyboardButton("저장 (Save)", callback_data="SAVE")],
            [InlineKeyboardButton("날짜 수정 (Edit Date)", callback_data="EDIT_DATE")]
        ]
        msg = f"📅 날짜: {new_date}\n💪 부위: {areas_str}\n\n저장하시겠습니까?"
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return CONFIRM_DATE
    else:
        await update.message.reply_text("⛔ 날짜 형식을 인식하지 못했습니다. 다시 입력해주세요. (예: 2026-02-09)")
        return MANUAL_DATE

async def check_existing_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    date_str = context.user_data['workout_date']
    
    if check_date_exists(date_str):
        keyboard = [
            [InlineKeyboardButton("이어쓰기 (Append)", callback_data="APPEND")],
            [InlineKeyboardButton("덮어쓰기 (Overwrite)", callback_data="OVERWRITE")],
            [InlineKeyboardButton("취소 (Cancel)", callback_data="CANCEL")]
        ]
        msg = f"⚠️ {date_str} 날짜에 이미 기록이 존재합니다.\n어떻게 하시겠습니까?"
        await query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return HANDLE_EXISTING
    else:
        return await perform_save(update, context, overwrite=False)

async def handle_existing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "APPEND":
        return await perform_save(update, context, overwrite=False)
    elif data == "OVERWRITE":
        return await perform_save(update, context, overwrite=True)
    elif data == "CANCEL":
        await query.edit_message_text("🚫 작업이 취소되었습니다.")
        return ConversationHandler.END

async def perform_save(update: Update, context: ContextTypes.DEFAULT_TYPE, overwrite=False):
    query = update.callback_query
    if query:
        await query.edit_message_text("💾 저장 중...")
    else:
        await update.message.reply_text("💾 저장 중...")
        
    text = context.user_data['workout_text']
    date_str = context.user_data['workout_date']
    selected = context.user_data.get('selected_areas', [])
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    areas_str = ", ".join(selected)
    
    final_content = f"### [{timestamp}] 운동 부위: {areas_str}\n\n### 운동 종목\n{text}"
    
    if overwrite:
        overwrite_log(date_str, final_content)
        action_msg = "덮어쓰기"
    else:
        save_log(date_str, final_content)
        action_msg = "기록"
    
    msg = f"✅ {date_str} 일지에 {action_msg} 완료! (MD)"
    
    if query:
         await query.edit_message_text(msg)
    else:
         await update.message.reply_text(msg)
         
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 작업이 취소되었습니다.")
    return ConversationHandler.END

if __name__ == '__main__':
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(post_init)
        .post_stop(post_stop)
        .build()
    )
    
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & (~filters.COMMAND), start_workout_log)],
        states={
            SELECT_AREA: [CallbackQueryHandler(area_handler)],
            CONFIRM_DATE: [CallbackQueryHandler(confirm_date_handler)],
            MANUAL_DATE: [MessageHandler(filters.TEXT & (~filters.COMMAND), manual_date_handler)],
            HANDLE_EXISTING: [CallbackQueryHandler(handle_existing_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    
    print("🚀 보안 모드로 가동 중... (Interactive Version)")
    application.run_polling()
