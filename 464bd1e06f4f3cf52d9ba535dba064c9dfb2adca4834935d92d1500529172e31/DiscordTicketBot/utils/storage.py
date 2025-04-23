"""
Storage module for the Discord bot.
Handles the storage of channels, categories, and their associated data.
"""

import json
import os
import uuid
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger('discord_bot.storage')

class ChannelStorage:
    """
    Class for storing and retrieving channel and category data.
    Uses a file-based storage system for persistence.
    """
    
    def __init__(self, storage_dir: str = "data"):
        """Initialize the storage with a directory for data files."""
        self.storage_dir = storage_dir
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    def _get_guild_file(self, guild_id: str) -> str:
        """Get the file path for a guild's data."""
        return os.path.join(self.storage_dir, f"guild_{guild_id}_temp.json")
    
    def _load_guild_data(self, guild_id: str) -> Dict[str, Any]:
        """Load a guild's data from file."""
        file_path = self._get_guild_file(guild_id)
        
        if not os.path.exists(file_path):
            return {"categories": {}, "channels": {}}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Garantir estrutura correta (corrigindo diferenças entre dicionários e arrays)
                if isinstance(data.get("categories"), list):
                    categories_dict = {}
                    for category in data["categories"]:
                        if "id" in category:
                            categories_dict[category["id"]] = category
                    data["categories"] = categories_dict
                
                if isinstance(data.get("channels"), list):
                    channels_dict = {}
                    for channel in data["channels"]:
                        if "id" in channel:
                            channels_dict[channel["id"]] = channel
                    data["channels"] = channels_dict
                
                return data
        except Exception as e:
            logger.error(f"Error loading guild data: {e}")
            return {"categories": {}, "channels": {}}
    
    def _save_guild_data(self, guild_id: str, data: Dict[str, Any]):
        """Save a guild's data to file."""
        file_path = self._get_guild_file(guild_id)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving guild data: {e}")
    
    def add_category(self, guild_id: str, name: str) -> str:
        """
        Add a new category to storage.
        
        Args:
            guild_id: The ID of the guild
            name: The name of the category
            
        Returns:
            The ID of the created category
        """
        guild_data = self._load_guild_data(guild_id)
        category_id = str(uuid.uuid4())
        
        guild_data["categories"][category_id] = {
            "id": category_id,
            "name": name,
            "created_at": import_time()
        }
        
        self._save_guild_data(guild_id, guild_data)
        return category_id
    
    def update_category(self, guild_id: str, category_id: str, name: str) -> bool:
        """
        Update a category in storage.
        
        Args:
            guild_id: The ID of the guild
            category_id: The ID of the category to update
            name: The new name of the category
            
        Returns:
            True if successful, False otherwise
        """
        guild_data = self._load_guild_data(guild_id)
        
        if category_id not in guild_data["categories"]:
            return False
        
        guild_data["categories"][category_id]["name"] = name
        guild_data["categories"][category_id]["updated_at"] = import_time()
        
        self._save_guild_data(guild_id, guild_data)
        return True
    
    def delete_category(self, guild_id: str, category_id: str) -> bool:
        """
        Delete a category from storage.
        
        Args:
            guild_id: The ID of the guild
            category_id: The ID of the category to delete
            
        Returns:
            True if successful, False otherwise
        """
        guild_data = self._load_guild_data(guild_id)
        
        if category_id not in guild_data["categories"]:
            return False
        
        # Delete the category
        del guild_data["categories"][category_id]
        
        # Update channels that belong to this category
        for channel_id, channel in guild_data["channels"].items():
            if channel.get("category_id") == category_id:
                channel["category_id"] = None
        
        self._save_guild_data(guild_id, guild_data)
        return True
    
    def get_category(self, guild_id: str, category_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a category from storage.
        
        Args:
            guild_id: The ID of the guild
            category_id: The ID of the category to get
            
        Returns:
            The category data, or None if not found
        """
        guild_data = self._load_guild_data(guild_id)
        
        if category_id not in guild_data["categories"]:
            return None
        
        return guild_data["categories"][category_id]
    
    def get_all_categories(self, guild_id: str) -> List[Dict[str, Any]]:
        """
        Get all categories for a guild.
        
        Args:
            guild_id: The ID of the guild
            
        Returns:
            A list of category data
        """
        guild_data = self._load_guild_data(guild_id)
        return list(guild_data["categories"].values())
    
    def add_channel(self, guild_id: str, name: str, channel_type: str, description: str = "", category_id: Optional[str] = None) -> str:
        """
        Add a new channel to storage.
        
        Args:
            guild_id: The ID of the guild
            name: The name of the channel
            channel_type: The type of channel ("texto" or "voz")
            description: The description of the channel
            category_id: The ID of the category the channel belongs to
            
        Returns:
            The ID of the created channel
        """
        guild_data = self._load_guild_data(guild_id)
        channel_id = str(uuid.uuid4())
        
        # Validate category_id if provided
        if category_id and category_id not in guild_data["categories"]:
            category_id = None
        
        guild_data["channels"][channel_id] = {
            "id": channel_id,
            "name": name,
            "type": channel_type,
            "description": description,
            "category_id": category_id,
            "created_at": import_time()
        }
        
        self._save_guild_data(guild_id, guild_data)
        return channel_id
    
    def update_channel(self, guild_id: str, channel_id: str, name: str, description: str = "", category_id: Optional[str] = None) -> bool:
        """
        Update a channel in storage.
        
        Args:
            guild_id: The ID of the guild
            channel_id: The ID of the channel to update
            name: The new name of the channel
            description: The new description of the channel
            category_id: The new category ID of the channel
            
        Returns:
            True if successful, False otherwise
        """
        guild_data = self._load_guild_data(guild_id)
        
        if channel_id not in guild_data["channels"]:
            return False
        
        # Validate category_id if provided
        if category_id is not None:
            if category_id and category_id not in guild_data["categories"]:
                category_id = None
            guild_data["channels"][channel_id]["category_id"] = category_id
        
        guild_data["channels"][channel_id]["name"] = name
        guild_data["channels"][channel_id]["description"] = description
        guild_data["channels"][channel_id]["updated_at"] = import_time()
        
        self._save_guild_data(guild_id, guild_data)
        return True
    
    def delete_channel(self, guild_id: str, channel_id: str) -> bool:
        """
        Delete a channel from storage.
        
        Args:
            guild_id: The ID of the guild
            channel_id: The ID of the channel to delete
            
        Returns:
            True if successful, False otherwise
        """
        guild_data = self._load_guild_data(guild_id)
        
        if channel_id not in guild_data["channels"]:
            return False
        
        del guild_data["channels"][channel_id]
        
        self._save_guild_data(guild_id, guild_data)
        return True
    
    def get_channel(self, guild_id: str, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a channel from storage.
        
        Args:
            guild_id: The ID of the guild
            channel_id: The ID of the channel to get
            
        Returns:
            The channel data, or None if not found
        """
        guild_data = self._load_guild_data(guild_id)
        
        if channel_id not in guild_data["channels"]:
            return None
        
        return guild_data["channels"][channel_id]
    
    def get_all_channels(self, guild_id: str, category_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all channels for a guild, optionally filtered by category.
        
        Args:
            guild_id: The ID of the guild
            category_id: The ID of the category to filter by
            
        Returns:
            A list of channel data
        """
        guild_data = self._load_guild_data(guild_id)
        channels = list(guild_data["channels"].values())
        
        if category_id is not None:
            channels = [c for c in channels if c.get("category_id") == category_id]
        
        return channels
        
    def clear_guild_data(self, guild_id: str) -> bool:
        """
        Completely clear all data for a guild.
        
        Args:
            guild_id: The ID of the guild to clear data for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove qualquer arquivo de dados antigos
            file_path = self._get_guild_file(guild_id)
            old_file_path = os.path.join(self.storage_dir, f"guild_{guild_id}.json")
            
            # Remover arquivos existentes se houver
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Removed temporary file for guild {guild_id}")
                
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
                logger.info(f"Removed old file for guild {guild_id}")
            
            # Create empty data structure
            empty_data = {
                "categories": {},
                "channels": {}
            }
            
            # Save empty data
            self._save_guild_data(guild_id, empty_data)
            
            logger.info(f"Cleared all data for guild {guild_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing data for guild {guild_id}: {str(e)}")
            return False

def import_time() -> str:
    """Get the current time as a string."""
    from datetime import datetime
    return datetime.utcnow().isoformat()
