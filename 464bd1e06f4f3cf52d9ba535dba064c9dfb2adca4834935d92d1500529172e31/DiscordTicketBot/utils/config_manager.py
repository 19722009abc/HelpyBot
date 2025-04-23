import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger('ticket_bot.config')

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# File paths
PANELS_FILE = 'data/panels.json'
TICKETS_FILE = 'data/tickets.json'
CONFIGS_FILE = 'data/configs.json'

# In-memory edit sessions
EDIT_SESSIONS = {}

def _load_json(file_path: str) -> dict:
    """Load JSON data from file, create if not exists"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create with empty structure
            empty_data = {}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(empty_data, f, indent=2)
            return empty_data
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return {}

def _save_json(file_path: str, data: dict) -> bool:
    """Save JSON data to file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False

def initialize_guild_config(guild_id: Union[str, int]) -> None:
    """Initialize guild configuration with default values"""
    guild_id = str(guild_id)
    
    # Load current configs
    configs = _load_json(CONFIGS_FILE)
    
    # Initialize guild settings if not exists
    if guild_id not in configs:
        configs[guild_id] = {
            "settings": {
                "allow_member_close": False,
                "show_priority_button": True,
                "show_notify_button": True,
                "show_archive_button": True,
                "show_claim_button": True,
                "show_transcript_button": True,
                "auto_archive_on_close": False,
                "notify_on_ticket_open": False,
                "max_tickets_per_user": 1,
                "inactivity_close_time": 72,
                "require_reason_on_close": False,
                "ticket_name_format": "ticket-{number}"
            }
        }
        
        # Save to file
        _save_json(CONFIGS_FILE, configs)
        logger.info(f"Initialized configuration for guild {guild_id}")

def get_next_ticket_number(guild_id: str) -> int:
    """Get the next available ticket number for a guild"""
    # Load current configs
    configs = _load_json(CONFIGS_FILE)
    
    # Initialize guild settings if not exists
    if guild_id not in configs:
        initialize_guild_config(guild_id)
        configs = _load_json(CONFIGS_FILE)
    
    # Initialize or increment ticket counter
    if "last_ticket_number" not in configs[guild_id]:
        configs[guild_id]["last_ticket_number"] = 1
    else:
        configs[guild_id]["last_ticket_number"] += 1
    
    ticket_number = configs[guild_id]["last_ticket_number"]
    
    # Save to file
    _save_json(CONFIGS_FILE, configs)
    
    return ticket_number

def get_config(guild_id: str) -> dict:
    """Get guild configuration"""
    # Load current configs
    configs = _load_json(CONFIGS_FILE)
    
    # Initialize guild settings if not exists
    if guild_id not in configs:
        initialize_guild_config(guild_id)
        configs = _load_json(CONFIGS_FILE)
    
    return configs[guild_id].get("settings", {})

def update_config(guild_id: str, key: str, value: Any) -> bool:
    """Update a specific configuration setting"""
    # Load current configs
    configs = _load_json(CONFIGS_FILE)
    
    # Initialize guild settings if not exists
    if guild_id not in configs:
        initialize_guild_config(guild_id)
        configs = _load_json(CONFIGS_FILE)
    
    # Update the setting
    if "settings" not in configs[guild_id]:
        configs[guild_id]["settings"] = {}
    
    configs[guild_id]["settings"][key] = value
    
    # Save to file
    result = _save_json(CONFIGS_FILE, configs)
    if result:
        logger.info(f"Updated config {key} to {value} for guild {guild_id}")
    
    return result

def get_panel_data(guild_id: str, panel_id: str) -> Optional[dict]:
    """Get data for a specific panel"""
    # Load panels data
    panels = _load_json(PANELS_FILE)
    
    # Check if guild and panel exist
    if guild_id in panels and panel_id in panels[guild_id]:
        return panels[guild_id][panel_id]
    
    return None

def get_all_panels(guild_id: str) -> dict:
    """Get all panels for a guild"""
    # Load panels data
    panels = _load_json(PANELS_FILE)
    
    # Return guild panels or empty dict
    return panels.get(guild_id, {})

def update_panel_data(guild_id: str, panel_id: str, panel_data: dict) -> bool:
    """Update data for a specific panel"""
    # Load panels data
    panels = _load_json(PANELS_FILE)
    
    # Initialize guild if not exists
    if guild_id not in panels:
        panels[guild_id] = {}
    
    # Update panel data
    panels[guild_id][panel_id] = panel_data
    
    # Save to file
    result = _save_json(PANELS_FILE, panels)
    if result:
        logger.info(f"Updated panel {panel_id} for guild {guild_id}")
    
    return result

def create_panel_data(guild_id: str, panel_id: str, panel_data: dict) -> bool:
    """Create a new panel"""
    return update_panel_data(guild_id, panel_id, panel_data)

def delete_panel_data(guild_id: str, panel_id: str) -> bool:
    """Delete a panel"""
    # Load panels data
    panels = _load_json(PANELS_FILE)
    
    # Check if guild and panel exist
    if guild_id in panels and panel_id in panels[guild_id]:
        # Delete panel
        del panels[guild_id][panel_id]
        
        # Save to file
        result = _save_json(PANELS_FILE, panels)
        if result:
            logger.info(f"Deleted panel {panel_id} from guild {guild_id}")
        
        return result
    
    return False

def get_ticket_data(guild_id: str, channel_id: str) -> Optional[dict]:
    """Get data for a specific ticket"""
    # Load tickets data
    tickets = _load_json(TICKETS_FILE)
    
    # Check if guild and ticket exist
    if guild_id in tickets and channel_id in tickets[guild_id]:
        return tickets[guild_id][channel_id]
    
    return None

def count_user_tickets(guild_id: str, user_id: str, guild=None) -> int:
    """Count open tickets for a user
    
    Args:
        guild_id (str): ID do servidor
        user_id (str): ID do usuário
        guild (discord.Guild, optional): Instância do servidor para verificar existência do canal. Defaults to None.
    
    Returns:
        int: Número de tickets abertos
    """
    # Load tickets data
    tickets = _load_json(TICKETS_FILE)
    
    # Check if guild exists
    if guild_id not in tickets:
        return 0
    
    # Count open tickets
    count = 0
    invalid_tickets = []
    
    for channel_id, ticket in tickets[guild_id].items():
        if ticket.get("user_id") == user_id and ticket.get("status") == "open":
            # Verificar se o canal ainda existe no servidor
            if guild is not None:
                try:
                    channel = guild.get_channel(int(channel_id))
                    if channel is None:
                        # Canal não existe mais, marcar para remoção
                        invalid_tickets.append(channel_id)
                        logger.info(f"Ticket {channel_id} não existe mais no servidor {guild_id}, será removido da contagem")
                        continue  # Pular este ticket na contagem
                except Exception as e:
                    logger.error(f"Erro ao verificar canal {channel_id}: {e}")
                    # Por segurança, não conta se não conseguir verificar
                    continue
                    
            # Contar apenas tickets válidos (canal existe ou não foi possível verificar)
            count += 1
    
    # Remover tickets inválidos da base de dados (canais que não existem mais)
    if guild is not None and invalid_tickets:
        for channel_id in invalid_tickets:
            delete_ticket_data(guild_id, channel_id)
            logger.info(f"Ticket {channel_id} foi removido da base de dados por não existir mais")
    
    return count

def update_ticket_data(guild_id: str, channel_id: str, ticket_data: dict) -> bool:
    """Update data for a specific ticket"""
    # Load tickets data
    tickets = _load_json(TICKETS_FILE)
    
    # Initialize guild if not exists
    if guild_id not in tickets:
        tickets[guild_id] = {}
    
    # Update ticket data
    tickets[guild_id][channel_id] = ticket_data
    
    # Save to file
    result = _save_json(TICKETS_FILE, tickets)
    if result:
        logger.info(f"Updated ticket {channel_id} for guild {guild_id}")
    
    return result

def create_ticket_data(guild_id: str, channel_id: str, ticket_data: dict) -> bool:
    """Create a new ticket"""
    return update_ticket_data(guild_id, channel_id, ticket_data)

def delete_ticket_data(guild_id: str, channel_id: str) -> bool:
    """Delete a ticket"""
    # Load tickets data
    tickets = _load_json(TICKETS_FILE)
    
    # Check if guild and ticket exist
    if guild_id in tickets and channel_id in tickets[guild_id]:
        # Delete ticket
        del tickets[guild_id][channel_id]
        
        # Save to file
        result = _save_json(TICKETS_FILE, tickets)
        if result:
            logger.info(f"Deleted ticket {channel_id} from guild {guild_id}")
        
        return result
    
    return False

def get_edit_session(user_id: str, guild_id: str) -> Optional[dict]:
    """Get panel edit session for a user"""
    session_key = f"{user_id}:{guild_id}"
    return EDIT_SESSIONS.get(session_key)

def initialize_edit_session(user_id: str, guild_id: str, panel_data: dict) -> None:
    """Initialize or update edit session for a user"""
    session_key = f"{user_id}:{guild_id}"
    EDIT_SESSIONS[session_key] = panel_data

def update_edit_session(user_id: str, guild_id: str, panel_data: dict) -> None:
    """Update edit session for a user"""
    session_key = f"{user_id}:{guild_id}"
    EDIT_SESSIONS[session_key] = panel_data

def clean_edit_session(user_id: str, guild_id: str) -> None:
    """Clean up edit session for a user"""
    session_key = f"{user_id}:{guild_id}"
    if session_key in EDIT_SESSIONS:
        del EDIT_SESSIONS[session_key]
