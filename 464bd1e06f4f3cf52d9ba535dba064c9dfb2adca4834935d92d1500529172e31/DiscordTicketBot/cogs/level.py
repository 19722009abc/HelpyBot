import discord
from discord import app_commands
from discord.ext import commands
import logging
import random
import datetime
import sqlite3
from typing import Literal, List, Dict, Optional

from utils.database_sqlite import UserService, ShopService

# Configuração do logger
logger = logging.getLogger("CartoonBot")

class ShopItemView(discord.ui.View):
    """View para visualização detalhada e compra de um item da loja"""
    def __init__(self, item, user_coins):
        super().__init__(timeout=60)
        self.item = item
        self.user_coins = user_coins
        self.can_buy = user_coins >= item["price"]
        
        # Desabilitar botão se não puder comprar
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "buy":
                child.disabled = not self.can_buy
    
    @discord.ui.button(label="Comprar", style=discord.ButtonStyle.success, custom_id="buy")
    async def buy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para comprar o item"""
        await interaction.response.defer(ephemeral=True)
        
        # Processar a compra
        success, result = ShopService.buy_item(
            str(interaction.user.id),
            self.item["id"]
        )
        
        if success:
            embed = discord.Embed(
                title="✅ COMPRA REALIZADA COM SUCESSO",
                description=f"Você comprou **{self.item['name']}**!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💰 Valor",
                value=f"`{self.item['price']:,} coins`",
                inline=True
            )
            
            embed.add_field(
                name="🎁 Item",
                value=f"`{self.item['name']}`",
                inline=True
            )
            
            embed.set_footer(text="Use /inventario para ver seus itens.")
            
            # Desabilitar o botão após a compra
            button.disabled = True
            
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            embed = discord.Embed(
                title="❌ FALHA NA COMPRA",
                description=f"Não foi possível comprar este item: {result}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para cancelar a compra"""
        embed = discord.Embed(
            title="🛑 COMPRA CANCELADA",
            description="Você cancelou esta compra.",
            color=discord.Color.light_grey()
        )
        
        # Desabilitar todos os botões
        for child in self.children:
            child.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class ShopView(discord.ui.View):
    """View principal da loja com categorias de itens e paginação"""
    def __init__(self, items, user_coins):
        super().__init__(timeout=180)
        self.all_items = items
        self.user_coins = user_coins
        self.current_category = "todos"
        self.current_page = 0
        self.items_per_page = 10
        
        # Adicionar opções ao dropdown de categorias
        self.category_select.add_option(label="Todos os Itens", value="todos", default=True)
        
        # Obter categorias únicas
        categories = set()
        for item in items:
            categories.add(item["type"])
        
        # Adicionar cada categoria ao dropdown
        for category in sorted(categories):
            display_name = self._get_display_name(category)
            self.category_select.add_option(label=display_name, value=category)
        
        # Atualizar estado dos botões de navegação
        self._update_button_states()
    
    def _get_display_name(self, category_id):
        """Converte o ID da categoria para um nome amigável"""
        category_names = {
            "daily_boost": "Bônus de Daily",
            "xp_boost": "Bônus de XP",
            "cooldown_reduction": "Redução de Cooldown",
            "game_boost": "Bônus de Jogo",
            "loss_protection": "Proteção",
            "visual_effect": "Visual",
            "title": "Títulos"
        }
        return category_names.get(category_id, category_id.replace("_", " ").title())
    
    def _get_filtered_items(self):
        """Retorna os itens filtrados pela categoria atual"""
        if self.current_category == "todos":
            return self.all_items
        return [item for item in self.all_items if item["type"] == self.current_category]
    
    def _get_page_items(self):
        """Retorna os itens da página atual"""
        filtered_items = self._get_filtered_items()
        
        # Se não houver itens, retornar lista vazia
        if not filtered_items:
            return []
            
        # Calcular índices de início e fim para a página atual
        start_idx = self.current_page * self.items_per_page
        
        # Garantir que o índice de início não seja maior que o número de itens
        if start_idx >= len(filtered_items):
            self.current_page = 0
            start_idx = 0
            
        # Calcular índice final e garantir que não exceda o tamanho da lista
        end_idx = min(start_idx + self.items_per_page, len(filtered_items))
        
        return filtered_items[start_idx:end_idx]
    
    def _get_max_pages(self):
        """Retorna o número total de páginas"""
        filtered_items = self._get_filtered_items()
        return max(1, (len(filtered_items) + self.items_per_page - 1) // self.items_per_page)
    
    def _update_button_states(self):
        """Atualiza o estado dos botões de navegação"""
        # Desabilitar botão anterior se estiver na primeira página
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "prev_page":
                child.disabled = (self.current_page <= 0)
            # Desabilitar botão próximo se estiver na última página
            elif isinstance(child, discord.ui.Button) and child.custom_id == "next_page":
                max_pages = self._get_max_pages()
                child.disabled = (self.current_page >= max_pages - 1)
            # Atualizar label do botão de página
            elif isinstance(child, discord.ui.Button) and child.custom_id == "page_info":
                max_pages = self._get_max_pages()
                child.label = f"Página {self.current_page + 1}/{max_pages}"
    
    @discord.ui.select(
        placeholder="Escolha uma categoria",
        custom_id="category_select",
        min_values=1,
        max_values=1
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Dropdown para selecionar categoria de itens"""
        self.current_category = select.values[0]
        self.current_page = 0  # Reiniciar para a primeira página ao mudar de categoria
        
        # Atualizar estado dos botões
        self._update_button_states()
        
        # Atualizar embed com os itens da página atual da categoria selecionada
        embed = create_shop_embed(
            self._get_page_items(), 
            self.user_coins, 
            self.current_category,
            page=self.current_page + 1,
            total_pages=self._get_max_pages(),
            total_items=len(self._get_filtered_items())
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="◀️ Anterior", style=discord.ButtonStyle.secondary, custom_id="prev_page", disabled=True, row=1)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para navegar para a página anterior"""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_button_states()
            
            embed = create_shop_embed(
                self._get_page_items(), 
                self.user_coins, 
                self.current_category,
                page=self.current_page + 1,
                total_pages=self._get_max_pages(),
                total_items=len(self._get_filtered_items())
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Página 1/1", style=discord.ButtonStyle.primary, custom_id="page_info", disabled=True, row=1)
    async def page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão que mostra a página atual (apenas informativo)"""
        await interaction.response.defer()
    
    @discord.ui.button(label="Próximo ▶️", style=discord.ButtonStyle.secondary, custom_id="next_page", row=1)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para navegar para a próxima página"""
        max_pages = self._get_max_pages()
        if self.current_page < max_pages - 1:
            self.current_page += 1
            self._update_button_states()
            
            embed = create_shop_embed(
                self._get_page_items(), 
                self.user_coins, 
                self.current_category,
                page=self.current_page + 1,
                total_pages=self._get_max_pages(),
                total_items=len(self._get_filtered_items())
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Ver detalhes", style=discord.ButtonStyle.primary, row=2)
    async def details_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para ver detalhes e comprar um item"""
        # Criar modal para seleção de item
        await interaction.response.send_modal(ItemSelectModal(self._get_filtered_items(), self.user_coins))
    
    @discord.ui.button(label="Meu inventário", style=discord.ButtonStyle.secondary, row=2)
    async def inventory_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para ver o inventário do usuário"""
        await interaction.response.defer(ephemeral=True)
        
        success, inventory = ShopService.get_user_inventory(str(interaction.user.id))
        
        if not success or not inventory:
            embed = discord.Embed(
                title="🎒 SEU INVENTÁRIO",
                description="Você não possui nenhum item no momento.\nUse `/loja` para comprar itens!",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎒 SEU INVENTÁRIO",
            description=f"Você possui **{len(inventory)}** item(ns) diferentes:",
            color=discord.Color.gold()
        )
        
        # Agrupar por tipo para melhor organização
        items_by_type = {}
        for item in inventory:
            item_type = item["type"]
            if item_type not in items_by_type:
                items_by_type[item_type] = []
            items_by_type[item_type].append(item)
        
        # Adicionar cada tipo como um campo separado
        for item_type, items in items_by_type.items():
            # Obter nome amigável do tipo
            type_name = self._get_display_name(item_type)
            
            # Criar lista formatada de itens
            items_text = ""
            for item in items:
                items_text += f"• **{item['name']}** (x{item['quantity']})\n"
                items_text += f"  __{item['description']}__\n"
            
            embed.add_field(
                name=f"📦 {type_name.upper()}",
                value=items_text,
                inline=False
            )
        
        embed.set_footer(text="Seus itens são aplicados automaticamente aos seus comandos.")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class ItemSelectModal(discord.ui.Modal):
    """Modal para selecionar um item para ver detalhes ou comprar"""
    
    def __init__(self, items, user_coins):
        super().__init__(title="Selecionar Item")
        self.items = items
        self.user_coins = user_coins
        
        # Criar campo de entrada para o ID do item
        self.item_id = discord.ui.TextInput(
            label="ID do item (veja na lista de itens)",
            placeholder="Digite o número do item que deseja comprar",
            required=True,
            min_length=1,
            max_length=3
        )
        self.add_item(self.item_id)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Quando o usuário envia o ID do item"""
        try:
            item_id = int(self.item_id.value.strip())
            
            # Verificar se o item existe na lista
            selected_item = None
            for item in self.items:
                if item["id"] == item_id:
                    selected_item = item
                    break
            
            if not selected_item:
                await interaction.response.send_message(
                    "❌ Item não encontrado. Verifique o ID e tente novamente.",
                    ephemeral=True
                )
                return
            
            # Criar embed de detalhes do item
            embed = discord.Embed(
                title=f"🛍️ {selected_item['name']}",
                description=selected_item['description'],
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="💰 Preço",
                value=f"**{selected_item['price']:,}** coins",
                inline=True
            )
            
            embed.add_field(
                name="📋 Tipo",
                value=f"{selected_item['type'].replace('_', ' ').title()}",
                inline=True
            )
            
            embed.add_field(
                name="⚡ Efeito",
                value=f"{selected_item['effect']} ({selected_item['effect_value']})",
                inline=True
            )
            
            # Status se pode comprar ou não
            if self.user_coins >= selected_item["price"]:
                embed.add_field(
                    name="✅ Saldo",
                    value=f"Você tem coins suficientes! (Saldo: **{self.user_coins:,}**)",
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ Saldo Insuficiente",
                    value=f"Você precisa de mais **{selected_item['price'] - self.user_coins:,}** coins",
                    inline=False
                )
            
            # Criar view com botões de compra
            view = ShopItemView(selected_item, self.user_coins)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        except ValueError:
            await interaction.response.send_message(
                "❌ ID inválido. Por favor, digite apenas números.",
                ephemeral=True
            )

def create_shop_embed(items, user_coins, category="todos", page=1, total_pages=1, total_items=None):
    """Cria um embed para exibir a loja de itens com suporte a paginação"""
    if category == "todos":
        title = "🛍️ LOJA DE ITENS"
        description = "Bem-vindo à loja! Compre itens para melhorar sua experiência."
    else:
        # Obter nome amigável da categoria
        category_names = {
            "daily_boost": "Bônus de Daily",
            "xp_boost": "Bônus de XP",
            "cooldown_reduction": "Redução de Cooldown",
            "game_boost": "Bônus de Jogo",
            "loss_protection": "Proteção",
            "visual_effect": "Visual",
            "title": "Títulos"
        }
        category_name = category_names.get(category, category.replace("_", " ").title())
        title = f"🛍️ CATEGORIA: {category_name.upper()}"
        description = f"Itens da categoria **{category_name}**"
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.gold()
    )
    
    # Adicionar saldo do usuário
    embed.add_field(
        name="💰 Seu saldo",
        value=f"**{user_coins:,}** coins",
        inline=False
    )
    
    # Se não há itens
    if not items:
        embed.add_field(
            name="❌ Sem itens",
            value="Não há itens disponíveis nesta categoria no momento.",
            inline=False
        )
        return embed
    
    # Formatação estilizada para lista de itens
    # Limitar o número de itens na página para evitar exceder o limite de 1024 caracteres
    # Uma linha típica tem ~50 caracteres, então 15 itens podem chegar a ~750 caracteres
    # Adicionamos mais 100 caracteres para o cabeçalho, ficando com margem segura
    
    items_text = "```md\n# ID | NOME | PREÇO\n"
    
    # Garantir que não vamos ultrapassar o limite de caracteres
    MAX_CARACTERES = 900  # Margem segura para manter abaixo de 1024
    
    for item in items:
        # Criar linha temporária para verificar tamanho
        item_name = item['name']
        if len(item_name) > 15:  # Reduzir ainda mais o tamanho dos nomes
            item_name = item_name[:12] + "..."
        
        # Verificar se pode comprar
        if user_coins >= item["price"]:
            nova_linha = f"{item['id']} | {item_name} | {item['price']:,} coins ✅\n"
        else:
            nova_linha = f"{item['id']} | {item_name} | {item['price']:,} coins ❌\n"
        
        # Verificar se adicionar esta linha excederia o limite
        if len(items_text) + len(nova_linha) + 3 > MAX_CARACTERES:  # +3 para ```
            break
            
        items_text += nova_linha
    
    items_text += "```"
    
    embed.add_field(
        name="📋 Itens Disponíveis",
        value=items_text,
        inline=False
    )
    
    embed.add_field(
        name="🔍 Como comprar",
        value="Clique em **Ver detalhes** e digite o ID do item que deseja comprar.",
        inline=False
    )
    
    # Adicionar informações de paginação no footer
    if total_items is None:
        total_items = len(items)
    
    embed.set_footer(text=f"Página {page}/{total_pages} • Total de {total_items} itens • Atualizado em {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    return embed

class XPGainManager:
    """Gerencia a concessão de XP para ações do usuário"""
    
    @staticmethod
    async def add_message_xp(user_id, username):
        """Adiciona XP quando o usuário envia uma mensagem (com cooldown)"""
        # Verificar se o usuário existe
        user = UserService.ensure_user_exists(user_id, username)
        if not user:
            return False, "Usuário não encontrado"
        
        # Verificar se já passou tempo suficiente desde a última mensagem (cooldown)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT last_message_time FROM users WHERE user_id = ?", (str(user_id),))
        result = cursor.fetchone()
        
        now = datetime.datetime.now()
        last_message = result[0] if result and result[0] else None
        
        # Converter string para datetime se necessário
        if last_message and isinstance(last_message, str):
            try:
                last_message = datetime.datetime.fromisoformat(last_message.replace('Z', '+00:00'))
            except:
                last_message = None
        
        # Se não tiver registro anterior ou já passou 1 minuto
        if not last_message or (now - last_message).total_seconds() >= 60:
            # Atualizar timestamp da última mensagem
            cursor.execute(
                "UPDATE users SET last_message_time = ?, messages_count = messages_count + 1 WHERE user_id = ?",
                (now.isoformat(), str(user_id))
            )
            conn.commit()
            
            # Adicionar XP (entre 5 e 15)
            xp_amount = random.randint(5, 15)
            
            # Liberar recursos
            cursor.close()
            conn.close()
            
            # Adicionar XP e verificar evolução de nível
            return UserService.add_xp(user_id, xp_amount)
        
        # Liberar recursos
        cursor.close()
        conn.close()
        return False, "Cooldown"
    
    @staticmethod
    async def add_command_xp(user_id, username, command_name):
        """Adiciona XP quando o usuário usa um comando"""
        # Verificar se o usuário existe
        user = UserService.ensure_user_exists(user_id, username)
        if not user:
            return False, "Usuário não encontrado"
        
        # Definir XP com base no comando (ajustar conforme necessário)
        command_xp = {
            "daily": 25,
            "carteira": 10,
            "transferir": 15,
            "jogo": 20,
            "top": 10,
            "loja": 10,
            "perfil": 10,
            "inventario": 10,
            "premium": 15
        }
        
        # XP padrão para comandos não listados
        xp_amount = command_xp.get(command_name, 10)
        
        # Adicionar XP e verificar evolução de nível
        return UserService.add_xp(user_id, xp_amount)

class Level(commands.Cog):
    """Comandos relacionados ao sistema de nível e loja"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Evento disparado quando uma mensagem é enviada"""
        # Ignorar mensagens do próprio bot
        if message.author.bot:
            return
        
        # Adicionar XP pela mensagem
        success, result = await XPGainManager.add_message_xp(
            message.author.id,
            message.author.name
        )
        
        # Se houve evolução de nível, enviar mensagem
        if success and isinstance(result, dict) and result.get("level_up"):
            try:
                # Criar embed de evolução
                embed = discord.Embed(
                    title="⭐ LEVEL UP! ⭐",
                    description=f"Parabéns, {message.author.mention}!",
                    color=discord.Color.gold()
                )
                
                embed.add_field(
                    name="📊 Novo Nível",
                    value=f"Você alcançou o **nível {result['new_level']}**!",
                    inline=False
                )
                
                # Enviar como mensagem direta para evitar spam no canal
                try:
                    await message.author.send(embed=embed)
                except:
                    # Se não puder enviar DM, enviar no canal como uma mensagem efêmera
                    pass
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem de level up: {e}")
    
    @app_commands.command(name="perfil", description="Veja seu perfil de nível e estatísticas")
    @app_commands.describe(
        usuario="Usuário para ver o perfil (deixe em branco para ver o seu)"
    )
    async def perfil(self, interaction: discord.Interaction, usuario: discord.Member = None):
        """Exibe o perfil do usuário com nível, XP e estatísticas"""
        await interaction.response.defer(ephemeral=True)
        
        # Se não for especificado um usuário, mostrar o próprio perfil
        target_user = usuario or interaction.user
        target_id = target_user.id
        target_name = target_user.name
        
        # Verificar se está vendo o próprio perfil ou de outro usuário
        is_self = target_user.id == interaction.user.id
        
        try:
            # Verificar se o usuário existe no banco
            user = UserService.ensure_user_exists(str(target_id), target_name)
            
            if not user:
                embed = discord.Embed(
                    title="❌ ERRO AO ACESSAR PERFIL",
                    description="Não foi possível acessar os dados solicitados. Tente novamente mais tarde.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obter dados do usuário
            user_coins = user[2]  # coins
            is_premium = bool(user[3]) if len(user) > 3 else False
            xp = user[6] if len(user) > 6 else 0
            level = user[7] if len(user) > 7 else 1
            messages = user[8] if len(user) > 8 else 0
            
            # Obter informações detalhadas de nível
            success, level_info = UserService.get_level_info(str(target_id))
            
            if not success:
                level_info = {
                    "level": level,
                    "xp": xp,
                    "xp_for_next_level": 100,
                    "progress_percent": 0
                }
            
            # Criar barra de progresso visual
            progress_bar_length = 20
            filled_length = int(progress_bar_length * (float(level_info["progress_percent"]) / 100))
            progress_bar = '█' * filled_length + '░' * (progress_bar_length - filled_length)
            
            # Criar embed para o perfil
            embed = discord.Embed(
                title=f"👤 PERFIL DE {target_name.upper()}",
                description=f"Estatísticas e progresso do usuário:",
                color=discord.Color.gold() if is_premium else discord.Color.blue()
            )
            
            # Adicionar nível e XP
            embed.add_field(
                name=f"📊 NÍVEL {level_info['level']}",
                value=(
                    f"```fix\n"
                    f"XP: {level_info['xp']}/{level_info['xp_for_next_level']}\n"
                    f"[{progress_bar}] {float(level_info['progress_percent']):.1f}%\n"
                    f"```"
                ),
                inline=False
            )
            
            # Adicionar informações financeiras
            embed.add_field(
                name="💰 Coins",
                value=f"`{user_coins:,}`",
                inline=True
            )
            
            # Adicionar status premium
            embed.add_field(
                name="✨ Status",
                value=f"`{'Premium' if is_premium else 'Padrão'}`",
                inline=True
            )
            
            # Adicionar contagem de mensagens se disponível
            if messages:
                embed.add_field(
                    name="💬 Mensagens",
                    value=f"`{messages:,}`",
                    inline=True
                )
            
            # Adicionar estatísticas de transações se for o próprio usuário
            if is_self:
                try:
                    import sqlite3
                    conn = sqlite3.connect('database.db')
                    cursor = conn.cursor()
                    
                    # Contar total de transações
                    cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (str(target_id),))
                    transaction_count = cursor.fetchone()[0] or 0
                    
                    # Obter total recebido (valores positivos)
                    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND amount > 0", (str(target_id),))
                    received = cursor.fetchone()[0] or 0
                    
                    # Obter total gasto (valores negativos)
                    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND amount < 0", (str(target_id),))
                    spent = abs(cursor.fetchone()[0] or 0)
                    
                    cursor.close()
                    conn.close()
                    
                    embed.add_field(
                        name="📈 ESTATÍSTICAS FINANCEIRAS",
                        value=(
                            f"• Transações: **{transaction_count:,}**\n"
                            f"• Recebido: **{received:,}** coins\n"
                            f"• Gasto: **{spent:,}** coins\n"
                        ),
                        inline=False
                    )
                except Exception as e:
                    logger.error(f"Erro ao obter estatísticas: {e}")
            
            # Obter itens do inventário se for o próprio usuário
            if is_self:
                success, inventory = ShopService.get_user_inventory(str(target_id))
                
                if success and inventory:
                    # Contar itens por tipo
                    items_by_type = {}
                    for item in inventory:
                        item_type = item["type"]
                        if item_type not in items_by_type:
                            items_by_type[item_type] = 0
                        items_by_type[item_type] += 1
                    
                    # Listar itens no perfil
                    items_text = ""
                    for item_type, count in items_by_type.items():
                        type_name = item_type.replace("_", " ").title()
                        items_text += f"• {type_name}: **{count}** item(ns)\n"
                    
                    embed.add_field(
                        name="🎒 INVENTÁRIO",
                        value=items_text if items_text else "Nenhum item no inventário.",
                        inline=False
                    )
            
            # Adicionar avatar do usuário
            if target_user.avatar:
                embed.set_thumbnail(url=target_user.avatar.url)
            
            # Adicionar dicas para o próprio usuário
            if is_self:
                embed.set_footer(text="💡 Ganhe XP enviando mensagens e usando comandos! • Use /loja para comprar itens")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao processar perfil: {e}")
            embed = discord.Embed(
                title="❌ ERRO AO PROCESSAR PERFIL",
                description="Ocorreu um erro ao acessar o perfil solicitado. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="loja", description="Acesse a loja para comprar itens e melhorias")
    async def loja(self, interaction: discord.Interaction):
        """Exibe a loja de itens do bot"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar se o usuário existe
            user = UserService.ensure_user_exists(str(interaction.user.id), interaction.user.name)
            
            if not user:
                embed = discord.Embed(
                    title="❌ ERRO AO ACESSAR LOJA",
                    description="Não foi possível acessar sua conta. Tente novamente mais tarde.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obter saldo do usuário
            user_coins = user[2]
            
            # Obter itens da loja
            success, items = ShopService.get_all_items()
            
            if not success or not items:
                embed = discord.Embed(
                    title="🛍️ LOJA DE ITENS",
                    description="Não há itens disponíveis no momento. Volte mais tarde!",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Criar embed da loja
            embed = create_shop_embed(items, user_coins)
            
            # Criar view com filtragem de categorias
            view = ShopView(items, user_coins)
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao processar loja: {e}")
            embed = discord.Embed(
                title="❌ ERRO AO ACESSAR LOJA",
                description="Ocorreu um erro ao acessar a loja. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="inventario", description="Veja os itens que você possui")
    async def inventario(self, interaction: discord.Interaction):
        """Exibe o inventário do usuário"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar se o usuário existe
            user = UserService.ensure_user_exists(str(interaction.user.id), interaction.user.name)
            
            if not user:
                embed = discord.Embed(
                    title="❌ ERRO AO ACESSAR INVENTÁRIO",
                    description="Não foi possível acessar sua conta. Tente novamente mais tarde.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obter inventário do usuário
            success, inventory = ShopService.get_user_inventory(str(interaction.user.id))
            
            if not success or not inventory:
                embed = discord.Embed(
                    title="🎒 SEU INVENTÁRIO",
                    description="Você não possui nenhum item no momento.\nUse `/loja` para comprar itens!",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Criar embed do inventário
            embed = discord.Embed(
                title="🎒 SEU INVENTÁRIO",
                description=f"Você possui **{len(inventory)}** itens diferentes:",
                color=discord.Color.gold()
            )
            
            # Agrupar por tipo para melhor organização
            items_by_type = {}
            for item in inventory:
                item_type = item["type"]
                if item_type not in items_by_type:
                    items_by_type[item_type] = []
                items_by_type[item_type].append(item)
            
            # Adicionar cada tipo como um campo separado
            for item_type, items in items_by_type.items():
                # Obter nome amigável do tipo
                category_names = {
                    "daily_boost": "Bônus de Daily",
                    "xp_boost": "Bônus de XP",
                    "cooldown_reduction": "Redução de Cooldown",
                    "game_boost": "Bônus de Jogo",
                    "loss_protection": "Proteção",
                    "visual_effect": "Visual",
                    "title": "Títulos"
                }
                type_name = category_names.get(item_type, item_type.replace("_", " ").title())
                
                # Criar lista formatada de itens
                items_text = ""
                for item in items:
                    items_text += f"• **{item['name']}** (x{item['quantity']})\n"
                    items_text += f"  {item['description']}\n"
                
                embed.add_field(
                    name=f"📦 {type_name.upper()}",
                    value=items_text,
                    inline=False
                )
            
            embed.set_footer(text="Seus itens são aplicados automaticamente aos seus comandos.")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao processar inventário: {e}")
            embed = discord.Embed(
                title="❌ ERRO AO ACESSAR INVENTÁRIO",
                description="Ocorreu um erro ao acessar seu inventário. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Level(bot))