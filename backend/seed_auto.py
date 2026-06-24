"""
Seed data for BuyAnywhere Auto: an admin user, a test customer, and ~12 vehicles.

Run from /app/backend:  python seed_auto.py
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).parent / ".env")

from models.auto import (
    AutoCountry,
    AutoImageRights,
    AutoListingType,
    AutoVehicle,
    AutoVehicleStatus,
    AutoDeposit,
    AutoDepositMethod,
    AutoDepositStatus,
)
from models.user import User, UserRole, CustomerInfo
from services.auth_service import AuthService

VEHICLES = [
    # --- NZ auction ---
    {
        "country": "NZ", "listing_type": "auction", "source": "ManheimNZ",
        "title_original": "2017 Toyota Aqua S Hybrid",
        "title_ru": "Toyota Aqua S Hybrid 2017",
        "make": "Toyota", "model": "Aqua", "year": 2017, "mileage_km": 78000,
        "engine": "1.5L Hybrid", "fuel": "Гибрид", "transmission": "Автомат", "body_type": "Хэтчбек",
        "location": "Окленд", "condition": "Хорошее", "damage_type": "Без повреждений",
        "current_price_nzd": 8200.0, "buy_now_price_nzd": 9500.0,
        "auction_offset_hours": 36,
        "images": ["https://images.unsplash.com/photo-1549924231-f129b911e442?w=900",
                   "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=900"],
        "ai_summary_ru": "Экономичный гибрид с пробегом 78 000 км в хорошем состоянии. Подходит для города.",
        "ai_risk_summary_ru": "Двигатель и гибридная батарея — низкий риск при подтверждённом сервисе. Каркас целый. Уровень осторожности: низкий.",
    },
    {
        "country": "NZ", "listing_type": "auction", "source": "PicklesNZ",
        "title_original": "2014 Mazda CX-5 GSX AWD",
        "title_ru": "Mazda CX-5 GSX AWD 2014",
        "make": "Mazda", "model": "CX-5", "year": 2014, "mileage_km": 132000,
        "engine": "2.5L бензин", "fuel": "Бензин", "transmission": "Автомат", "body_type": "Кроссовер",
        "location": "Веллингтон", "condition": "Хорошее", "damage_type": "Без повреждений",
        "current_price_nzd": 11500.0,
        "auction_offset_hours": 18,
        "images": ["https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=900"],
        "ai_summary_ru": "Полноприводный кроссовер для семейных поездок и зимних дорог.",
        "ai_risk_summary_ru": "Двигатель: низкий риск. Коробка: средний риск из-за пробега. Затопления нет. Каркас: целый. Уровень осторожности: средний.",
    },
    {
        "country": "NZ", "listing_type": "auction", "source": "TurnersNZ",
        "title_original": "2012 Subaru Legacy 2.5i Wagon — flood damage",
        "title_ru": "Subaru Legacy 2.5i Wagon 2012 — после затопления",
        "make": "Subaru", "model": "Legacy", "year": 2012, "mileage_km": 165000,
        "engine": "2.5L бензин", "fuel": "Бензин", "transmission": "Вариатор", "body_type": "Универсал",
        "location": "Крайстчерч", "condition": "Повреждённое", "damage_type": "Затопление",
        "current_price_nzd": 3400.0,
        "auction_offset_hours": 12,
        "images": ["https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=900"],
        "ai_summary_ru": "Универсал после затопления. Может подойти как донор или для восстановления опытным механиком.",
        "ai_risk_summary_ru": "Затопление — высокий риск электрики и салона. Двигатель: средний риск. Коробка: высокий риск. Уровень осторожности: высокий. Подходит для разбора на запчасти.",
    },
    {
        "country": "NZ", "listing_type": "auction", "source": "ManheimNZ",
        "title_original": "2016 Nissan Leaf 30kWh",
        "title_ru": "Nissan Leaf 30 кВт·ч 2016",
        "make": "Nissan", "model": "Leaf", "year": 2016, "mileage_km": 64000,
        "engine": "Электро 30 кВт·ч", "fuel": "Электро", "transmission": "Автомат", "body_type": "Хэтчбек",
        "location": "Окленд", "condition": "Хорошее", "damage_type": "Без повреждений",
        "current_price_nzd": 9700.0,
        "auction_offset_hours": 50,
        "images": ["https://images.unsplash.com/photo-1593941707874-ef25b8b4a92b?w=900"],
        "ai_summary_ru": "Электрокар с батареей 30 кВт·ч. Подходит для города; запас хода зависит от состояния батареи.",
        "ai_risk_summary_ru": "Двигатель электро: низкий риск. Состояние батареи — критический фактор, требует проверки SOH. Уровень осторожности: средний.",
    },
    {
        "country": "NZ", "listing_type": "auction", "source": "TurnersNZ",
        "title_original": "2015 Ford Ranger XLT 3.2 4WD",
        "title_ru": "Ford Ranger XLT 3.2 4WD 2015",
        "make": "Ford", "model": "Ranger", "year": 2015, "mileage_km": 195000,
        "engine": "3.2L дизель", "fuel": "Дизель", "transmission": "Автомат", "body_type": "Пикап",
        "location": "Окленд", "condition": "Удовлетворительное", "damage_type": "Без повреждений",
        "current_price_nzd": 18500.0,
        "auction_offset_hours": 72,
        "images": ["https://images.unsplash.com/photo-1567808291548-fc3ee04dbcf0?w=900"],
        "ai_summary_ru": "Полноразмерный пикап для работы и дальних поездок.",
        "ai_risk_summary_ru": "Двигатель 3.2L дизель: исторически возможен EGR/турбо — средний риск. Коробка: средний риск. Уровень осторожности: средний.",
    },
    {
        "country": "NZ", "listing_type": "fixed_price", "source": "DealerAuckland",
        "title_original": "2019 Honda Fit Hybrid",
        "title_ru": "Honda Fit Hybrid 2019",
        "make": "Honda", "model": "Fit", "year": 2019, "mileage_km": 43000,
        "engine": "1.5L Hybrid", "fuel": "Гибрид", "transmission": "Автомат", "body_type": "Хэтчбек",
        "location": "Окленд", "condition": "Отличное", "damage_type": "Без повреждений",
        "current_price_nzd": 14900.0, "buy_now_price_nzd": 14900.0,
        "images": ["https://images.unsplash.com/photo-1610647752706-3bb12232b3ab?w=900"],
        "ai_summary_ru": "Компактный гибрид с малым пробегом в отличном состоянии.",
        "ai_risk_summary_ru": "Низкий риск по всем узлам. Уровень осторожности: низкий.",
    },
    {
        "country": "NZ", "listing_type": "auction", "source": "PicklesNZ",
        "title_original": "2010 BMW 320i E90 — airbag deployed",
        "title_ru": "BMW 320i E90 2010 — сработали подушки",
        "make": "BMW", "model": "320i", "year": 2010, "mileage_km": 178000,
        "engine": "2.0L бензин", "fuel": "Бензин", "transmission": "Автомат", "body_type": "Седан",
        "location": "Гамильтон", "condition": "Повреждённое", "damage_type": "Передний удар",
        "current_price_nzd": 2600.0,
        "auction_offset_hours": 6,
        "images": ["https://images.unsplash.com/photo-1502877338535-766e1452684a?w=900"],
        "ai_summary_ru": "Седан после фронтального удара со сработавшими подушками. Возможна сложная реставрация или донор.",
        "ai_risk_summary_ru": "Подушки/каркас: высокий риск. Двигатель: возможно цел — средний риск. Коробка: средний риск. Уровень осторожности: высокий. Подходит для запчастей.",
    },
    {
        "country": "NZ", "listing_type": "auction", "source": "ManheimNZ",
        "title_original": "2013 Toyota Hiace Van 2.7L",
        "title_ru": "Toyota Hiace 2.7L 2013",
        "make": "Toyota", "model": "Hiace", "year": 2013, "mileage_km": 220000,
        "engine": "2.7L бензин", "fuel": "Бензин", "transmission": "Автомат", "body_type": "Фургон",
        "location": "Окленд", "condition": "Хорошее", "damage_type": "Без повреждений",
        "current_price_nzd": 15400.0,
        "auction_offset_hours": 96,
        "images": ["https://images.unsplash.com/photo-1597009622933-ffeefbc4b51a?w=900"],
        "ai_summary_ru": "Надёжный коммерческий фургон. Подходит для бизнеса и переоборудования.",
        "ai_risk_summary_ru": "Двигатель: низкий риск. Коробка: средний риск из-за пробега. Уровень осторожности: средний.",
    },
    {
        "country": "NZ", "listing_type": "auction", "source": "TurnersNZ",
        "title_original": "2008 Lexus IS250 — donor",
        "title_ru": "Lexus IS250 2008 — донор",
        "make": "Lexus", "model": "IS250", "year": 2008, "mileage_km": 240000,
        "engine": "2.5L бензин", "fuel": "Бензин", "transmission": "Автомат", "body_type": "Седан",
        "location": "Веллингтон", "condition": "На запчасти", "damage_type": "Двигатель",
        "current_price_nzd": 1800.0,
        "auction_offset_hours": 8,
        "images": ["https://images.unsplash.com/photo-1542362567-b07e54358753?w=900"],
        "ai_summary_ru": "Машина на запчасти. Подходит для разбора и продажи компонентов.",
        "ai_risk_summary_ru": "Двигатель: высокий риск (заявлен дефект). Коробка: неизвестно — средний риск. Уровень осторожности: высокий. Только как донор.",
    },
    # --- AU inquiry-only ---
    {
        "country": "AU", "listing_type": "inquiry_only", "source": "Pickles AU",
        "title_original": "2018 Holden Commodore VXR",
        "title_ru": "Holden Commodore VXR 2018",
        "make": "Holden", "model": "Commodore VXR", "year": 2018, "mileage_km": 89000,
        "engine": "3.6L V6", "fuel": "Бензин", "transmission": "Автомат", "body_type": "Седан",
        "location": "Сидней", "condition": "Хорошее", "damage_type": "Без повреждений",
        "current_price_nzd": 22500.0,
        "images": ["https://images.unsplash.com/photo-1542228262-3d663b306a53?w=900"],
        "ai_summary_ru": "Австралийский седан премиум-сегмента. Доступен по запросу.",
        "ai_risk_summary_ru": "Двигатель/коробка: низкий риск. Уровень осторожности: низкий.",
    },
    {
        "country": "AU", "listing_type": "inquiry_only", "source": "Manheim AU",
        "title_original": "2016 Ford Falcon XR6",
        "title_ru": "Ford Falcon XR6 2016",
        "make": "Ford", "model": "Falcon XR6", "year": 2016, "mileage_km": 112000,
        "engine": "4.0L I6", "fuel": "Бензин", "transmission": "Автомат", "body_type": "Седан",
        "location": "Мельбурн", "condition": "Хорошее", "damage_type": "Без повреждений",
        "current_price_nzd": 19800.0,
        "images": ["https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=900"],
        "ai_summary_ru": "Спортивный седан с шестицилиндровым мотором. Только по запросу.",
        "ai_risk_summary_ru": "Двигатель: низкий риск. Коробка: средний риск. Уровень осторожности: средний.",
    },
    {
        "country": "AU", "listing_type": "inquiry_only", "source": "Pickles AU",
        "title_original": "2014 Toyota Hilux SR5 4x4",
        "title_ru": "Toyota Hilux SR5 4x4 2014",
        "make": "Toyota", "model": "Hilux", "year": 2014, "mileage_km": 175000,
        "engine": "3.0L дизель", "fuel": "Дизель", "transmission": "Механика", "body_type": "Пикап",
        "location": "Брисбен", "condition": "Удовлетворительное", "damage_type": "Без повреждений",
        "current_price_nzd": 24500.0,
        "images": ["https://images.unsplash.com/photo-1605559424843-9e4c228bf1c2?w=900"],
        "ai_summary_ru": "Дизельный пикап для тяжёлой работы. Доступ по запросу.",
        "ai_risk_summary_ru": "Двигатель 3.0L дизель: исторически возможны проблемы с поршневой — средний риск. Уровень осторожности: средний.",
    },
]


async def main() -> None:
    mongo_url = os.environ["MONGO_URL"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ["DB_NAME"]]
    auth = AuthService()

    # --- admin ---
    admin_email = "admin@buyanywhere.com"
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        admin = User(
            email=admin_email,
            phone="+79135533369",
            password_hash=auth.hash_password("admin12345"),
            role=UserRole.ADMIN,
            customer_info=CustomerInfo(first_name="BuyAnywhere", last_name="Admin",
                                       phone="+79135533369", email=admin_email),
        )
        await db.users.insert_one(admin.dict())
        print(f"Created admin: {admin_email} / admin12345")
    else:
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {
                "role": UserRole.ADMIN.value,
                "password_hash": auth.hash_password("admin12345"),
            }},
        )
        print(f"Updated admin password: {admin_email} / admin12345")

    # --- demo customer ---
    customer_email = "client@buyanywhere.com"
    existing = await db.users.find_one({"email": customer_email})
    if not existing:
        cust = User(
            email=customer_email,
            phone="+79991112233",
            password_hash=auth.hash_password("client12345"),
            role=UserRole.CUSTOMER,
            customer_info=CustomerInfo(first_name="Иван", last_name="Петров",
                                       phone="+79991112233", email=customer_email),
        )
        await db.users.insert_one(cust.dict())
        customer_id = cust.id
        # Pre-verified deposit so the demo user can bid immediately
        deposit = AutoDeposit(
            user_id=customer_id, amount=1000.0, currency="NZD",
            method=AutoDepositMethod.BANK_TRANSFER, status=AutoDepositStatus.VERIFIED,
            payment_proof_note="Seed deposit",
        )
        await db.auto_deposits.insert_one(deposit.dict())
        print(f"Created customer: {customer_email} / client12345 (deposit verified)")
    else:
        customer_id = existing["id"]
        await db.users.update_one(
            {"email": customer_email},
            {"$set": {"password_hash": auth.hash_password("client12345")}},
        )
        print(f"Updated customer password: {customer_email} / client12345")

    # --- second customer (no deposit) ---
    customer2_email = "client2@buyanywhere.com"
    existing2 = await db.users.find_one({"email": customer2_email})
    if not existing2:
        c2 = User(
            email=customer2_email,
            phone="+79991112244",
            password_hash=auth.hash_password("client12345"),
            role=UserRole.CUSTOMER,
            customer_info=CustomerInfo(first_name="Анна", last_name="Сидорова",
                                       phone="+79991112244", email=customer2_email),
        )
        await db.users.insert_one(c2.dict())
        print(f"Created customer: {customer2_email} / client12345 (no deposit)")

    # --- vehicles ---
    inserted = 0
    for v in VEHICLES:
        # idempotency: match by source + title_original
        key = {"source": v["source"], "title_original": v.get("title_original")}
        existing_v = await db.auto_vehicles.find_one(key)
        if existing_v:
            continue
        vehicle = AutoVehicle(
            source=v["source"],
            country=AutoCountry(v["country"]),
            listing_type=AutoListingType(v["listing_type"]),
            title_original=v.get("title_original"),
            title_ru=v.get("title_ru") or "Автомобиль",
            description_original=v.get("description_original"),
            description_ru=v.get("description_ru"),
            make=v.get("make"), model=v.get("model"), year=v.get("year"),
            mileage_km=v.get("mileage_km"), engine=v.get("engine"), fuel=v.get("fuel"),
            transmission=v.get("transmission"), body_type=v.get("body_type"),
            location=v.get("location"), condition=v.get("condition"),
            damage_type=v.get("damage_type"),
            current_price_nzd=v.get("current_price_nzd"),
            buy_now_price_nzd=v.get("buy_now_price_nzd"),
            status=AutoVehicleStatus.AVAILABLE,
            images=v.get("images") or [],
            image_rights_status=AutoImageRights.SOURCE_PREVIEW,
            auction_end_time=(datetime.utcnow() + timedelta(hours=v["auction_offset_hours"]))
            if v.get("auction_offset_hours") else None,
            ai_summary_ru=v.get("ai_summary_ru"),
            ai_risk_summary_ru=v.get("ai_risk_summary_ru"),
        )
        # estimated_total
        if vehicle.current_price_nzd:
            from services.auto_service import calculate_price_breakdown
            vehicle.estimated_total_nzd = calculate_price_breakdown(vehicle.current_price_nzd)["total_nzd"]
        await db.auto_vehicles.insert_one(vehicle.dict())
        inserted += 1
    print(f"Inserted {inserted} new vehicles (total in DB: {await db.auto_vehicles.count_documents({})}).")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
