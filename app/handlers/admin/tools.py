"""Admin yordamchi vositalari — media file_id olish.

Admin botga video/animatsiya/rasm yuborsa, bot uning file_id sini qaytaradi.
Bu file_id ni .env dagi PRODUCT_VIDEO_FILE_ID ga qo'yish uchun ishlatiladi.
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router(name="admin_tools")


@router.message(F.video)
async def on_video(message: Message, state: FSMContext) -> None:
    # FSM holatida bo'lmaganda ishlaydi (kod/bonus qo'shish jarayonini buzmaydi)
    if await state.get_state() is not None:
        return
    file_id = message.video.file_id
    await message.answer(
        "🎬 Video qabul qilindi.\n\n"
        "Quyidagi <b>file_id</b> ni .env dagi <code>PRODUCT_VIDEO_FILE_ID</code> ga qo'ying:\n\n"
        f"<code>{file_id}</code>\n\n"
        "Keyin botni qayta ishga tushiring: <code>docker compose up -d --build</code>"
    )


@router.message(F.animation)
async def on_animation(message: Message, state: FSMContext) -> None:
    if await state.get_state() is not None:
        return
    await message.answer(
        f"GIF/animatsiya file_id:\n\n<code>{message.animation.file_id}</code>"
    )


@router.message(F.document)
async def on_document(message: Message, state: FSMContext) -> None:
    if await state.get_state() is not None:
        return
    await message.answer(
        f"Hujjat file_id:\n\n<code>{message.document.file_id}</code>"
    )
