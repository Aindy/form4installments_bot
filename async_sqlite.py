import aiosqlite
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

async def db_start():
    try:
        async with aiosqlite.connect('users.db') as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS profile(
                user_id TEXT PRIMARY KEY, 
                name TEXT, 
                surname TEXT, 
                middle_name TEXT, 
                city_of_registration TEXT, 
                city_of_residence TEXT, 
                phone_number TEXT, 
                passport_scans TEXT, 
                selfie_with_passport TEXT, 
                monthly_income TEXT, 
                employment_status TEXT, 
                organization_number TEXT, 
                guarantor_info TEXT, 
                guarantor_passport TEXT, 
                category_choice TEXT, 
                product_choice TEXT, 
                cost_product INTEGER, 
                installment_terms TEXT,
                status_check INTEGER DEFAULT 0,
                status_check_timestamp TEXT DEFAULT (datetime('now')),
                timestamp TEXT DEFAULT (datetime('now'))
            )
            """)
            await db.commit()
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")


async def create_profile(user_id):
    async with aiosqlite.connect('users.db') as db:
        try:
            user = await db.execute("""
            SELECT 1 FROM profile 
            WHERE user_id = ?""", (user_id,))
            user = await user.fetchone()

            if not user:
                await db.execute("""
                INSERT INTO profile (user_id, name, surname, middle_name, city_of_registration, city_of_residence, phone_number, passport_scans, selfie_with_passport, monthly_income, employment_status, organization_number, guarantor_info, guarantor_passport, category_choice, product_choice, cost_product, installment_terms, status_check)
                VALUES (?, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0)""",
                (user_id,))
                await db.commit()
                logger.info(f"Профиль успешно создан для пользователя: {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при создании профиля user_id {user_id}: {e}")


async def update_profile(data, user_id):
    async with aiosqlite.connect('users.db') as db:
        try:
            status_check = data.get('status_check', None)
            if status_check is not None:
                await db.execute("""
                UPDATE profile SET
                status_check = ?,
                status_check_timestamp = datetime('now')
                WHERE user_id = ?""", (
                    status_check,
                    user_id
                ))
            else:
                await db.execute("""
                UPDATE profile SET
                name = ?, 
                surname = ?, 
                middle_name = ?, 
                city_of_registration = ?, 
                city_of_residence = ?, 
                phone_number = ?, 
                passport_scans = ?, 
                selfie_with_passport = ?, 
                monthly_income = ?, 
                employment_status = ?, 
                organization_number = ?, 
                guarantor_info = ?, 
                guarantor_passport = ?, 
                category_choice = ?, 
                product_choice = ?, 
                cost_product = ?, 
                installment_terms = ?,
                timestamp = datetime('now')
                WHERE user_id = ?""", (
                    str(data['name']),
                    str(data['surname']),
                    str(data['middle_name']),
                    str(data['city_of_registration']),
                    str(data['city_of_residence']),
                    str(data['phone_number']),
                    str(data['passport_scans']),
                    str(data['selfie_with_passport']),
                    str(data['monthly_income']),
                    str(data['employment_status']),
                    str(data['organization_number']),
                    str(data['guarantor_info']),
                    str(data['guarantor_passport']),
                    str(data['category_choice']),
                    str(data['product_choice']),
                    str(data['cost_product']),
                    str(data['installment_terms']),
                    user_id
                ))
            await db.commit()
        except Exception as e:
            logger.error(f"Ошибка при обновлении профиля пользователя {user_id}: {e}")


async def update_profile_status(user_id, status_check):
    async with aiosqlite.connect('users.db') as db:
        await db.execute("""
        UPDATE profile SET status_check = ? WHERE user_id = ?
        """, (status_check, user_id))
        await db.commit()


async def get_status(user_id):
    async with aiosqlite.connect('users.db') as db:
        cursor = await db.execute("""
        SELECT * FROM profile WHERE user_id = ?
        """, (user_id,))
        return await cursor.fetchone()