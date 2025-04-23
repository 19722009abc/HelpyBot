import logging
import datetime
import random
import sqlite3
import time

# Configuração do logger
logger = logging.getLogger("CartoonBot")

# Vamos mudar para usar SQLite ao invés de PostgreSQL
# Isso eliminará os problemas de SSL connection e instabilidade de conexão remota

# Caminho para o banco de dados SQLite
DB_PATH = 'database.db'

def init_db():
    """Inicializa o banco de dados SQLite com as tabelas necessárias"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Criar tabela de usuários se não existir
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            coins INTEGER DEFAULT 0,
            is_premium INTEGER DEFAULT 0,
            premium_until TIMESTAMP,
            last_daily TIMESTAMP,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            messages_count INTEGER DEFAULT 0,
            last_message_time TIMESTAMP,
            coin_limit INTEGER DEFAULT 100000,
            inventory_capacity INTEGER DEFAULT 20,
            premium_tier INTEGER DEFAULT 0
        )
        ''')

        # Criar tabela de transações se não existir
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')

        # Criar tabela de itens da loja
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS shop_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price INTEGER NOT NULL,
            type TEXT NOT NULL,
            effect TEXT NOT NULL,
            effect_value REAL NOT NULL,
            image_url TEXT,
            is_active INTEGER DEFAULT 1,
            premium INTEGER DEFAULT 0,
            rarity TEXT DEFAULT 'comum'
        )
        ''')

        # Criar tabela de inventário do usuário
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            expiry_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (item_id) REFERENCES shop_items(id)
        )
        ''')

        # Criar tabela para loja diária com itens em promoção
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_shop (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            discount_percent INTEGER DEFAULT 10,
            expiration_date TIMESTAMP NOT NULL,
            FOREIGN KEY (item_id) REFERENCES shop_items(id)
        )
        ''')

        # Criar tabela de fragmentos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fragments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            fragment_type TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')

        # Criar tabela de receitas para crafting
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crafting_recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            result_item_id INTEGER,
            common_fragments INTEGER DEFAULT 0,
            uncommon_fragments INTEGER DEFAULT 0,
            rare_fragments INTEGER DEFAULT 0,
            epic_fragments INTEGER DEFAULT 0,
            legendary_fragments INTEGER DEFAULT 0,
            coins_cost INTEGER DEFAULT 0,
            FOREIGN KEY (result_item_id) REFERENCES shop_items(id)
        )
        ''')

        conn.commit()
        cursor.close()
        conn.close()

        # Inicializar itens da loja
        ShopService.initialize_default_items()

        # Inicializar receitas de crafting
        ShopService.initialize_default_recipes()

        logger.info("Banco de dados SQLite inicializado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados SQLite: {e}")
        return False

def get_db():
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            conn = sqlite3.connect('database.db', timeout=20.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            return conn
        except sqlite3.OperationalError:
            if attempt == max_attempts - 1:
                raise
            time.sleep(1)

# Classe de serviço para operações de usuário
class UserService:
    @staticmethod
    def get_user(user_id):
        """Obtém um usuário pelo ID"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return user
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {e}")
            return None

    @staticmethod
    def create_user(user_id, username):
        """Cria um novo usuário"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (user_id, username, coins, is_premium) VALUES (?, ?, ?, ?)",
                (str(user_id), username, 0, 0)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
            return False

    @staticmethod
    def ensure_user_exists(user_id, username):
        """Verifica se o usuário existe, se não, cria um novo"""
        user = UserService.get_user(user_id)
        if not user:
            success = UserService.create_user(user_id, username)
            if success:
                return UserService.get_user(user_id)
            return None
        return user

    @staticmethod
    def add_coins(user_id, amount, description="Adição de coins"):
        """Adiciona coins ao usuário"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Atualizar saldo do usuário
            cursor.execute(
                "UPDATE users SET coins = coins + ? WHERE user_id = ?",
                (amount, str(user_id))
            )

            # Registrar transação
            cursor.execute(
                "INSERT INTO transactions (user_id, amount, description) VALUES (?, ?, ?)",
                (str(user_id), amount, description)
            )

            conn.commit()

            # Obter usuário atualizado
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
            updated_user = cursor.fetchone()

            cursor.close()
            conn.close()

            return True, updated_user
        except Exception as e:
            logger.error(f"Erro ao adicionar coins: {e}")
            return False, str(e)

    @staticmethod
    def remove_coins(user_id, amount, description="Remoção de coins"):
        """Remove coins do usuário se tiver saldo suficiente"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Verificar saldo
            cursor.execute("SELECT coins FROM users WHERE user_id = ?", (str(user_id),))
            result = cursor.fetchone()
            if not result or result[0] < amount:
                cursor.close()
                conn.close()
                return False, "Saldo insuficiente"

            # Atualizar saldo
            cursor.execute(
                "UPDATE users SET coins = coins - ? WHERE user_id = ?",
                (amount, str(user_id))
            )

            # Registrar transação
            cursor.execute(
                "INSERT INTO transactions (user_id, amount, description) VALUES (?, ?, ?)",
                (str(user_id), -amount, description)
            )

            conn.commit()

            # Obter usuário atualizado
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
            updated_user = cursor.fetchone()

            cursor.close()
            conn.close()

            return True, updated_user
        except Exception as e:
            logger.error(f"Erro ao remover coins: {e}")
            return False, str(e)

    @staticmethod
    def transfer_coins(from_user_id, to_user_id, amount, description="Transferência"):
        """Transfere coins entre usuários"""
        try:
            # Remover do remetente
            success, result = UserService.remove_coins(
                from_user_id, 
                amount, 
                f"Transferência para {to_user_id}"
            )

            if not success:
                return False, result

            # Adicionar ao destinatário
            success, result = UserService.add_coins(
                to_user_id,
                amount,
                f"Recebido de {from_user_id}"
            )

            if not success:
                # Reverter a transação se falhar
                UserService.add_coins(
                    from_user_id,
                    amount,
                    "Estorno de transferência falha"
                )
                return False, result

            return True, amount
        except Exception as e:
            logger.error(f"Erro na transferência: {e}")
            return False, str(e)

    @staticmethod
    def check_daily(user_id):
        """Verifica se o usuário pode coletar o daily, com tratamento robusto de erros"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Verificar último daily e status premium
            cursor.execute(
                "SELECT last_daily, is_premium FROM users WHERE user_id = ?", 
                (str(user_id),)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if not result:
                return False, "Usuário não encontrado"

            # Verificar se o valor last_daily está presente
            last_daily = result[0]
            is_premium = bool(result[1]) if result[1] is not None else False

            # Se não tem último daily registrado, pode coletar
            if not last_daily:
                logger.info(f"Usuário {user_id} nunca coletou daily antes, liberado")
                return True, None

            # Tratar diferentes formatos de data
            try:
                # Se for string, converter para datetime
                if isinstance(last_daily, str):
                    # Remover Z ou +00:00 se presente para evitar erros
                    last_daily = last_daily.replace('Z', '').replace('+00:00', '')

                    # Tentar converter com diferentes formatos
                    try:
                        last_daily = datetime.datetime.fromisoformat(last_daily)
                    except ValueError:
                        try:
                            # Tentar format SQLite padrão
                            last_daily = datetime.datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            # Formato desconhecido, assumir que pode coletar
                            logger.warning(f"Formato de data não reconhecido: {last_daily}, permitindo coletar")
                            return True, None
            except Exception as date_error:
                # Em caso de erro ao processar a data, log e permite coletar
                logger.error(f"Erro ao processar data do último daily: {date_error}")
                return True, None

            # Calcular próximo daily possível
            try:
                now = datetime.datetime.now()
                # Premium tem cooldown reduzido (20h vs 24h)
                cooldown = datetime.timedelta(hours=20) if is_premium else datetime.timedelta(hours=24)
                next_daily = last_daily + cooldown

                # Verificar se já passou o tempo necessário
                if now < next_daily:
                    # Ainda não pode coletar, calcular tempo restante
                    remaining = next_daily - now
                    # Converter para horas e minutos
                    total_seconds = remaining.total_seconds()
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)

                    logger.info(f"Usuário {user_id} ainda precisa esperar {hours}h {minutes}m para coletar daily")
                    return False, (is_premium, hours, minutes)

                # Tempo suficiente passou, pode coletar
                logger.info(f"Usuário {user_id} pode coletar daily (último: {last_daily})")
                return True, None

            except Exception as time_error:
                # Em caso de erro no cálculo do tempo, log e permite coletar
                logger.error(f"Erro ao calcular tempo para próximo daily: {time_error}")
                return True, None

        except Exception as e:
            # Erro geral na verificação, log detalhado
            logger.error(f"Erro crítico ao verificar daily: {e}")

            # Em caso de falhas, tentamos um fallback simplificado
            try:
                # Tentativa de fallback para verificação
                conn = get_db()
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Verificar se o usuário existe
                cursor.execute("SELECT COUNT(*) as count FROM users WHERE user_id = ?", (str(user_id),))
                exists = cursor.fetchone()["count"] > 0

                cursor.close()
                conn.close()

                if exists:
                    # Se o usuário existe mas houve erro, permitir coletar para evitar frustração
                    logger.warning("Usando fallback para permitir coleta do daily após erro")
                    return True, None
            except:
                pass

            # Se chegou aqui, informar o erro
            return False, "Erro ao verificar status do daily. Tente novamente."

    @staticmethod
    def claim_daily(user_id):
        """Processa a coleta do daily com múltiplas camadas de segurança"""
        try:
            # Criar conexão e cursor
            conn = get_db()
            conn.isolation_level = None  # Habilitar transações manuais
            cursor = conn.cursor()

            try:
                # Iniciar transação explícita 
                cursor.execute("BEGIN TRANSACTION")

                # Obter status premium e moedas atuais
                cursor.execute(
                    "SELECT is_premium, coins FROM users WHERE user_id = ?", 
                    (str(user_id),)
                )
                result = cursor.fetchone()

                if not result:
                    cursor.execute("ROLLBACK")
                    cursor.close()
                    conn.close()
                    return False, "Usuário não encontrado"

                is_premium = bool(result[0])
                current_coins = result[1] or 0

                # Gerar valor com base no status
                base_amount = random.randint(1000, 1500)
                amount = int(base_amount * 1.5) if is_premium else base_amount

                # Atualizar último daily com timestamp serializado
                now = datetime.datetime.now().isoformat()

                # Registrar transação primeiro (mais seguro se houver falha)
                description = "Daily Reward (Premium)" if is_premium else "Daily Reward"
                cursor.execute(
                    "INSERT INTO transactions (user_id, amount, description) VALUES (?, ?, ?)",
                    (str(user_id), amount, description)
                )

                # Registrar data do daily
                cursor.execute(
                    "UPDATE users SET last_daily = ? WHERE user_id = ?",
                    (now, str(user_id))
                )

                # Adicionar coins
                cursor.execute(
                    "UPDATE users SET coins = coins + ? WHERE user_id = ?",
                    (amount, str(user_id))
                )

                # Confirmar transação
                cursor.execute("COMMIT")

                # Registrar log de sucesso
                logger.info(f"Daily processado com sucesso para {user_id}: +{amount} coins")

                # Retornar resultado com informações completas
                return True, (amount, is_premium)

            except Exception as e:
                # Em caso de erro, fazer rollback explícito
                cursor.execute("ROLLBACK")
                logger.error(f"Erro na transação de daily, rollback executado: {e}")
                raise  # Re-lançar a exceção para ser capturada no bloco externo

        except Exception as e:
            logger.error(f"Erro ao processar daily: {e}")

            # Sistema de contingência: tentar uma abordagem alternativa mais simples
            try:
                logger.warning("Tentando abordagem de contingência para o daily")
                conn = get_db()
                cursor = conn.cursor()

                # Verificar se o usuário existe
                cursor.execute("SELECT is_premium FROM users WHERE user_id = ?", (str(user_id),))
                user_check = cursor.fetchone()

                if user_check:
                    is_premium = bool(user_check[0])

                    # Valor fixo de contingência
                    amount = 1500 if is_premium else 1000

                    # Atualização mínima necessária
                    cursor.execute(
                        "UPDATE users SET coins = coins + ?, last_daily = ? WHERE user_id = ?",
                        (amount, datetime.datetime.now().isoformat(), str(user_id))
                    )

                    conn.commit()
                    cursor.close()
                    conn.close()

                    logger.info(f"Daily processado em modo de contingência: +{amount} coins")
                    return True, (amount, is_premium)

            except Exception as contingency_error:
                logger.error(f"Falha também no sistema de contingência: {contingency_error}")

            # Se chegou aqui, retornar erro
            return False, str(e)

    @staticmethod
    def update_premium_status(user_id, is_premium, days=30):
        """Atualiza o status premium do usuário"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            now = datetime.datetime.now()
            premium_until = None

            if is_premium:
                # Verificar se já é premium para estender o prazo
                cursor.execute("SELECT premium_until FROM users WHERE user_id = ?", (str(user_id),))
                result = cursor.fetchone()

                if result and result[0]:
                    premium_date = None
                    # Converter string para datetime se necessário
                    if isinstance(result[0], str):
                        premium_date = datetime.datetime.fromisoformat(result[0].replace('Z', '+00:00'))
                    else:
                        premium_date = result[0]

                    # Se ainda é premium, estende o prazo
                    if premium_date and premium_date > now:
                        premium_until = premium_date + datetime.timedelta(days=days)
                    else:
                        premium_until = now + datetime.timedelta(days=days)
                else:
                    premium_until = now + datetime.timedelta(days=days)

                premium_until_str = premium_until.isoformat() if premium_until else None
                cursor.execute(
                    "UPDATE users SET is_premium = 1, premium_until = ? WHERE user_id = ?",
                    (premium_until_str, str(user_id))
                )
            else:
                cursor.execute(
                    "UPDATE users SET is_premium = 0, premium_until = NULL WHERE user_id = ?",
                    (str(user_id),)
                )

            conn.commit()

            # Obter usuário atualizado
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
            updated_user = cursor.fetchone()

            cursor.close()
            conn.close()

            return True, updated_user
        except Exception as e:
            logger.error(f"Erro ao atualizar status premium: {e}")
            return False, str(e)

    @staticmethod
    def add_xp(user_id, amount):
        """Adiciona XP ao usuário e gerencia evolução de nível"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Obter XP e nível atual
            cursor.execute("SELECT xp, level FROM users WHERE user_id = ?", (str(user_id),))
            result = cursor.fetchone()

            if not result:
                cursor.close()
                conn.close()
                return False, "Usuário não encontrado"

            current_xp = result[0] or 0
            current_level = result[1] or 1

            # Adicionar XP
            new_xp = current_xp + amount

            # Calcular se deve haver evolução de nível
            # Fórmula: XP necessário para o próximo nível = 100 * nível atual * 1.5
            xp_for_next_level = int(100 * current_level * 1.5)
            level_up = False
            new_level = current_level

            # Verificar se o novo XP é suficiente para evoluir
            while new_xp >= xp_for_next_level:
                new_level += 1
                new_xp -= xp_for_next_level
                level_up = True
                # Recalcular XP necessário para o próximo nível
                xp_for_next_level = int(100 * new_level * 1.5)

            # Atualizar usuário no banco
            cursor.execute(
                "UPDATE users SET xp = ?, level = ? WHERE user_id = ?",
                (new_xp, new_level, str(user_id))
            )

            conn.commit()

            # Obter usuário atualizado
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
            updated_user = cursor.fetchone()

            cursor.close()
            conn.close()

            return True, {"user": updated_user, "level_up": level_up, "old_level": current_level, "new_level": new_level}
        except Exception as e:
            logger.error(f"Erro ao adicionar XP: {e}")
            return False, str(e)

    @staticmethod
    def get_level_info(user_id):
        """Obtém informações detalhadas do nível do usuário"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Obter XP e nível atual
            cursor.execute("SELECT xp, level FROM users WHERE user_id = ?", (str(user_id),))
            result = cursor.fetchone()

            if not result:
                cursor.close()
                conn.close()
                return False, "Usuário não encontrado"

            current_xp = result[0] or 0
            current_level = result[1] or 1

            # Calcular XP necessário para o próximo nível
            xp_for_next_level = int(100 * current_level * 1.5)

            # Calcular progresso percentual
            progress_percent = (current_xp / xp_for_next_level) * 100 if xp_for_next_level > 0 else 100

            cursor.close()
            conn.close()

            return True, {
                "level": current_level,
                "xp": current_xp,
                "xp_for_next_level": xp_for_next_level,
                "progress_percent": progress_percent
            }
        except Exception as e:
            logger.error(f"Erro ao obter informações de nível: {e}")
            return False, str(e)

class ShopService:
    """Serviço para gerenciar a loja e o inventário dos usuários"""

    @staticmethod
    def get_all_items(premium_filter=None, rarity_filter=None):
        """
        Obtém todos os itens disponíveis na loja

        Args:
            premium_filter: None (todos os itens), True (só itens premium), False (só itens não-premium)
            rarity_filter: None (todas raridades) ou string com nome da raridade específica
        """
        try:
            conn = get_db()
            conn.row_factory = sqlite3.Row  # Para obter resultados como dicionários
            cursor = conn.cursor()

            query = "SELECT * FROM shop_items WHERE is_active = 1"
            params = []

            # Filtrar por premium se especificado
            if premium_filter is not None:
                query += " AND premium = ?"
                params.append(1 if premium_filter else 0)

            # Filtrar por raridade se especificada
            if rarity_filter is not None:
                query += " AND rarity = ?"
                params.append(rarity_filter)

            query += " ORDER BY price"

            cursor.execute(query, params)
            items = [dict(row) for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            return True, items
        except Exception as e:
            logger.error(f"Erro ao obter itens da loja: {e}")
            return False, str(e)

    @staticmethod
    def get_normal_shop_items():
        """Obtém itens da loja normal (não premium, categorias específicas)"""
        try:
            conn = get_db()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Obter itens para loja normal - itens básicos não premium
            cursor.execute("""
                SELECT * FROM shop_items 
                WHERE is_active = 1 
                AND premium = 0 
                AND type IN ('coin_limit', 'inventory', 'xp_boost', 'daily_boost')
                ORDER BY price
            """)

            items = []
            for row in cursor.fetchall():
                items.append(dict(row))

            cursor.close()
            conn.close()

            return True, items
        except Exception as e:
            logger.error(f"Erro ao obter itens da loja normal: {e}")
            return False, str(e)

    @staticmethod
    def get_premium_shop_items():
        """Obtém itens da loja premium (apenas itens premium)"""
        try:
            conn = get_db()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Obter itens premium especiais
            cursor.execute("""
                SELECT * FROM shop_items 
                WHERE is_active = 1 
                AND premium = 1
                ORDER BY price
            """)

            items = []
            for row in cursor.fetchall():
                items.append(dict(row))

            cursor.close()
            conn.close()

            return True, items
        except Exception as e:
            logger.error(f"Erro ao obter itens da loja premium: {e}")
            return False, str(e)

    @staticmethod
    def get_daily_shop_items():
        """Obtém os itens da loja diária com seus descontos"""
        try:
            conn = get_db()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Verificar se os itens ainda são válidos (não expiraram)
            now = datetime.datetime.now().isoformat()

            cursor.execute("""
                SELECT ds.item_id, ds.discount_percent, ds.expiration_date, 
                       si.* 
                FROM daily_shop ds
                JOIN shop_items si ON ds.item_id = si.id
                WHERE ds.expiration_date > ?
                ORDER BY si.price
            """, (now,))

            items = []
            for row in cursor.fetchall():
                item = dict(row)

                # Calcular preço com desconto
                original_price = item['price']
                discount_percent = item['discount_percent']
                discounted_price = int(original_price * (1 - discount_percent/100))

                # Adicionar campos adicionais
                item['original_price'] = original_price
                item['price'] = discounted_price  # Substituir preço pelo com desconto
                item['discount_percent'] = discount_percent

                items.append(item)

            cursor.close()
            conn.close()

            # Se a loja estiver vazia ou expirada, gerar novos itens
            if not items:
                ShopService.refresh_daily_shop()
                return ShopService.get_daily_shop_items()

            return True, items
        except Exception as e:
            logger.error(f"Erro ao obter itens da loja diária: {e}")
            return False, []

    @staticmethod
    def refresh_daily_shop():
        """Atualiza a loja diária com novos itens e descontos"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Limpar loja diária anterior
            cursor.execute('DELETE FROM daily_shop')

            # Selecionar itens aleatórios (4 itens não premium)
            cursor.execute('SELECT id FROM shop_items WHERE premium = 0 ORDER BY RANDOM() LIMIT 4')
            daily_items = cursor.fetchall()

            # Data de expiração (próxima meia-noite)
            tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
            tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            expiration_date = tomorrow.isoformat()

            # Inserir itens com desconto aleatório
            for item_id in daily_items:
                discount = random.choice([10, 15, 20, 25, 30])
                cursor.execute(
                    'INSERT INTO daily_shop (item_id, discount_percent, expiration_date) VALUES (?, ?, ?)',
                    (item_id[0], discount, expiration_date)
                )

            conn.commit()
            cursor.close()
            conn.close()

            return True, "Loja diária atualizada com sucesso!"
        except Exception as e:
            logger.error(f"Erro ao atualizar loja diária: {e}")
            return False, f"Erro ao atualizar loja diária: {e}"

    @staticmethod
    def get_item(item_id):
        """Obtém um item específico da loja pelo ID"""
        try:
            conn = get_db()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM shop_items WHERE id = ?", (item_id,))
            item = cursor.fetchone()

            cursor.close()
            conn.close()

            if not item:
                return False, "Item não encontrado"

            return True, dict(item)
        except Exception as e:
            logger.error(f"Erro ao obter item da loja: {e}")
            return False, str(e)

    @staticmethod
    def buy_item(user_id, item_id, quantity=1):
        """Compra um item da loja para o usuário"""
        try:
            # Verificar se o item existe
            success, item = ShopService.get_item(item_id)
            if not success:
                return False, item  # Mensagem de erro

            # Verificar se o usuário existe e tem coins suficientes
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("SELECT coins FROM users WHERE user_id = ?", (str(user_id),))
            user_coins = cursor.fetchone()

            if not user_coins:
                cursor.close()
                conn.close()
                return False, "Usuário não encontrado"

            total_price = item["price"] * quantity

            if user_coins[0] < total_price:
                cursor.close()
                conn.close()
                return False, f"Saldo insuficiente. Você precisa de {total_price:,} coins."

            # Processar a compra
            # 1. Remover coins do usuário
            cursor.execute(
                "UPDATE users SET coins = coins - ? WHERE user_id = ?",
                (total_price, str(user_id))
            )

            # 2. Registrar transação
            cursor.execute(
                "INSERT INTO transactions (user_id, amount, description) VALUES (?, ?, ?)",
                (str(user_id), -total_price, f"Compra de {quantity}x {item['name']}")
            )

            # 3. Verificar se o usuário já tem esse item
            cursor.execute(
                "SELECT id, quantity FROM user_inventory WHERE user_id = ? AND item_id = ? AND is_active = 1",
                (str(user_id), item_id)
            )
            existing_item = cursor.fetchone()

            if existing_item:
                # Atualizar quantidade
                cursor.execute(
                    "UPDATE user_inventory SET quantity = quantity + ? WHERE id = ?",
                    (quantity, existing_item[0])
                )
            else:
                # Adicionar ao inventário
                cursor.execute(
                    "INSERT INTO user_inventory (user_id, item_id, quantity) VALUES (?, ?, ?)",
                    (str(user_id), item_id, quantity)
                )

            conn.commit()
            cursor.close()
            conn.close()

            return True, {"item": item, "quantity": quantity, "total_price": total_price}
        except Exception as e:
            logger.error(f"Erro ao comprar item: {e}")
            return False, str(e)

    @staticmethod
    def get_user_inventory(user_id):
        """Obtém o inventário do usuário com detalhes dos itens"""
        try:
            conn = get_db()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Obter itens do inventário com junção na tabela de itens
            cursor.execute("""
                SELECT ui.*, si.name, si.description, si.type, si.effect, si.effect_value, si.premium, si.rarity
                FROM user_inventory ui
                JOIN shop_items si ON ui.item_id = si.id
                WHERE ui.user_id = ? AND ui.is_active = 1
            """, (str(user_id),))

            inventory = [dict(row) for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            return True, inventory
        except Exception as e:
            logger.error(f"Erro ao obter inventário: {e}")
            return False, str(e)

    @staticmethod
    def get_user_fragments(user_id):
        """Obtém os fragmentos do usuário"""
        try:
            conn = get_db()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Verificar se o usuário tem entradas na tabela de fragmentos
            cursor.execute("SELECT COUNT(*) as count FROM fragments WHERE user_id = ?", (str(user_id),))
            count = cursor.fetchone()["count"]

            # Se não tiver, inicializar com valores zero
            if count == 0:
                fragment_types = ["comum", "incomum", "raro", "épico", "lendário"]
                for f_type in fragment_types:
                    cursor.execute(
                        "INSERT INTO fragments (user_id, fragment_type, quantity) VALUES (?, ?, 0)",
                        (str(user_id), f_type)
                    )
                conn.commit()

            # Obter todos os fragmentos
            cursor.execute("SELECT fragment_type, quantity FROM fragments WHERE user_id = ?", (str(user_id),))
            fragments = {}
            for row in cursor.fetchall():
                fragments[row["fragment_type"]] = row["quantity"]

            cursor.close()
            conn.close()

            return True, fragments
        except Exception as e:
            logger.error(f"Erro ao obter fragmentos: {e}")
            return False, {"comum": 0, "incomum": 0, "raro": 0, "épico": 0, "lendário": 0}

    @staticmethod
    def add_fragments(user_id, fragment_type, amount):
        """Adiciona fragmentos ao usuário"""
        try:
            # Normalizar tipo de fragmento
            fragment_type = fragment_type.lower()
            if fragment_type not in ["comum", "incomum", "raro", "épico", "lendário"]:
                return False, f"Tipo de fragmento inválido: {fragment_type}"

            conn = get_db()
            cursor = conn.cursor()

            # Verificar se já existe o tipo de fragmento para o usuário
            cursor.execute(
                "SELECT id FROM fragments WHERE user_id = ? AND fragment_type = ?",
                (str(user_id), fragment_type)
            )
            result = cursor.fetchone()

            if result:
                # Atualizar quantidade
                cursor.execute(
                    "UPDATE fragments SET quantity = quantity + ? WHERE user_id = ? AND fragment_type = ?",
                    (amount, str(user_id), fragment_type)
                )
            else:
                # Inserir novo
                cursor.execute(
                    "INSERT INTO fragments (user_id, fragment_type, quantity) VALUES (?, ?, ?)",
                    (str(user_id), fragment_type, amount)
                )

            conn.commit()
            cursor.close()
            conn.close()

            return True, f"Adicionado {amount} fragmento(s) {fragment_type}"
        except Exception as e:
            logger.error(f"Erro ao adicionar fragmentos: {e}")
            return False, str(e)

    @staticmethod
    def get_crafting_recipes():
        """Obtém as receitas disponíveis para crafting"""
        try:
            conn = get_db()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT cr.*, si.name as item_name, si.description as item_description, 
                       si.price as item_price, si.rarity as item_rarity
                FROM crafting_recipes cr
                JOIN shop_items si ON cr.result_item_id = si.id
            """)

            recipes = [dict(row) for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            return True, recipes
        except Exception as e:
            logger.error(f"Erro ao obter receitas de crafting: {e}")
            return False, str(e)

    @staticmethod
    def craft_item(user_id, recipe_id):
        """
        Cria um item usando fragmentos e adiciona ao inventário do usuário

        Returns:
            tuple: (success, result)
                success: bool indicando se o crafting foi bem-sucedido
                result: Em caso de sucesso, dicionário com informações do item criado.
                        Em caso de falha, string com a mensagem de erro
        """
        try:
            conn = get_db()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Obter a receita
            cursor.execute("""
                SELECT cr.*, si.name as item_name, si.description as item_description, 
                       si.price as item_price, si.rarity as item_rarity, si.id as item_id
                FROM crafting_recipes cr
                JOIN shop_items si ON cr.result_item_id = si.id
                WHERE cr.id = ?
            """, (recipe_id,))

            recipe = cursor.fetchone()

            if not recipe:
                cursor.close()
                conn.close()
                return False, "Receita não encontrada"

            recipe_dict = dict(recipe)

            # 2. Obter fragmentos do usuário
            success, fragments = ShopService.get_user_fragments(user_id)
            if not success:
                cursor.close()
                conn.close()
                return False, "Erro ao obter fragmentos do usuário"

            # 3. Verificar se tem coins suficientes
            cursor.execute("SELECT coins FROM users WHERE user_id = ?", (str(user_id),))
            user_coins = cursor.fetchone()["coins"]

            if user_coins < recipe_dict["coins_cost"]:
                cursor.close()
                conn.close()
                return False, f"Coins insuficientes. Necessário: {recipe_dict['coins_cost']}, Disponível: {user_coins}"

            # 4. Verificar se tem os fragmentos necessários
            fragment_mapping = {
                "comum": "common_fragments",
                "incomum": "uncommon_fragments",
                "raro": "rare_fragments",
                "épico": "epic_fragments",
                "lendário": "legendary_fragments"
            }

            for fragment_type, recipe_field in fragment_mapping.items():
                required = recipe_dict[recipe_field]
                available = fragments.get(fragment_type, 0)

                if available < required:
                    cursor.close()
                    conn.close()
                    return False, f"Fragmentos insuficientes. Necessário: {required} {fragment_type}, Disponível: {available}"

            # 5. Tudo ok, começar a transação
            # 5.1 Deduzir os fragmentos
            for fragment_type, recipe_field in fragment_mapping.items():
                required = recipe_dict[recipe_field]
                if required > 0:
                    cursor.execute(
                        "UPDATE fragments SET quantity = quantity - ? WHERE user_id = ? AND fragment_type = ?",
                        (required, str(user_id), fragment_type)
                    )

            # 5.2 Deduzir os coins
            if recipe_dict["coins_cost"] > 0:
                cursor.execute(
                    "UPDATE users SET coins = coins - ? WHERE user_id = ?",
                    (recipe_dict["coins_cost"], str(user_id))
                )

                # Registrar na tabela de transações
                cursor.execute(
                    "INSERT INTO transactions (user_id, amount, description) VALUES (?, ?, ?)",
                    (str(user_id), -recipe_dict["coins_cost"], f"Crafting de item: {recipe_dict['item_name']}")
                )

            # 5.3 Adicionar o item ao inventário
            cursor.execute(
                "INSERT INTO user_inventory (user_id, item_id, quantity) VALUES (?, ?, 1)",
                (str(user_id), recipe_dict["item_id"])
            )

            # Commit da transação
            conn.commit()

            # Retornar informações do item criado
            result = {
                "item_name": recipe_dict["item_name"],
                "item_description": recipe_dict["item_description"],
                "item_rarity": recipe_dict["item_rarity"],
                "fragments_used": {
                    "comum": recipe_dict["common_fragments"],
                    "incomum": recipe_dict["uncommon_fragments"],
                    "raro": recipe_dict["rare_fragments"],
                    "épico": recipe_dict["epic_fragments"],
                    "lendário": recipe_dict["legendary_fragments"]
                },
                "coins_cost": recipe_dict["coins_cost"]
            }

            cursor.close()
            conn.close()

            return True, result

        except Exception as e:
            logger.error(f"Erro ao criar item: {e}")
            return False, f"Erro ao criar item: {e}"

    @staticmethod
    def initialize_default_recipes():
        """Inicializa o banco com algumas receitas de crafting padrão"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Verificar se já existem receitas
            cursor.execute("SELECT COUNT(*) FROM crafting_recipes")
            recipe_count = cursor.fetchone()[0]

            if recipe_count == 0:
                # Obter alguns IDs de itens para usar nas receitas
                cursor.execute("SELECT id, name FROM shop_items WHERE type IN ('xp_boost', 'daily_boost', 'coin_limit', 'cooldown_reduction') LIMIT 10")
                items = cursor.fetchall()

                if not items:
                    cursor.close()
                    conn.close()
                    return False, "Nenhum item disponível para criar receitas"

                # Criar receitas para alguns itens
                recipes = []
                for item_id, item_name in items:
                    # Diferentes combinações de fragmentos baseadas no nome/id do item
                    if "XP" in item_name:
                        recipes.append((
                            f"Criar {item_name}", 
                            f"Crafta o item '{item_name}' usando fragmentos", 
                            item_id, 15, 10, 5, 0, 0, 2000
                        ))
                    elif "Daily" in item_name:
                        recipes.append((
                            f"Criar {item_name}", 
                            f"Crafta o item '{item_name}' usando fragmentos", 
                            item_id, 10, 8, 4, 1, 0, 1500
                        ))
                    elif "Cooldown" in item_name:
                        recipes.append((
                            f"Criar {item_name}", 
                            f"Crafta o item '{item_name}' usando fragmentos", 
                            item_id, 8, 6, 3, 1, 0, 1000
                        ))
                    else:
                        recipes.append((
                            f"Criar {item_name}", 
                            f"Crafta o item '{item_name}' usando fragmentos", 
                            item_id, 12, 8, 4, 0, 0, 1200
                        ))

                # Inserir as receitas
                cursor.executemany("""
                    INSERT INTO crafting_recipes 
                    (name, description, result_item_id, common_fragments, uncommon_fragments, 
                     rare_fragments, epic_fragments, legendary_fragments, coins_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, recipes)

                conn.commit()
                cursor.close()
                conn.close()

                return True, f"Adicionadas {len(recipes)} receitas de crafting"
            else:
                cursor.close()
                conn.close()
                return True, f"Já existem {recipe_count} receitas de crafting"

        except Exception as e:
            logger.error(f"Erro ao inicializar receitas de crafting: {e}")
            return False, str(e)

    @staticmethod
    def initialize_default_items():
        """Inicializa a loja com itens padrão se estiver vazia"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Verificar se já existem itens
            cursor.execute("SELECT COUNT(*) FROM shop_items")
            item_count = cursor.fetchone()[0]

            if item_count == 0:
                # Criar itens padrão
                default_items = [
                    # Limite de Coins
                    ("Expansão de Carteira I", "Aumenta limite de coins em 50.000", 10000, "coin_limit", "aumento", 50000, None, 0, "comum"),
                    ("Expansão de Carteira II", "Aumenta limite de coins em 100.000", 25000, "coin_limit", "aumento", 100000, None, 0, "incomum"),
                    ("Expansão de Carteira III", "Aumenta limite de coins em 200.000", 50000, "coin_limit", "aumento", 200000, None, 0, "raro"),
                    ("Expansão de Carteira IV", "Aumenta limite de coins em 500.000", 100000, "coin_limit", "aumento", 500000, None, 0, "épico"),
                    ("Expansão de Carteira V", "Aumenta limite de coins em 1.000.000", 250000, "coin_limit", "aumento", 1000000, None, 1, "lendário"),

                    # Expansão de Inventário
                    ("Bolsa Pequena", "Aumenta capacidade do inventário em 5 slots", 5000, "inventory", "aumento", 5, None, 0, "comum"),
                    ("Bolsa Média", "Aumenta capacidade do inventário em 10 slots", 15000, "inventory", "aumento", 10, None, 0, "incomum"),
                    ("Bolsa Grande", "Aumenta capacidade do inventário em 20 slots", 30000, "inventory", "aumento", 20, None, 0, "raro"),
                    ("Bolsa Épica", "Aumenta capacidade do inventário em 50 slots", 75000, "inventory", "aumento", 50, None, 0, "épico"),
                    ("Bolsa Infinita", "Aumenta capacidade do inventário em 100 slots", 150000, "inventory", "aumento", 100, None, 1, "lendário"),

                    # Daily Boosters
                    ("Multiplicador de Daily I", "Aumenta em 25% os coins do daily por 7 dias", 5000, "daily_boost", "multiplicador", 1.25, None, 0, "comum"),
                    ("Multiplicador de Daily II", "Aumenta em 50% os coins do daily por 7 dias", 10000, "daily_boost", "multiplicador", 1.50, None, 0, "incomum"),
                    ("Multiplicador de Daily III", "Aumenta em 75% os coins do daily por 7 dias", 15000, "daily_boost", "multiplicador", 1.75, None, 0, "raro"),
                    ("Multiplicador de Daily IV", "Dobra os coins do daily por 7 dias", 25000, "daily_boost", "multiplicador", 2.00, None, 0, "épico"),
                    ("Multiplicador de Daily V", "Triplica os coins do daily por 7 dias", 50000, "daily_boost", "multiplicador", 3.00, None, 1, "lendário"),

                    # XP Boosters
                    ("Boost de XP I", "Aumenta em 25% o XP ganho por 3 dias", 3500, "xp_boost", "multiplicador", 1.25, None, 0, "comum"),
                    ("Boost de XP II", "Aumenta em 50% o XP ganho por 3 dias", 7000, "xp_boost", "multiplicador", 1.50, None, 0, "incomum"),
                    ("Boost de XP III", "Dobra o XP ganho por 3 dias", 12000, "xp_boost", "multiplicador", 2.00, None, 0, "raro"),
                    ("Boost de XP IV", "Triplica o XP ganho por 3 dias", 20000, "xp_boost", "multiplicador", 3.00, None, 0, "épico"),
                    ("Boost de XP V", "Quintuplica o XP ganho por 3 dias", 40000, "xp_boost", "multiplicador", 5.00, None, 1, "lendário"),

                    # Cooldown Reducers  
                    ("Redutor de Cooldown I", "Reduz em 20% o cooldown do daily", 4000, "cooldown_reduction", "percentual", 0.20, None, 0, "comum"),
                    ("Redutor de Cooldown II", "Reduz em 35% o cooldown do daily", 8000, "cooldown_reduction", "percentual", 0.35, None, 0, "incomum"),
                    ("Redutor de Cooldown III", "Reduz em 50% o cooldown do daily", 12000, "cooldown_reduction", "percentual", 0.50, None, 0, "raro"),
                    ("Redutor de Cooldown IV", "Reduz em 75% o cooldown do daily", 20000, "cooldown_reduction", "percentual", 0.75, None, 0, "épico"),
                    ("Redutor de Cooldown V", "Elimina o cooldown do daily por 1 dia", 50000, "cooldown_reduction", "percentual", 1.00, None, 1, "lendário"),

                    # Game Boosters
                    ("Bônus de Vitória I", "Aumenta em 30% os ganhos no minigame", 3000, "game_boost", "multiplicador", 1.30, None, 0, "comum"),
                    ("Bônus de Vitória II", "Aumenta em 60% os ganhos no minigame", 6000, "game_boost", "multiplicador", 1.60, None, 0, "incomum"),
                    ("Bônus de Vitória III", "Dobra os ganhos no minigame", 10000, "game_boost", "multiplicador", 2.00, None, 0, "raro"),
                    ("Bônus de Vitória IV", "Triplica os ganhos no minigame", 18000, "game_boost", "multiplicador", 3.00, None, 0, "épico"),
                    ("Bônus de Vitória V", "Quintuplica os ganhos no minigame", 35000, "game_boost", "multiplicador", 5.00, None, 1, "lendário"),

                    # Loss Protection
                    ("Proteção Básica", "30% de chance de não perder coins", 5000, "loss_protection", "percentual", 0.30, None, 0, "comum"),
                    ("Proteção Avançada", "50% de chance de não perder coins", 10000, "loss_protection", "percentual", 0.50, None, 0, "incomum"),
                    ("Proteção Suprema", "70% de chance de não perder coins", 15000, "loss_protection", "percentual", 0.70, None, 0, "raro"),
                    ("Proteção Épica", "85% de chance de não perder coins", 25000, "loss_protection", "percentual", 0.85, None, 0, "épico"),
                    ("Proteção Divina", "100% de chance de não perder coins por 1 dia", 50000, "loss_protection", "percentual", 1.00, None, 1, "lendário"),

                    # Fragment Boosters (New!)
                    ("Coletor de Fragmentos I", "Aumenta em 20% os fragmentos ganhos", 5000, "fragment_boost", "multiplicador", 1.20, None, 0, "comum"),
                    ("Coletor de Fragmentos II", "Aumenta em 50% os fragmentos ganhos", 10000, "fragment_boost", "multiplicador", 1.50, None, 0, "incomum"),
                    ("Coletor de Fragmentos III", "Dobra os fragmentos ganhos", 20000, "fragment_boost", "multiplicador", 2.00, None, 0, "raro"),
                    ("Coletor de Fragmentos IV", "Triplica os fragmentos ganhos", 35000, "fragment_boost", "multiplicador", 3.00, None, 0, "épico"),
                    ("Coletor de Fragmentos V", "Quintuplica os fragmentos ganhos", 60000, "fragment_boost", "multiplicador", 5.00, None, 1, "lendário"),

                    # Lucky Items (New!)
                    ("Trevo de Quatro Folhas", "Aumenta em 10% sua sorte nos jogos", 8000, "luck_boost", "percentual", 0.10, None, 0, "comum"),
                    ("Pata de Coelho", "Aumenta em 20% sua sorte nos jogos", 15000, "luck_boost", "percentual", 0.20, None, 0, "incomum"),
                    ("Ferradura de Ouro", "Aumenta em 30% sua sorte nos jogos", 25000, "luck_boost", "percentual", 0.30, None, 0, "raro"),
                    ("Amuleto da Sorte", "Aumenta em 50% sua sorte nos jogos", 40000, "luck_boost", "percentual", 0.50, None, 0, "épico"),
                    ("Artefato da Fortuna", "Dobra sua sorte nos jogos por 1 dia", 75000, "luck_boost", "percentual", 1.00, None, 1, "lendário"),

                    # Crafting Boosters (New!)
                    ("Kit de Ferramentas Básico", "Reduz em 10% os fragmentos necessários para crafting", 6000, "crafting_discount", "percentual", 0.10, None, 0, "comum"),
                    ("Kit de Ferramentas Avançado", "Reduz em 25% os fragmentos necessários para crafting", 12000, "crafting_discount", "percentual", 0.25, None, 0, "incomum"),
                    ("Kit de Ferramentas Premium", "Reduz em 40% os fragmentos necessários para crafting", 24000, "crafting_discount", "percentual", 0.40, None, 0, "raro"),
                    ("Estação de Crafting Portátil", "Reduz em 60% os fragmentos necessários para crafting", 45000, "crafting_discount", "percentual", 0.60, None, 0, "épico"),
                    ("Forja Arcana", "Reduz em 80% os fragmentos necessários para crafting", 80000, "crafting_discount", "percentual", 0.80, None, 1, "lendário"),

                    # Visual Effects
                    ("Aura Verde", "Adiciona uma aura verde ao seu perfil", 1500, "visual_effect", "aura", "green", None, 0, "comum"),
                    ("Aura Azul", "Adiciona uma aura azul ao seu perfil", 1500, "visual_effect", "aura", "blue", None, 0, "comum"),
                    ("Aura Vermelha", "Adiciona uma aura vermelha ao seu perfil", 1500, "visual_effect", "aura", "red", None, 0, "comum"),
                    ("Aura Roxa", "Adiciona uma aura roxa ao seu perfil", 3000, "visual_effect", "aura", "purple", None, 0, "incomum"),
                    ("Aura Dourada", "Adiciona uma aura dourada ao seu perfil", 5000, "visual_effect", "aura", "gold", None, 0, "raro"),
                    ("Aura de Cristal", "Adiciona uma aura de cristal ao seu perfil", 12000, "visual_effect", "aura", "crystal", None, 0, "épico"),
                    ("Aura Lendária", "Adiciona uma aura arco-íris ao seu perfil", 25000, "visual_effect", "aura", "rainbow", None, 1, "lendário"),

                    # Custom Backgrounds (New!)
                    ("Fundo: Floresta", "Muda o fundo do seu perfil para uma floresta", 2000, "profile_background", "imagem", "forest", None, 0, "comum"),
                    ("Fundo: Praia", "Muda o fundo do seu perfil para uma praia", 2000, "profile_background", "imagem", "beach", None, 0, "comum"),
                    ("Fundo: Montanhas", "Muda o fundo do seu perfil para montanhas", 2000, "profile_background", "imagem", "mountain", None, 0, "comum"),
                    ("Fundo: Cidade", "Muda o fundo do seu perfil para uma cidade à noite", 4000, "profile_background", "imagem", "city", None, 0, "incomum"),
                    ("Fundo: Espaço", "Muda o fundo do seu perfil para o espaço", 4000, "profile_background", "imagem", "space", None, 0, "incomum"),
                    ("Fundo: Vulcânico", "Muda o fundo do seu perfil para um cenário vulcânico", 8000, "profile_background", "imagem", "volcano", None, 0, "raro"),
                    ("Fundo: Aquático", "Muda o fundo do seu perfil para um cenário subaquático", 8000, "profile_background", "imagem", "underwater", None, 0, "raro"),
                    ("Fundo: Nebulosa", "Muda o fundo do seu perfil para uma nebulosa cósmica", 15000, "profile_background", "imagem", "nebula", None, 0, "épico"),
                    ("Fundo: Aurora Boreal", "Muda o fundo do seu perfil para uma aurora boreal", 15000, "profile_background", "imagem", "aurora", None, 0, "épico"),
                    ("Fundo: Dimensão Paralela", "Muda o fundo do seu perfil para uma dimensão paralela", 30000, "profile_background", "imagem", "dimension", None, 1, "lendário"),

                    # Titles
                    ("Título: Novato", "Título básico para perfil", 5000, "title", "estilo", 1.0, None, 0, "comum"),
                    ("Título: Aventureiro", "Título básico para perfil", 5000, "title", "estilo", 1.1, None, 0, "comum"),
                    ("Título: Explorador", "Título básico para perfil", 5000, "title", "estilo", 1.2, None, 0, "comum"),
                    ("Título: Veterano", "Título intermediário para perfil", 10000, "title", "estilo", 2.0, None, 0, "incomum"),
                    ("Título: Caçador", "Título intermediário para perfil", 10000, "title", "estilo", 2.1, None, 0, "incomum"),
                    ("Título: Guardião", "Título intermediário para perfil", 10000, "title", "estilo", 2.2, None, 0, "incomum"),
                    ("Título: Mestre", "Título avançado para perfil", 20000, "title", "estilo", 3.0, None, 0, "raro"),
                    ("Título: Campeão", "Título avançado para perfil", 20000, "title", "estilo", 3.1, None, 0, "raro"),
                    ("Título: Herói", "Título avançado para perfil", 20000, "title", "estilo", 3.2, None, 0, "raro"),
                    ("Título: Lendário", "Título lendário para perfil", 30000, "title", "estilo", 4.0, None, 0, "épico"),
                    ("Título: Mítico", "Título lendário para perfil", 30000, "title", "estilo", 4.1, None, 0, "épico"),
                    ("Título: Imortal", "Título supremo para perfil", 50000, "title", "estilo", 5.0, None, 1, "lendário"),

                    # Special Items (New!)
                    ("Chave Misteriosa", "Desbloqueia um item aleatório de qualquer raridade", 12000, "special", "chave", 1.0, None, 0, "raro"),
                    ("Orbe Mágico", "Revela as probabilidades em todos os jogos por 24h", 15000, "special", "revelação", 1.0, None, 0, "raro"),
                    ("Pergaminho Antigo", "Permite renomear um título que você possui", 20000, "special", "renomear", 1.0, None, 0, "épico"),
                    ("Ampulheta Arcana", "Reinicia todos os cooldowns imediatamente", 25000, "special", "resetar_cooldown", 1.0, None, 0, "épico"),
                    ("Cristal da Transformação", "Permite mudar a cor de uma aura que você possui", 30000, "special", "transformar", 1.0, None, 1, "lendário")
                ]

                for item in default_items:
                    # Inserir com suporte a raridade e premium
                    if len(item) >= 9:
                        cursor.execute("""
                            INSERT INTO shop_items 
                            (name, description, price, type, effect, effect_value, image_url, premium, rarity) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, item[:9])
                    else:
                        # Fallback para compatibilidade com versões antigas
                        cursor.execute("""
                            INSERT INTO shop_items 
                            (name, description, price, type, effect, effect_value) 
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, item[:6])

                conn.commit()
                logger.info(f"Loja inicializada com {len(default_items)} itens padrão")

            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar loja: {e}")
            return False