#!/usr/bin/env python3
"""Example: Storing A2A conversations in a database (similar to ADK DatabaseSessionService)."""

import sqlite3
import json
from datetime import datetime
from typing import Optional
from python_a2a import Conversation, Message, TextContent, MessageRole

class ConversationStorage:
    """SQLite-based conversation storage (similar to ADK DatabaseSessionService)."""
    
    def __init__(self, db_path: str = "a2a_conversations.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                agent_id TEXT,
                app_name TEXT,
                conversation_data TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id 
            ON conversations(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_id 
            ON conversations(agent_id)
        """)
        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {self.db_path}")
    
    def save_conversation(
        self,
        conversation_id: str,
        user_id: str,
        conversation: Conversation,
        agent_id: Optional[str] = None,
        app_name: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """Save a conversation to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        conversation_json = conversation.to_json()
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT OR REPLACE INTO conversations 
            (id, user_id, agent_id, app_name, conversation_data, metadata, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            conversation_id,
            user_id,
            agent_id,
            app_name,
            conversation_json,
            metadata_json,
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
        print(f"✅ Saved conversation: {conversation_id}")
    
    def load_conversation(
        self,
        conversation_id: str
    ) -> Optional[Conversation]:
        """Load a conversation from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT conversation_data FROM conversations
            WHERE id = ?
        """, (conversation_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            conversation = Conversation.from_json(row[0])
            print(f"✅ Loaded conversation: {conversation_id} ({len(conversation.messages)} messages)")
            return conversation
        print(f"❌ Conversation not found: {conversation_id}")
        return None
    
    def list_conversations(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> list:
        """List conversations, optionally filtered by user_id or agent_id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if user_id and agent_id:
            cursor.execute("""
                SELECT id, user_id, agent_id, app_name, created_at, updated_at
                FROM conversations
                WHERE user_id = ? AND agent_id = ?
                ORDER BY updated_at DESC
            """, (user_id, agent_id))
        elif user_id:
            cursor.execute("""
                SELECT id, user_id, agent_id, app_name, created_at, updated_at
                FROM conversations
                WHERE user_id = ?
                ORDER BY updated_at DESC
            """, (user_id,))
        elif agent_id:
            cursor.execute("""
                SELECT id, user_id, agent_id, app_name, created_at, updated_at
                FROM conversations
                WHERE agent_id = ?
                ORDER BY updated_at DESC
            """, (agent_id,))
        else:
            cursor.execute("""
                SELECT id, user_id, agent_id, app_name, created_at, updated_at
                FROM conversations
                ORDER BY updated_at DESC
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "user_id": row[1],
                "agent_id": row[2],
                "app_name": row[3],
                "created_at": row[4],
                "updated_at": row[5]
            }
            for row in rows
        ]

def main():
    """Demonstrate conversation storage."""
    print("=" * 60)
    print("A2A Conversation Storage Example")
    print("(Similar to ADK DatabaseSessionService)")
    print("=" * 60)
    
    # Initialize storage
    storage = ConversationStorage("a2a_conversations.db")
    
    # Create a conversation
    print("\n1. Creating a conversation...")
    conversation = Conversation()
    
    # Add messages using the conversation's helper methods
    conversation.add_message(
        conversation.create_text_message("Hello! My name is Alice.", role=MessageRole.USER)
    )
    conversation.add_message(
        conversation.create_text_message("Hi Alice! Nice to meet you.", role=MessageRole.AGENT)
    )
    conversation.add_message(
        conversation.create_text_message("What's the weather today?", role=MessageRole.USER)
    )
    conversation.add_message(
        conversation.create_text_message("I don't have access to weather data, but I can help with other things!", role=MessageRole.AGENT)
    )
    
    # Save conversation
    print("\n2. Saving conversation to database...")
    storage.save_conversation(
        conversation_id="conv_001",
        user_id="user_alice",
        conversation=conversation,
        agent_id="agent_helper",
        app_name="demo_app",
        metadata={"source": "example", "version": "1.0"}
    )
    
    # Load conversation
    print("\n3. Loading conversation from database...")
    loaded_conv = storage.load_conversation("conv_001")
    
    if loaded_conv:
        print(f"\n   Conversation has {len(loaded_conv.messages)} messages:")
        for i, msg in enumerate(loaded_conv.messages, 1):
            role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
            text = ""
            for content in msg.content:
                if isinstance(content, TextContent):
                    text += content.text
            print(f"   {i}. [{role}]: {text[:50]}...")
    
    # List conversations
    print("\n4. Listing all conversations...")
    conversations = storage.list_conversations(user_id="user_alice")
    print(f"   Found {len(conversations)} conversation(s) for user_alice:")
    for conv in conversations:
        print(f"   - {conv['id']} (agent: {conv['agent_id']}, updated: {conv['updated_at']})")
    
    # Add more messages and update
    print("\n5. Adding new message and updating conversation...")
    if loaded_conv:
        loaded_conv.add_message(
            loaded_conv.create_text_message("Can you help me with math?", role=MessageRole.USER)
        )
        loaded_conv.add_message(
            loaded_conv.create_text_message("Of course! What math problem do you need help with?", role=MessageRole.AGENT)
        )
        
        storage.save_conversation(
            conversation_id="conv_001",
            user_id="user_alice",
            conversation=loaded_conv,
            agent_id="agent_helper",
            app_name="demo_app"
        )
    
    # Reload and verify
    print("\n6. Reloading updated conversation...")
    updated_conv = storage.load_conversation("conv_001")
    if updated_conv:
        print(f"   Updated conversation now has {len(updated_conv.messages)} messages")
    
    print("\n" + "=" * 60)
    print("✅ Example complete!")
    print("=" * 60)
    print("\nNote: This demonstrates how A2A conversations can be stored")
    print("in a database, similar to how ADK stores sessions via DatabaseSessionService.")

if __name__ == "__main__":
    main()
