import discord
from typing import Union

def create_config_embed(title: str, description: str, color: Union[discord.Color, str] = discord.Color.blue()) -> discord.Embed:
    """Create a standardized embed for configuration panels"""
    # Convert string color to discord.Color
    if isinstance(color, str):
        color_map = {
            "red": discord.Color.red(),
            "green": discord.Color.green(),
            "blue": discord.Color.blue(),
            "yellow": discord.Color.gold(),
            "purple": discord.Color.purple(),
            "black": discord.Color.dark_grey(),
            "white": discord.Color.light_grey()
        }
        embed_color = color_map.get(color.lower(), discord.Color.blue())
    else:
        embed_color = color
    
    # Create embed
    embed = discord.Embed(
        title=title,
        description=description,
        color=embed_color
    )
    
    embed.set_footer(text="Discord Ticket System")
    
    return embed

def create_ticket_embed(title: str, description: str, color: Union[discord.Color, str] = discord.Color.blue()) -> discord.Embed:
    """Create a standardized embed for ticket messages"""
    # Convert string color to discord.Color
    if isinstance(color, str):
        color_map = {
            "red": discord.Color.red(),
            "green": discord.Color.green(),
            "blue": discord.Color.blue(),
            "yellow": discord.Color.gold(),
            "purple": discord.Color.purple(),
            "black": discord.Color.dark_grey(),
            "white": discord.Color.light_grey()
        }
        embed_color = color_map.get(color.lower(), discord.Color.blue())
    else:
        embed_color = color
    
    # Create embed
    embed = discord.Embed(
        title=title,
        description=description,
        color=embed_color
    )
    
    embed.set_footer(text="Ticket System • Use os botões abaixo para gerenciar o ticket")
    
    return embed

def create_panel_preview(panel_data: dict) -> str:
    """Create a text preview of a panel"""
    title = panel_data.get("title", "Título não definido")
    description = panel_data.get("description", "Descrição não definida")
    color = panel_data.get("color", "blue")
    
    # Support role
    support_role_id = panel_data.get("support_role_id")
    support_role_text = f"<@&{support_role_id}>" if support_role_id else "Não definido"
    
    # Category 
    category_id = panel_data.get("category_id")
    category_text = f"<#{category_id}>" if category_id else "Não definido"
    
    # Interaction type
    interaction_type = panel_data.get("interaction_type", "button")
    interaction_text = "Botão" if interaction_type == "button" else "Dropdown"
    
    # Create preview text
    preview = f"**Título:** {title}\n"
    preview += f"**Descrição:** {description}\n"
    preview += f"**Cor:** {color.capitalize()}\n"
    preview += f"**Cargo de Suporte:** {support_role_text}\n"
    preview += f"**Categoria:** {category_text}\n"
    preview += f"**Tipo de Interação:** {interaction_text}\n"
    
    # Add button or dropdown details
    if interaction_type == "button":
        button_style = panel_data.get("button_style", "primary")
        button_emoji = panel_data.get("button_emoji", "🎫")
        button_text = panel_data.get("button_text", "Abrir Ticket")
        
        preview += f"**Estilo do Botão:** {button_style.capitalize()}\n"
        preview += f"**Emoji do Botão:** {button_emoji}\n"
        preview += f"**Texto do Botão:** {button_text}\n"
    else:
        dropdown_placeholder = panel_data.get("dropdown_placeholder", "Selecione uma opção")
        dropdown_options = panel_data.get("dropdown_options", [])
        
        preview += f"**Placeholder do Dropdown:** {dropdown_placeholder}\n"
        preview += f"**Opções do Dropdown:** {len(dropdown_options)} opção(ões)\n"
    
    return preview
