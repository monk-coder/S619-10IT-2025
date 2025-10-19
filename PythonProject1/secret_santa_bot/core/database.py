import sqlite3
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_name='secret_santa.db'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Инициализация базы данных"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                # Пользователи
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        full_name TEXT,
                        bio TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Вишлисты
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS wishlists (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        item_name TEXT NOT NULL,
                        description TEXT,
                        photo_id TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')

                # Игры
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS games (
                        game_code TEXT PRIMARY KEY,
                        game_name TEXT NOT NULL,
                        organizer_id INTEGER,
                        draw_date TEXT,
                        min_participants INTEGER DEFAULT 3,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (organizer_id) REFERENCES users (user_id)
                    )
                ''')

                # Участники игр
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS game_participants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        game_code TEXT,
                        user_id INTEGER,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (game_code) REFERENCES games (game_code),
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        UNIQUE(game_code, user_id)
                    )
                ''')

                # Распределение пар
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS santa_pairs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        game_code TEXT,
                        santa_id INTEGER,
                        recipient_id INTEGER,
                        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (game_code) REFERENCES games (game_code),
                        FOREIGN KEY (santa_id) REFERENCES users (user_id),
                        FOREIGN KEY (recipient_id) REFERENCES users (user_id),
                        UNIQUE(game_code, santa_id)
                    )
                ''')

                # Анонимные сообщения
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS anonymous_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        game_code TEXT,
                        from_user_id INTEGER,
                        to_user_id INTEGER,
                        message_text TEXT NOT NULL,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_read BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (game_code) REFERENCES games (game_code),
                        FOREIGN KEY (from_user_id) REFERENCES users (user_id),
                        FOREIGN KEY (to_user_id) REFERENCES users (user_id)
                    )
                ''')

                conn.commit()
                logger.info("✅ База данных инициализирована")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise

    def add_user(self, user_id, username, full_name=None):
        """Добавление пользователя"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, username, full_name)
                    VALUES (?, ?, ?)
                ''', (user_id, username, full_name))
                conn.commit()
                logger.info(f"✅ Пользователь добавлен: {user_id}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка добавления пользователя {user_id}: {e}")
            return False

        def get_santa_pair(self, santa_id, game_code):
            """Получение пары Санта-Получатель для конкретной игры"""
            try:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT 
                            sp.recipient_id,
                            u.username,
                            u.full_name,
                            u.bio
                        FROM santa_pairs sp
                        JOIN users u ON sp.recipient_id = u.user_id
                        WHERE sp.santa_id = ? AND sp.game_code = ?
                    ''', (santa_id, game_code))
                    return cursor.fetchone()
            except Exception as e:
                logger.error(f"❌ Ошибка получения пары Санты: {e}")
                return None

        def get_recipient_wishlist(self, recipient_id):
            """Получение вишлиста получателя"""
            try:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT item_name, description, photo_id
                        FROM wishlists
                        WHERE user_id = ?
                        ORDER BY id
                    ''', (recipient_id,))
                    return cursor.fetchall()
            except Exception as e:
                logger.error(f"❌ Ошибка получения вишлиста: {e}")
                return []

        def can_view_recipient(self, user_id, game_code):
            """Проверка, может ли пользователь просматривать информацию о получателе"""
            try:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()

                    # Проверяем, была ли жеребьевка
                    cursor.execute('''
                        SELECT 1 FROM santa_pairs 
                        WHERE game_code = ? AND santa_id = ?
                    ''', (game_code, user_id))

                    return cursor.fetchone() is not None
            except Exception as e:
                logger.error(f"❌ Ошибка проверки доступа к получателю: {e}")
                return False

    def update_user_profile(self, user_id, full_name, bio):
        """Обновление профиля пользователя"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET full_name = ?, bio = ? 
                    WHERE user_id = ?
                ''', (full_name, bio, user_id))
                conn.commit()
                logger.info(f"✅ Профиль обновлен: {user_id}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка обновления профиля {user_id}: {e}")
            return False

    def get_user(self, user_id):
        """Получение пользователя"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                return cursor.fetchone()

        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователя {user_id}: {e}")
            return None

    def create_game(self, game_code, game_name, organizer_id, draw_date, min_participants=3):
        """Создание новой игры"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO games (game_code, game_name, organizer_id, draw_date, min_participants)
                    VALUES (?, ?, ?, ?, ?)
                ''', (game_code, game_name, organizer_id, draw_date, min_participants))
                conn.commit()
                logger.info(f"✅ Игра создана: {game_code}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка создания игры {game_code}: {e}")
            return False

    def join_game(self, game_code, user_id):
        """Присоединение пользователя к игре"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO game_participants (game_code, user_id)
                    VALUES (?, ?)
                ''', (game_code, user_id))
                conn.commit()
                logger.info(f"✅ Пользователь {user_id} присоединился к игре {game_code}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка присоединения пользователя {user_id} к игре {game_code}: {e}")
            return False

    def leave_game(self, game_code, user_id):
        """Выход пользователя из игры"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                # Проверяем, является ли пользователь организатором
                cursor.execute('SELECT organizer_id FROM games WHERE game_code = ?', (game_code,))
                game = cursor.fetchone()

                if game and game[0] == user_id:
                    # Пользователь организатор - нельзя выйти
                    return "organizer"

                # Удаляем пользователя из участников
                cursor.execute('''
                    DELETE FROM game_participants 
                    WHERE game_code = ? AND user_id = ?
                ''', (game_code, user_id))

                # Проверяем, удалилась ли запись
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"✅ Пользователь {user_id} вышел из игры {game_code}")
                    return "success"
                else:
                    return "not_found"

        except Exception as e:
            logger.error(f"❌ Ошибка выхода пользователя {user_id} из игры {game_code}: {e}")
            return "error"

    def get_user_active_games(self, user_id):
        """Получение активных игр пользователя с детальной информацией"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT g.game_code, g.game_name, g.draw_date, 
                           COUNT(gp.user_id) as participant_count,
                           g.organizer_id,
                           EXISTS(SELECT 1 FROM santa_pairs WHERE game_code = g.game_code) as is_drawn
                    FROM game_participants gp
                    JOIN games g ON gp.game_code = g.game_code
                    WHERE gp.user_id = ? AND g.is_active = TRUE
                    GROUP BY g.game_code, g.game_name, g.draw_date, g.organizer_id
                ''', (user_id,))
                return cursor.fetchall()

        except Exception as e:
            logger.error(f"❌ Ошибка получения игр пользователя {user_id}: {e}")
            return []

    def is_game_drawn(self, game_code):
        """Проверка, была ли уже проведена жеребьёвка"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 1 FROM santa_pairs WHERE game_code = ?
                ''', (game_code,))
                return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"❌ Ошибка проверки жеребьёвки игры {game_code}: {e}")
            return False

    def get_game_participants_details(self, game_code):
        """Получение детальной информации об участниках игры"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        u.user_id,
                        u.username,
                        u.full_name,
                        u.bio,
                        COUNT(w.id) as wishlist_count,
                        (SELECT COUNT(*) FROM wishlists WHERE user_id = u.user_id) as total_wishlist_items
                    FROM game_participants gp
                    JOIN users u ON gp.user_id = u.user_id
                    LEFT JOIN wishlists w ON u.user_id = w.user_id
                    WHERE gp.game_code = ?
                    GROUP BY u.user_id, u.username, u.full_name, u.bio
                    ORDER BY u.full_name
                ''', (game_code,))
                return cursor.fetchall()

        except Exception as e:
            logger.error(f"❌ Ошибка получения участников игры {game_code}: {e}")
            return []

    def get_game_info(self, game_code):
        """Получение информации об игре"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        game_name, 
                        organizer_id,
                        draw_date,
                        min_participants,
                        (SELECT COUNT(*) FROM game_participants WHERE game_code = ?) as current_participants
                    FROM games 
                    WHERE game_code = ?
                ''', (game_code, game_code))
                return cursor.fetchone()

        except Exception as e:
            logger.error(f"❌ Ошибка получения информации об игре {game_code}: {e}")
            return None

    def get_participants_count(self, game_code):
        """Получение количества участников игры"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM game_participants 
                    WHERE game_code = ?
                ''', (game_code,))
                result = cursor.fetchone()
                return result[0] if result else 0

        except Exception as e:
            logger.error(f"❌ Ошибка получения количества участников игры {game_code}: {e}")
            return 0

    def is_user_in_game(self, user_id, game_code):
        """Проверка, участвует ли пользователь в игре"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 1 FROM game_participants 
                    WHERE user_id = ? AND game_code = ?
                ''', (user_id, game_code))
                return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"❌ Ошибка проверки участия пользователя {user_id} в игре {game_code}: {e}")
            return False

    def is_game_organizer(self, game_code, user_id):
        """Проверка, является ли пользователь организатором игры"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 1 FROM games 
                    WHERE game_code = ? AND organizer_id = ?
                ''', (game_code, user_id))
                return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"❌ Ошибка проверки организатора игры {game_code}: {e}")
            return False

    def get_game_participants_ids(self, game_code):
        """Получение ID участников игры"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id FROM game_participants 
                    WHERE game_code = ?
                ''', (game_code,))
                return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"❌ Ошибка получения ID участников игры {game_code}: {e}")
            return []

    def assign_santa_pairs(self, game_code, pairs):
        """Сохранение распределенных пар Санта-Получатель"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                # Удаляем старые пары для этой игры
                cursor.execute('DELETE FROM santa_pairs WHERE game_code = ?', (game_code,))

                # Сохраняем новые пары
                for santa_id, recipient_id in pairs:
                    cursor.execute('''
                        INSERT INTO santa_pairs (game_code, santa_id, recipient_id)
                        VALUES (?, ?, ?)
                    ''', (game_code, santa_id, recipient_id))

                conn.commit()
                logger.info(f"✅ Пары распределены для игры {game_code}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка распределения пар для игры {game_code}: {e}")
            return False

    def get_recipient_info(self, santa_id, game_code):
        """Получение информации о получателе для Санты"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                # Получаем информацию о получателе
                cursor.execute('''
                    SELECT u.full_name, u.bio
                    FROM santa_pairs sp
                    JOIN users u ON sp.recipient_id = u.user_id
                    WHERE sp.santa_id = ? AND sp.game_code = ?
                ''', (santa_id, game_code))
                recipient_info = cursor.fetchone()

                if not recipient_info:
                    return None, []

                # Получаем вишлист получателя
                cursor.execute('''
                    SELECT item_name, description, photo_id
                    FROM wishlists
                    WHERE user_id = (
                        SELECT recipient_id FROM santa_pairs 
                        WHERE santa_id = ? AND game_code = ?
                    )
                ''', (santa_id, game_code))
                wishlist = cursor.fetchall()

                return recipient_info, wishlist

        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о получателе: {e}")
            return None, []

    # === МЕТОДЫ ДЛЯ АНОНИМНЫХ СООБЩЕНИЙ ===

    def add_anonymous_message(self, game_code, from_user_id, to_user_id, message_text):
        """Добавление анонимного сообщения"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO anonymous_messages (game_code, from_user_id, to_user_id, message_text)
                    VALUES (?, ?, ?, ?)
                ''', (game_code, from_user_id, to_user_id, message_text))
                conn.commit()
                logger.info(f"✅ Анонимное сообщение добавлено от {from_user_id} к {to_user_id}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка добавления анонимного сообщения: {e}")
            return False

    def get_recipient_for_santa(self, santa_id, game_code):
        """Получение ID получателя для Санты"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT recipient_id 
                    FROM santa_pairs 
                    WHERE santa_id = ? AND game_code = ?
                ''', (santa_id, game_code))
                result = cursor.fetchone()
                return result[0] if result else None

        except Exception as e:
            logger.error(f"❌ Ошибка получения получателя для Санты {santa_id}: {e}")
            return None

    def get_unread_messages_count(self, user_id, game_code=None):
        """Получение количества непрочитанных сообщений"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                if game_code:
                    cursor.execute('''
                        SELECT COUNT(*) 
                        FROM anonymous_messages 
                        WHERE to_user_id = ? AND game_code = ? AND is_read = FALSE
                    ''', (user_id, game_code))
                else:
                    cursor.execute('''
                        SELECT COUNT(*) 
                        FROM anonymous_messages 
                        WHERE to_user_id = ? AND is_read = FALSE
                    ''', (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 0

        except Exception as e:
            logger.error(f"❌ Ошибка получения количества непрочитанных сообщений: {e}")
            return 0

    def get_unread_messages(self, user_id, game_code=None):
        """Получение непрочитанных сообщений"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                if game_code:
                    cursor.execute('''
                        SELECT id, message_text, sent_at, game_code
                        FROM anonymous_messages 
                        WHERE to_user_id = ? AND game_code = ? AND is_read = FALSE
                        ORDER BY sent_at
                    ''', (user_id, game_code))
                else:
                    cursor.execute('''
                        SELECT id, message_text, sent_at, game_code
                        FROM anonymous_messages 
                        WHERE to_user_id = ? AND is_read = FALSE
                        ORDER BY sent_at
                    ''', (user_id,))
                return cursor.fetchall()

        except Exception as e:
            logger.error(f"❌ Ошибка получения непрочитанных сообщений: {e}")
            return []

    def mark_message_as_read(self, message_id):
        """Пометить сообщение как прочитанное"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE anonymous_messages 
                    SET is_read = TRUE 
                    WHERE id = ?
                ''', (message_id,))
                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"❌ Ошибка отметки сообщения как прочитанного: {e}")
            return False

    def can_send_message(self, from_user_id, to_user_id, game_code):
        """Проверка, может ли пользователь отправить сообщение получателю"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                # Проверяем, что from_user_id - это Санта для to_user_id
                cursor.execute('''
                    SELECT 1 
                    FROM santa_pairs 
                    WHERE santa_id = ? AND recipient_id = ? AND game_code = ?
                ''', (from_user_id, to_user_id, game_code))

                return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"❌ Ошибка проверки возможности отправки сообщения: {e}")
            return False