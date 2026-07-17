import asyncio
import logging
import os
from collections import defaultdict

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from dotenv import load_dotenv

import database
from agent import get_agent_response

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Har bir foydalanuvchining suhbat tarixi
conversation_history = defaultdict(list)
MAX_HISTORY = 20


# ── Inline klaviaturalar ──────────────────────────────────────────────────

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Bosh menyu — bot xabari tagiga yopishadi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Mahsulotlar", callback_data="show_products"),
            InlineKeyboardButton(text="Narxlar", callback_data="show_prices"),
        ],
        [
            InlineKeyboardButton(text="Maslahat olish", callback_data="consult"),
            InlineKeyboardButton(text="Yordam", callback_data="help"),
        ],
    ])


def products_list_keyboard() -> InlineKeyboardMarkup:
    """Mahsulotlar ro'yxati."""
    products = database.load_products()
    buttons = []
    for p in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"{p['name']} — {p['price']}",
                callback_data=f"product_{p['id']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="Bosh menyu", callback_data="back_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Mahsulot detail sahifasi tugmalari."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Buyurtma berish", callback_data=f"order_{product_id}")],
        [InlineKeyboardButton(text="Barcha mahsulotlar", callback_data="show_products")],
        [InlineKeyboardButton(text="Bosh menyu", callback_data="back_main")],
    ])


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Faqat bosh menyu tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Bosh menyu", callback_data="back_main")]
    ])


# ── /start ────────────────────────────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    conversation_history[message.chat.id].clear()
    # Avval pastki klaviaturani olib tashlaymiz (ReplyKeyboardRemove)
    await message.answer("Xush kelibsiz!", reply_markup=ReplyKeyboardRemove())
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "Men Abdulloh — do'konimizning virtual maslahatchisiman.\n"
        "Nima haqida bilmoqchisiz?",
        reply_markup=main_menu_keyboard()
    )


# ── /help ─────────────────────────────────────────────────────────────────
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Abdulloh Bot — Yordam\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=main_menu_keyboard()
    )


# ── Callback: Bosh menyu ──────────────────────────────────────────────────
@dp.callback_query(F.data == "back_main")
async def cb_back_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Bosh menyu. Nima haqida bilmoqchisiz?",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


# ── Callback: Mahsulotlar ro'yxati ───────────────────────────────────────
@dp.callback_query(F.data == "show_products")
async def cb_show_products(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Bizning mahsulotlarimiz — birini tanlang:",
        reply_markup=products_list_keyboard()
    )
    await callback.answer()


# ── Callback: Narxlar ────────────────────────────────────────────────────
@dp.callback_query(F.data == "show_prices")
async def cb_show_prices(callback: types.CallbackQuery):
    products = database.load_products()
    if not products:
        await callback.answer("Hozircha mahsulotlar yo'q!", show_alert=True)
        return

    text = "Narxlar jadvali:\n\n"
    for p in products:
        text += f"  {p['name']}: {p['price']}\n"

    await callback.message.edit_text(
        text,
        reply_markup=back_to_main_keyboard()
    )
    await callback.answer()


# ── Callback: Maslahat olish ─────────────────────────────────────────────
@dp.callback_query(F.data == "consult")
async def cb_consult(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Abdulloh quloq solmoqda!\n\n"
        "Qaysi mahsulot haqida savolingiz bor? Yozing:",
        reply_markup=back_to_main_keyboard()
    )
    await callback.answer()


# ── Callback: Yordam ──────────────────────────────────────────────────────
@dp.callback_query(F.data == "help")
async def cb_help(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Abdulloh Bot — Yordam\n\n"
        "Nima qila olaman:\n"
        "  Mahsulotlar — barcha mahsulotlar ro'yxati\n"
        "  Narxlar — narxlar jadvali\n"
        "  Maslahat olish — savol-javob rejimi\n\n"
        "Yoki shunchaki savolingizni yozing, men javob beraman!",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


# ── Callback: Mahsulot detail ─────────────────────────────────────────────
@dp.callback_query(F.data.startswith("product_"))
async def cb_product_detail(callback: types.CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    products = database.load_products()
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        await callback.answer("Mahsulot topilmadi!", show_alert=True)
        return

    text = (
        f"Mahsulot: {product['name']}\n"
        f"Narxi:    {product['price']}\n\n"
        f"{product['description']}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=product_detail_keyboard(product_id)
    )
    await callback.answer()


# ── Callback: Buyurtma ───────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("order_"))
async def cb_order(callback: types.CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    products = database.load_products()
    product = next((p for p in products if p["id"] == product_id), None)
    name = product["name"] if product else "Mahsulot"

    await callback.message.edit_text(
        f"Buyurtmangiz qabul qilindi!\n\n"
        f"Mahsulot: {name}\n\n"
        f"Tez orada menejerimiz siz bilan bog'lanadi.",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer("Buyurtma yuborildi!")


# ── Matn xabarlari (AI javob) ─────────────────────────────────────────────
@dp.message(F.text)
async def handle_text_message(message: types.Message):
    user_text = message.text
    chat_id = message.chat.id

    processing_msg = await message.answer("Abdulloh o'ylamoqda...")
    history = list(conversation_history[chat_id])

    agent_reply = await get_agent_response(user_text, history)

    conversation_history[chat_id].append({"role": "user", "content": user_text})
    conversation_history[chat_id].append({"role": "assistant", "content": agent_reply})

    if len(conversation_history[chat_id]) > MAX_HISTORY:
        conversation_history[chat_id] = conversation_history[chat_id][-MAX_HISTORY:]

    # AI javobi tagiga ham bosh menyu tugmasini qo'shamiz
    await processing_msg.edit_text(
        agent_reply,
        reply_markup=main_menu_keyboard()
    )


# ── Matn bo'lmagan xabarlar ───────────────────────────────────────────────
@dp.message()
async def handle_non_text(message: types.Message):
    await message.answer(
        "Iltimos, faqat matn yuboring.\n"
        "Mahsulot haqida savolingizni yozing!",
        reply_markup=main_menu_keyboard()
    )


# ── Main ─────────────────────────────────────────────────────────────────
async def main():
    if not TELEGRAM_BOT_TOKEN:
        logging.error("[XATO] Telegram bot tokeni topilmadi!")
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    print("[OK] Abdulloh bot ishga tushmoqda...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
