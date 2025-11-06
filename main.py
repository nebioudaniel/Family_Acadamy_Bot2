import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from telegram.error import BadRequest

# --- Configuration & Global Constants ---

# 1. TOKEN: Updated with the valid token you provided.
BOT_TOKEN = "8408457893:AAGN0q_O2QE-yG70T01JzPnFpIlAOvWdzzo"
if not BOT_TOKEN:
    raise ValueError("FATAL: BOT_TOKEN is not set.")

# Your Support Chat ID (Where registration details and direct messages will be forwarded)
# NOTE: This MUST be an integer ID for sending messages, though the input was a string.
# I am leaving it as a string for now but recommend changing it to an INT in production.
SUPPORT_CHAT_ID = "8323892309"

# Conversation States for Registration Flow (Kept for existing logic)
NAME, CLASS, REFERENCE_CODE = range(3)

# Conversation State for Direct Message Flow
SEND_MESSAGE = 99

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ACADEMY DATA (Unchanged) ---

FULL_COURSE_LIST_TEXT = """
• Civics and Moral Education
• Emerging Technology
• Communicative English Skills II
• Anthropology
• Economics
• General Chemistry
• Applied Math I
• Inclussiveness (Inclusiveness)
• Entrepreneurship
• Logic and Critical Thinking
• General Psychology
• Global Trends
• Geography of Ethiopia and the Horn
• Maths for Social Science
"""

ABOUT_US_AMHARIC = f"""
**ℹ️ ስለ Family Academy (About Us):**
Family Academy የተመሰረተው በ**2017 ዓ.ም** ሲሆን፣ ዋና አላማውም በ12ኛ ክፍል የማትሪክ ፈተና የሚጠየቁትን ዋና ዋና ትምህርቶች በጥልቀት እና በቀላሉ ማስተማር ነው፡፡ የኛ አካዳሚ ቀደም ብሎ ከተማሪዎች ጋር በቅንነት በመስራት በሺዎች የሚቆጠሩ ተማሪዎች የተሻለ ውጤት እንዲያመጡ ረድቷል፡፡

**የምናቀርባቸው ዋና ዋና ኮርሶች (Major Courses):**
{FULL_COURSE_LIST_TEXT}
"""

REGISTER_INSTRUCTIONS = """
**📝 የመመዝገቢያ ሂደት (Registration Steps):**
1. **ምዝገባ:** ለ Family Academy ፕሮግራም ሙሉ በሙሉ ለመመዝገግ ከታች ካሉት ክፍያዎች አንዱን በመጠቀም መክፈል አለብዎ፡፡
2. **የክፍያ መጠን:** ለአንድ ሴሚስተር **250 ብር** ብቻ ነው፡፡
3. **የመክፈያ ዘዴዎች (Payment Methods):**
   • **Google Pay/PayPal** - ለውጭ አገር ክፍያዎች
   • **CBE Account** - [Please Insert CBE Account Number]
   • **አካውንት ስም** - [Please Insert Account Name]
4. **ማረጋገጫ:** ክፍያውን እንደፈጸሙ የሚያሳይ **screenshot** ወይም **የባንክ Refernce Code** መላክ አለብዎ፡፡ ይህንን ካደረጉ በኋላ ወደ ትምህርቱ መግቢያ በTelegram በኩል ይላክልዎታል፡፡
"""

FAQ_ANSWERS = """
**❓ ተደጋጋሚ ጥያቄዎች (FAQ):**

**Q1. እንዴት ነው መመዝገብ የምንችለው?**
**A:** መጀመሪያ "📝 Register Now" የሚለውን በመጫን ያሉትን የክፍያ ዘዴዎች በመጠቀም መክፈል፡፡ ከዛም የክፍያውን ማስረጃ ወይም **Reference Code** ማስገባት አለቦት፡፡

**Q2. ክፍያ ስንት ብር ነው?**
**A:** ክፍያው ለአንድ ሴሚስተር **250 ብር** ብቻ ነው፡፡

**Q3. የጥናት ሞጁሎች አሉን ወይ?**
**A:** አዎ፡፡ ለሁሉም ትምህርቶች **Lecture Notes** እና **Module** ይዘጋጃሉ፡፡ በተጨማሪም **Diagram**፣ **Outline** እና ሌሎች የማጥኛ ቁሳቁሶች ይቀርባሉ፡፡

**Q4. የመጨረሻ ፈተና እና ምዘና እንዴት ነው የሚሰጠው?**
**A:** ከትምህርቱ መጨረሻ በኋላ የሚኖረው **Mid-Exam** እና **Final Exam** በ Family Academy በኩል ተዘጋጅቶ ይቀርባል፡፡

**Q5. ትምህርቱን የምንከታተለው የትኛው Platform ላይ ነው?**
**A:** ትምህርቶቹ በአዲስ መልክ በተዘጋጀው የራሳችን **Platform** ላይ የሚሰጡ ይሆናሉ፡፡ ሁሉንም ትምህርቶች በማንኛውም ጊዜ መከታተል ይቻላል፡፡
"""

CONTACT_INFO = """
📞 **የእውቂያ መረጃ (Contact Info):**
• **ዋና የ Telegram Support:** @family\_academyadmin
• **Email:** familyacademy979@gmail.com
• **Phone Number:** 0987880902 || 0799645851
"""

# --- Reusable Keyboards (MODIFIED) ---

def get_start_keyboard():
    """Returns the NEW support-focused keyboard for the initial /start message."""
    keyboard = [
        [
            InlineKeyboardButton("📞 Contact Us", callback_data="SHOW_CONTACT"),
            InlineKeyboardButton("ℹ️ About Us", callback_data="VIEW_INFO"),
        ],
        [
            InlineKeyboardButton("📩 Send Direct Message", callback_data="START_DIRECT_MESSAGE"), # New Button
        ]
        # Registration and other buttons from the old menu are now gone from the main view
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_start_keyboard():
    """Returns a simple keyboard to go back to the NEW main menu."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Go Back to Main Menu", callback_data="GO_BACK_START")]])

def get_cancel_message_keyboard():
    """Keyboard to cancel direct message composition."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Message", callback_data="GO_BACK_START")]])


# --- NEW DIRECT MESSAGE CONVERSATION HANDLERS ---

async def start_direct_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to compose a direct message."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        text="**📩 Direct Message to Family Academy Support**\n\n"
             "እባክዎ መልዕክትዎን ወይም ጥያቄዎን በአንድ ጊዜ ይላኩልን፡፡ አድሚኖች መልዕክቱን ወዲያውኑ አይተው ይመልሱልዎታል፡፡\n\n"
             "**ማስታወሻ:** ጽሑፍ ብቻ ወይም ፎቶ ከመግለጫ ጋር መላክ ይችላሉ፡፡",
        parse_mode='Markdown',
        reply_markup=get_cancel_message_keyboard()
    )
    return SEND_MESSAGE

async def receive_direct_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the message (text or photo) and forwards it to the support chat."""
    user = update.effective_user

    # Compile the summary header for the support team
    summary_header = (
        "🔔 **NEW DIRECT MESSAGE** 🔔\n"
        f"**From:** @{user.username or 'N/A'} (ID: `{user.id}`)\n"
        "-------------------------------------\n"
    )

    # 1. Forward the message (photo/text) to the support chat
    try:
        if update.message.text:
            await context.bot.send_message(
                chat_id=SUPPORT_CHAT_ID,
                text=summary_header + update.message.text,
                parse_mode='Markdown'
            )
            confirmation_text = "✅ **መልዕክትዎ ተልኳል!** Family Academy ቡድን መልዕክትዎን ተመልክቶ በቅርቡ መልስ ይሰጥዎታል፡፡"

        elif update.message.photo:
            caption = summary_header + (update.message.caption or "*No Caption Provided*")
            await context.bot.send_photo(
                chat_id=SUPPORT_CHAT_ID,
                photo=update.message.photo[-1].file_id,
                caption=caption,
                parse_mode='Markdown'
            )
            confirmation_text = "✅ **ፎቶ እና መልዕክትዎ ተልኳል!** Family Academy ቡድን መልዕክትዎን ተመልክቶ በቅርቡ መልስ ይሰጥዎታል፡፡"

        else:
            # Should not happen with the filter, but as a safeguard
            await update.message.reply_text("⚠️ እባክዎ ትክክለኛ የጽሑፍ መልዕክት ወይም ፎቶ ይላኩ፡፡", reply_markup=get_cancel_message_keyboard())
            return SEND_MESSAGE

        # 2. Confirm to the user and return to main menu
        await update.message.reply_text(
            confirmation_text,
            reply_markup=get_back_to_start_keyboard()
        )

    except Exception as e:
        logger.error(f"Failed to forward direct message to support chat {SUPPORT_CHAT_ID}: {e}")
        await update.message.reply_text(
            "❌ **ስህተት (Error):** መልዕክትዎ ወደ ሲስተሙ መግባት አልቻለም፡፡ እባክዎን 'Contact Us' የሚለውን በመጠቀም ያግኙን፡፡",
            reply_markup=get_back_to_start_keyboard()
        )

    context.user_data.clear()
    return ConversationHandler.END

async def cancel_direct_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the message composition and returns to the start menu."""
    # Use the button handler to go back to start
    await button_handler(update, context)
    return ConversationHandler.END

# --- REGISTRATION CONVERSATION HANDLERS (Unchanged in logic) ---
#NOTE: Registration handlers are still present but only accessible if you add a 'Register' button back
# or if you use the direct callback data in a message (e.g., /start_reg).

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the registration conversation (hidden from main menu now)."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        text=f"**📝 Family Academy Registration**\n\n{REGISTER_INSTRUCTIONS}\n\n**🛑 Step 1/3: Please enter your full name (Full Name):**",
        parse_mode='Markdown'
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the user's name and asks for the class."""
    user_name = update.message.text
    context.user_data['name'] = user_name

    await update.message.reply_text(
        f"✅ Thank you, **{user_name}**.\n\n**🛑 Step 2/3: Please enter your current class (e.g., 10, 12, Matric):**",
        parse_mode='Markdown'
    )
    return CLASS

async def get_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the user's class and asks for the bank reference code."""
    user_class = update.message.text
    context.user_data['class'] = user_class

    payment_info = REGISTER_INSTRUCTIONS.replace("**📝 የመመዝገቢያ ሂደት (Registration Steps):**\n\n", "")

    await update.message.reply_text(
        f"✅ Your class is recorded as **{user_class}**.\n\n"
        f"**🛑 Step 3/3: Payment Reference Code**\n\n"
        f"**1. Make the payment:**\n{payment_info}\n\n"
        f"**2. Type the Bank Reference/Transaction Code now to complete registration:**",
        parse_mode='Markdown'
    )
    return REFERENCE_CODE

async def get_reference_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the reference code and forwards all data to the support chat."""
    ref_code = update.message.text
    user_info = context.user_data
    user = update.effective_user

    summary_text = (
        "🔥 **ACADEMY REGISTRATION SUBMISSION** 🔥\n\n"
        f"**User:** {user_info.get('name', 'N/A')} (@{user.username or 'N/A'})\n"
        f"**User ID:** `{user.id}`\n"
        f"**Class:** {user_info.get('class', 'N/A')}\n"
        f"**Reference Code:** `{ref_code}`\n\n"
        "**Action:** Please verify payment using the code, enroll the student, and send the course access link."
    )

    try:
        await context.bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=summary_text,
            parse_mode='Markdown'
        )
        await update.message.reply_text(
            "🎉 **Registration Complete!** 🎉\n\nYour details have been successfully sent. A staff member will contact you shortly.",
            reply_markup=get_back_to_start_keyboard()
        )
    except Exception as e:
        logger.error(f"Failed to forward registration details: {e}")
        await update.message.reply_text("❌ **Error:** Could not submit your registration due to an internal error.")

    context.user_data.clear()
    return ConversationHandler.END

async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        'Registration process canceled. Press /start to open the main menu.',
        reply_markup=get_back_to_start_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END


# --- GENERAL HANDLERS (MODIFIED) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the NEW support-focused welcome message."""
    reply_markup = get_start_keyboard()
    # New custom welcome message
    welcome_text = (
      "👋 **ውድ ተማሪዎቻችን ሰላም!**\n\n"
"መልዕክት ለመላክ፣ ለመገናኘት ወይም ስለ Family Academy ጥያቄ ለመጠየቅ ከፈለጉ፣ "
"እዚህ በቀጥታ መጠየቅ ትችላላችሁ፣ እኛም **ወዲያውኑ** እንመልሳለን።\n\n"
"**እባክዎ ከታች ያለውን ምርጫ ይምረጡ።**"

    )

    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button presses for general information pages and delegates navigation/actions."""
    query = update.callback_query

    # Delegate to the direct message handler first
    if query.data == 'START_DIRECT_MESSAGE':
        # Don't answer the query here, let the conversation handler entry point do it
        # Note: We need to rely on the ConversationHandler entry point to handle this now.
        # For simplicity and to avoid restructuring the main ConversationHandler, I'll redirect it.
        # However, for the 'Cancel Message' button which uses 'GO_BACK_START', we handle it here.
        pass # Let the Direct Message CH handle this.
        return

    await query.answer()
    data = query.data
    response_text = ""
    reply_markup = get_back_to_start_keyboard()

    # Handle Navigation Button
    if data == 'GO_BACK_START':
        await query.edit_message_text(
            text="👋 **Welcome back to the main support menu!** Please choose an option:",
            parse_mode='Markdown',
            reply_markup=get_start_keyboard()
        )
        return

    # Handle Information Buttons
    elif data == 'VIEW_INFO':
        response_text = ABOUT_US_AMHARIC

    elif data == 'SHOW_CONTACT':
        response_text = CONTACT_INFO

    # All other old menu items are removed or handled differently
    elif data in ['SHOW_COURSES', 'SHOW_REMEDIAL', 'SHOW_FAQ', 'START_REGISTRATION']:
        # Catch-all for old buttons that might still be in old messages
        response_text = "⚠️ This option is not currently available in the main menu. Please use the new options."

    # Edit the message with the response
    if response_text:
        await query.edit_message_text(
            text=response_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

# --- MAIN FUNCTION ---

def main() -> None:
    """Starts the bot using polling."""

    if not BOT_TOKEN:
        logger.error("FATAL: BOT_TOKEN is missing. Cannot start bot.")
        return

    try:
        application = Application.builder().token(BOT_TOKEN).build()
    except Exception as e:
        logger.error(f"Failed to build application: {e}. Check your token again.")
        return

    # 1. Direct Message Conversation Handler (NEW)
    direct_message_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_direct_message, pattern='^START_DIRECT_MESSAGE$')],
        states={
            SEND_MESSAGE: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, receive_direct_message)],
        },
        fallbacks=[CallbackQueryHandler(cancel_direct_message, pattern='^GO_BACK_START$'), CommandHandler('start', cancel_direct_message)],
        allow_reentry=True
    )
    application.add_handler(direct_message_handler)

    # 2. Registration Conversation Handler (Kept in case needed later, hidden from start menu)
    registration_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_registration, pattern='^START_REGISTRATION$')],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_class)],
            REFERENCE_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_reference_code)],
        },
        fallbacks=[CommandHandler('start', cancel_registration)],
        allow_reentry=True
    )
    application.add_handler(registration_handler)

    # 3. General Command and Button Handlers
    application.add_handler(CommandHandler("start", start_command))
    # This handler catches all other callback queries, including GO_BACK_START and the other info buttons.
    # It excludes the entry points for the CHs.
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^(?!START_DIRECT_MESSAGE|START_REGISTRATION$).*$'))

    logger.info("Starting bot in local polling mode...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()