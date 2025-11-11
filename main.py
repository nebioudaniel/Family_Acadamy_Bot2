import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
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

# Conversation States for Direct Message Flow (MODIFIED)
ASK_PHONE_NUMBER, SEND_MESSAGE = range(99, 101) # 99 and 100

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
    # This is an InlineKeyboardMarkup used for cancelling the message
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Message", callback_data="GO_BACK_START")]])

def get_phone_keyboard():
    """
    Returns a ReplyKeyboardMarkup with a 'Share Contact' button.
    This special button allows users to share their Telegram-associated phone number easily.
    """
    keyboard = [
        [
            KeyboardButton("📱 Share My Phone Number", request_contact=True)
        ]
    ]
    # We use ReplyKeyboardMarkup for this to ensure the special button works
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

# --- DIRECT MESSAGE CONVERSATION HANDLERS (MODIFIED) ---

async def start_direct_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation by asking for the phone number."""
    query = update.callback_query
    await query.answer()

    # The InlineKeyboard needs to be removed/replaced by the phone keyboard
    # For now, we will edit the message to present the new step.
    await query.edit_message_text(
        text="**📞 Step 1: Please share your Phone Number**\n\n"
             "መልዕክትዎን ከመላክዎ በፊት፣ አድሚኑ መልስ ሊሰጥዎ እንዲችል የስልክ ቁጥርዎን ማስገባት ግድ ነው፡፡\n"
             "**\"📱 Share My Phone Number\"** የሚለውን ቁልፍ በመጫን በቀላሉ ቁጥርዎን ማጋራት ይችላሉ፡፡ ወይም ደግሞ እራስዎ ማስገባት ይችላሉ፡፡",
        parse_mode='Markdown'
    )
    
    # Send a new message with the special ReplyKeyboardMarkup for phone sharing
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="**እባክዎ የስልክ ቁጥርዎን ያስገቡ:**",
        parse_mode='Markdown',
        reply_markup=get_phone_keyboard()
    )

    return ASK_PHONE_NUMBER

async def get_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the phone number (via contact or text) and moves to message composition."""
    phone_number = None

    if update.message.contact:
        # User used the 'Share Contact' button
        phone_number = update.message.contact.phone_number
    elif update.message.text:
        # User typed the number or other text
        phone_number = update.message.text

    if phone_number:
        # Store the phone number
        context.user_data['phone_number'] = phone_number

        # Confirm the phone number and ask for the message
        await update.message.reply_text(
            f"✅ **ስልክ ቁጥርዎ:** `{phone_number}` **ተመዝግቧል፡፡**\n\n"
             "**📩 Step 2: Now, send your message**\n"
             "እባክዎ መልዕክትዎን ወይም ጥያቄዎን በአንድ ጊዜ ይላኩልን፡፡ አድሚኖች መልዕክቱን ወዲያውኑ አይተው ይመልሱልዎታል፡፡\n\n"
             "**ማስታወሻ:** ጽሑፍ ብቻ ወይም ፎቶ ከመግለጫ ጋር መላክ ይችላሉ፡፡",
            parse_mode='Markdown',
            # We hide the ReplyKeyboard and present the InlineKeyboard for cancellation
            reply_markup=get_cancel_message_keyboard()
        )
        return SEND_MESSAGE
    else:
        # Should not happen with current filters, but as a safeguard
        await update.message.reply_text(
            "⚠️ እባክዎ የስልክ ቁጥርዎን በትክክል ያስገቡ፡፡",
            reply_markup=get_phone_keyboard()
        )
        return ASK_PHONE_NUMBER


async def receive_direct_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receives the message (text or photo) and forwards it to the support chat, including the phone number.
    FIXED: Escapes backticks in user text/caption to prevent Markdown parsing errors in the header.
    """
    user = update.effective_user
    phone_number = context.user_data.get('phone_number', 'N/A (Not Provided)')

    # Safely get username/ID text without extra formatting for the header
    user_info = f"@{user.username or 'N/A'} (ID: {user.id})"
    
    # Compile the summary header for the support team
    summary_header = (
        "🔔 **NEW DIRECT MESSAGE** 🔔\n"
        f"**From:** {user_info}\n"
        f"**📞 Phone:** `{phone_number}`\n" 
        "-------------------------------------\n"
    )
    
    # 1. Forward the message (photo/text) to the support chat
    try:
        # Ensure the phone keyboard is removed from the user's view
        reply_markup_remove = ReplyKeyboardMarkup([[]], resize_keyboard=True, one_time_keyboard=True, selective=True)

        if update.message.text:
            # FIX: Escape backticks in the user's text to prevent Markdown error
            safe_message = update.message.text.replace("`", "'")
            
            await context.bot.send_message(
                chat_id=SUPPORT_CHAT_ID,
                text=summary_header + safe_message,
                parse_mode='Markdown'
            )
            confirmation_text = "✅ **መልዕክትዎ ተልኳል!** Family Academy ቡድን መልዕክትዎን ተመልክቶ በቅርቡ መልስ ይሰጥዎታል፡፡"

        elif update.message.photo:
            caption_text = update.message.caption or "*No Caption Provided*"
            # FIX: Escape backticks in the photo caption
            safe_caption = caption_text.replace("`", "'")
            caption = summary_header + safe_caption
            
            await context.bot.send_photo(
                chat_id=SUPPORT_CHAT_ID,
                photo=update.message.photo[-1].file_id,
                caption=caption,
                parse_mode='Markdown'
            )
            confirmation_text = "✅ **ፎቶ እና መልዕክትዎ ተልኳል!** Family Academy ቡድን መልዕክትዎን ተመልክቶ በቅርቡ መልስ ይሰጥዎታል፡፡"

        else:
            # Should not happen with the filter, but as a safeguard
            await update.message.reply_text(
                "⚠️ እባክዎ ትክክለኛ የጽሑፍ መልዕክት ወይም ፎቶ ይላኩ፡፡", 
                reply_markup=get_cancel_message_keyboard() # Keep the inline cancel button
            )
            return SEND_MESSAGE

        # 2. Confirm to the user and return to main menu, removing the reply keyboard
        await update.message.reply_text(
            confirmation_text,
            reply_markup=reply_markup_remove # Remove the reply keyboard
        )
        # 3. Send the final main menu with the inline keyboard
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="👋 **Welcome back to the main support menu!** Please choose an option:",
            parse_mode='Markdown',
            reply_markup=get_start_keyboard()
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
    
    # Remove the Reply Keyboard if present (for phone number state)
    reply_markup_remove = ReplyKeyboardMarkup([[]], resize_keyboard=True, one_time_keyboard=True, selective=True)

    if update.callback_query:
        # User pressed the Inline 'Cancel Message' button
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text='Message composition canceled. Press /start to open the main menu.',
            reply_markup=None # Remove the inline cancel button
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Menu loaded.",
            reply_markup=reply_markup_remove # Ensure reply keyboard is removed
        )
    else:
        # User sent /start during the conversation (CommandHandler fallback)
        await update.message.reply_text(
            'Message composition canceled. Press /start to open the main menu.',
            reply_markup=reply_markup_remove # Remove the Reply Keyboard
        )
    
    # Call the main start command to return to the menu
    await start_command(update, context) 

    context.user_data.clear()
    return ConversationHandler.END

# --- REGISTRATION CONVERSATION HANDLERS (Unchanged in logic) ---

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
    """Sends the NEW support-focused welcome message, ensuring reply keyboard is removed."""
    reply_markup = get_start_keyboard()
    
    # A custom ReplyKeyboardMarkup is created to explicitly remove any existing Reply Keyboards (like the phone one)
    remove_keyboard = ReplyKeyboardMarkup([[]], resize_keyboard=True, one_time_keyboard=True, selective=True)

    welcome_text = (
      "👋 **ውድ ተማሪዎቻችን ሰላም!**\n\n"
"መልዕክት ለመላክ፣ ለመገናኘት ወይም ስለ Family Academy ጥያቄ ለመጠየቅ ከፈለጉ፣ "
"እዚህ በቀጥታ መጠየቅ ትችላላችሁ፣ እኛም **ወዲያውኑ** እንመልሳለን።\n\n"
"**እባክዎ ከታች ያለውን ምርጫ ይምረጡ።**"
    )

    # First message: Remove any lingering ReplyKeyboardMarkup
    await update.message.reply_text(
        "Loading menu...",
        reply_markup=remove_keyboard
    )
    # Second message: Send the actual menu with the InlineKeyboardMarkup
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
        # Note: The ConversationHandler entry point handles this.
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

    # 1. Direct Message Conversation Handler (MODIFIED)
    direct_message_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_direct_message, pattern='^START_DIRECT_MESSAGE$')],
        states={
            # State 99: ASK_PHONE_NUMBER - Accepts Contact object or text
            ASK_PHONE_NUMBER: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), get_phone_number)],
            # State 100: SEND_MESSAGE - Accepts text or photo
            SEND_MESSAGE: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, receive_direct_message)],
        },
        # Fallbacks to cancel the conversation
        fallbacks=[
            CallbackQueryHandler(cancel_direct_message, pattern='^GO_BACK_START$'), 
            CommandHandler('start', cancel_direct_message)
        ],
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
