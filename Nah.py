from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = "7539730736:AAF_yMu8sDeZkVyOgKQ5TayfGVb3Jsbej7g"

# Temporary in-memory selection per chat
selected_bots = {}

# ================= ADMIN CHECK =================

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("Use this inside a group.")
        return False

    member = await chat.get_member(user.id)
    if member.status not in ("administrator", "creator"):
        await update.message.reply_text("Only group admins can use this.")
        return False

    return True

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot Admin Manager Active\n\n"
        "Commands:\n"
        "/selectbots – Select bots & promote to admin"
    )

# ================= SELECT BOTS =================

async def select_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    chat = update.effective_chat
    admins = await chat.get_administrators()

    bots_in_group = [m.user for m in admins if m.user.is_bot]
    
    if not bots_in_group:
        await update.message.reply_text("No bots found in this group.")
        return

    selected_bots[chat.id] = set()

    keyboard = []
    for bot in bots_in_group:
        name = f"@{bot.username}" if bot.username else bot.full_name
        keyboard.append([
            InlineKeyboardButton(name, callback_data=f"toggle_{bot.id}")
        ])

    keyboard.append([
        InlineKeyboardButton("✅ Promote Selected", callback_data="promote_selected")
    ])

    await update.message.reply_text(
        "Select bots to promote:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ================= BUTTON HANDLER =================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id
    data = query.data

    await query.answer()

    if data.startswith("toggle_"):
        bot_id = int(data.split("_")[1])

        if bot_id in selected_bots.get(chat_id, set()):
            selected_bots[chat_id].remove(bot_id)
        else:
            selected_bots[chat_id].add(bot_id)

        await query.edit_message_text(
            f"✅ Selected Bots: {len(selected_bots[chat_id])}\n\n"
            "Tap more or press ✅ Promote Selected"
        )

    elif data == "promote_selected":
        await promote_selected(query, context)

# ================= PROMOTE SELECTED =================

async def promote_selected(query, context):
    chat = query.message.chat
    bots = selected_bots.get(chat.id, set())

    if not bots:
        await query.edit_message_text("❌ No bots selected.")
        return

    success = 0
    failed = 0

    for bot_id in bots:
        try:
            await context.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=bot_id,
                can_manage_chat=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_promote_members=False,
            )
            success += 1
        except:
            failed += 1

    selected_bots.pop(chat.id, None)

    await query.edit_message_text(
        f"✅ Promotion Complete\n\n"
        f"Success: {success}\n"
        f"Failed: {failed}"
    )

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("selectbots", select_bots))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
