import json
import os
import time

DB_FILE = 'products.json'

# Oddiy kesh — har 60 soniyada bir marta faylni o'qiydi
_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 60  # soniya


def load_products():
    """Mahsulotlarni kesh orqali yuklaydi."""
    global _cache
    now = time.time()
    if _cache["data"] is not None and (now - _cache["timestamp"]) < CACHE_TTL:
        return _cache["data"]

    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    _cache = {"data": data, "timestamp": now}
    return data


def get_all_products_info():
    """Barcha mahsulotlar haqida qisqacha ma'lumot beradi."""
    products = load_products()
    if not products:
        return "Hozircha mahsulotlar yo'q."

    info = "Do'konimizdagi mahsulotlar:\n"
    for p in products:
        info += f"- {p['name']} (Narxi: {p['price']})\n"
    return info


def search_product(query):
    """Qidiruv so'ziga ko'ra mahsulot topib ma'lumot beradi."""
    products = load_products()
    query = query.lower()

    results = []
    for p in products:
        if query in p['name'].lower() or query in p['description'].lower():
            results.append(
                f"Mahsulot: {p['name']}\nNarxi: {p['price']}\nMa'lumot: {p['description']}"
            )

    if results:
        return "\n\n".join(results)
    return "Kechirasiz, bunday mahsulot topilmadi."
