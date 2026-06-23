"""
CircuitSage — Session Memory Management
Maintains a sliding window of the last 10 conversational turns (user inputs and agent replies)
for context-aware routing and multi-agent interaction.
"""

import json
import os
from typing import List, Dict, Any
from datetime import datetime

class SessionMemory:
    """
    Manages session history for CircuitSage.
    Keeps a maximum of 10 turns (20 messages: 10 user and 10 assistant).
    Supports optional persistence to a JSON file.
    """
    def __init__(self, session_id: str, persistence_dir: str = "memory"):
        self.session_id = session_id
        self.persistence_dir = persistence_dir
        self.filepath = os.path.join(persistence_dir, f"session_{session_id}.json")
        self.messages: List[Dict[str, Any]] = []
        self._load_memory()

    def _load_memory(self):
        """Loads memory from a file if it exists, otherwise starts fresh."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.messages = data.get("messages", [])
            except Exception as e:
                # Handle gracefully as per CircuitSage CONTEXT.md
                print(f"[CircuitSage·Memory] Error loading memory: {e}")
                self.messages = []

    def _save_memory(self):
        """Saves current memory window to a JSON file."""
        if not os.path.exists(self.persistence_dir):
            try:
                os.makedirs(self.persistence_dir, exist_ok=True)
            except Exception as e:
                print(f"[CircuitSage·Memory] Error creating directory: {e}")
                return

        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "session_id": self.session_id,
                    "last_updated": datetime.now().isoformat(),
                    "messages": self.messages
                }, f, indent=4)
        except Exception as e:
            print(f"[CircuitSage·Memory] Error saving memory: {e}")

    def add_message(self, role: str, content: str):
        """
        Adds a message to the conversation history.
        Enforces a maximum of 20 messages (10 user inputs + 10 assistant responses).
        
        Args:
            role: "user" or "assistant"
            content: The text message content (max 500 chars limit is handled at agent input level)
        """
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Enforce sliding window of last 10 turns (user+assistant = 20 messages)
        if len(self.messages) > 20:
            self.messages = self.messages[-20:]
            
        self._save_memory()

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns the current conversation history."""
        return self.messages

    def clear(self):
        """Clears the current conversation history."""
        self.messages = []
        if os.path.exists(self.filepath):
            try:
                os.remove(self.filepath)
            except Exception as e:
                print(f"[CircuitSage·Memory] Error clearing file: {e}")
