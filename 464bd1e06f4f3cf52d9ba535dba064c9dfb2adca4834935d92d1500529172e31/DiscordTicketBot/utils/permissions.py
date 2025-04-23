"""
Permissions module for the Discord bot.
Handles permission management for channels and categories.
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger('discord_bot.permissions')

# Define standard permissions
STANDARD_PERMISSIONS = [
    {"id": "view", "name": "Ver Canal", "default": True},
    {"id": "send", "name": "Enviar Mensagens", "default": True},
    {"id": "read_history", "name": "Ler Histórico", "default": True},
    {"id": "embed", "name": "Incorporar Links", "default": True},
    {"id": "attach", "name": "Anexar Arquivos", "default": True},
    {"id": "mention", "name": "Mencionar @everyone", "default": False},
    {"id": "external_emoji", "name": "Usar Emojis Externos", "default": True},
    {"id": "react", "name": "Adicionar Reações", "default": True},
    {"id": "manage", "name": "Gerenciar Canal", "default": False},
    {"id": "manage_messages", "name": "Gerenciar Mensagens", "default": False},
]

# Additional voice channel permissions
VOICE_PERMISSIONS = [
    {"id": "connect", "name": "Conectar", "default": True},
    {"id": "speak", "name": "Falar", "default": True},
    {"id": "stream", "name": "Compartilhar Tela", "default": True},
    {"id": "use_voice_activity", "name": "Usar Detecção de Voz", "default": True},
    {"id": "priority_speaker", "name": "Voz Prioritária", "default": False},
    {"id": "mute_members", "name": "Silenciar Membros", "default": False},
    {"id": "deafen_members", "name": "Ensurdecer Membros", "default": False},
    {"id": "move_members", "name": "Mover Membros", "default": False},
]

class PermissionManager:
    """
    Class for managing permissions for channels and categories.
    Uses a file-based storage system for persistence.
    """
    
    def __init__(self, storage_dir: str = "data"):
        """Initialize the permission manager with a directory for data files."""
        self.storage_dir = storage_dir
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    def _get_permissions_file(self, guild_id: str) -> str:
        """Get the file path for a guild's permission data."""
        return os.path.join(self.storage_dir, f"permissions_{guild_id}.json")
    
    def _load_permissions_data(self, guild_id: str) -> Dict[str, Any]:
        """Load a guild's permission data from file."""
        file_path = self._get_permissions_file(guild_id)
        
        if not os.path.exists(file_path):
            return {"channels": {}, "categories": {}}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading permissions data: {e}")
            return {"channels": {}, "categories": {}}
    
    def _save_permissions_data(self, guild_id: str, data: Dict[str, Any]):
        """Save a guild's permission data to file."""
        file_path = self._get_permissions_file(guild_id)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving permissions data: {e}")
    
    def get_permissions(self, guild_id: str, item_id: str, item_type: str, channel_type: str = "texto") -> List[Dict[str, Any]]:
        """
        Get permissions for a channel or category.
        
        Args:
            guild_id: The ID of the guild
            item_id: The ID of the channel or category
            item_type: The type of item ("channel" or "category")
            channel_type: The type of channel ("texto" or "voz") - only relevant for channels
            
        Returns:
            A list of permission data
        """
        perms_data = self._load_permissions_data(guild_id)
        item_data = perms_data["channels" if item_type == "channel" else "categories"]
        
        # If the item doesn't exist in the permissions data, create default permissions
        if item_id not in item_data:
            permissions = STANDARD_PERMISSIONS.copy()
            if item_type == "channel" and channel_type == "voz":
                permissions.extend(VOICE_PERMISSIONS)
            
            # Set default values
            for perm in permissions:
                perm["enabled"] = perm["default"]
            
            # Save to storage
            if item_type == "channel":
                perms_data["channels"][item_id] = {"permissions": permissions}
            else:
                perms_data["categories"][item_id] = {"permissions": permissions}
            
            self._save_permissions_data(guild_id, perms_data)
            return permissions
        
        return item_data[item_id]["permissions"]
    
    def set_permission(self, guild_id: str, item_id: str, item_type: str, permission_id: str, enabled: bool) -> bool:
        """
        Set a permission for a channel or category.
        
        Args:
            guild_id: The ID of the guild
            item_id: The ID of the channel or category
            item_type: The type of item ("channel" or "category")
            permission_id: The ID of the permission to set
            enabled: Whether the permission is enabled
            
        Returns:
            True if successful, False otherwise
        """
        perms_data = self._load_permissions_data(guild_id)
        item_data = perms_data["channels" if item_type == "channel" else "categories"]
        
        # If the item doesn't exist in the permissions data, get default permissions first
        if item_id not in item_data:
            self.get_permissions(guild_id, item_id, item_type)
            perms_data = self._load_permissions_data(guild_id)
            item_data = perms_data["channels" if item_type == "channel" else "categories"]
        
        # Find and update the permission
        for perm in item_data[item_id]["permissions"]:
            if perm["id"] == permission_id:
                perm["enabled"] = enabled
                self._save_permissions_data(guild_id, perms_data)
                return True
        
        return False
    
    def get_permission(self, guild_id: str, item_id: str, item_type: str, permission_id: str) -> Optional[bool]:
        """
        Get a specific permission value for a channel or category.
        
        Args:
            guild_id: The ID of the guild
            item_id: The ID of the channel or category
            item_type: The type of item ("channel" or "category")
            permission_id: The ID of the permission to get
            
        Returns:
            True if the permission is enabled, False if disabled, None if not found
        """
        permissions = self.get_permissions(guild_id, item_id, item_type)
        
        for perm in permissions:
            if perm["id"] == permission_id:
                return perm["enabled"]
        
        return None
    
    def delete_item_permissions(self, guild_id: str, item_id: str, item_type: str) -> bool:
        """
        Delete permissions for a channel or category.
        
        Args:
            guild_id: The ID of the guild
            item_id: The ID of the channel or category
            item_type: The type of item ("channel" or "category")
            
        Returns:
            True if successful, False otherwise
        """
        perms_data = self._load_permissions_data(guild_id)
        item_data = perms_data["channels" if item_type == "channel" else "categories"]
        
        if item_id not in item_data:
            return False
        
        del item_data[item_id]
        self._save_permissions_data(guild_id, perms_data)
        return True
