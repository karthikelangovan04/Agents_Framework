#!/usr/bin/env python3
"""Quick script to check database for user_id values."""
import asyncio
import asyncpg
import os

async def check_database():
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/copilot_adk_app")
    
    print("🔍 Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Check events table
        print("\n📊 LATEST EVENTS (Last 10):")
        print("-" * 80)
        events = await conn.fetch("""
            SELECT user_id, LEFT(event_type, 30) as event_type, created_at 
            FROM events 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        if not events:
            print("❌ No events found in database")
        else:
            for event in events:
                user_id = event['user_id']
                if user_id.startswith('thread_user_'):
                    status = "❌ THREAD USER"
                elif user_id.isdigit():
                    status = "✅ NUMERIC USER"
                else:
                    status = "⚠️ CUSTOM USER"
                
                print(f"{status} | user_id: {user_id[:30]:<30} | {event['event_type']:<30} | {event['created_at']}")
        
        # Check unique user_ids
        print("\n📊 UNIQUE USER IDs:")
        print("-" * 80)
        users = await conn.fetch("""
            SELECT DISTINCT user_id, COUNT(*) as count
            FROM events 
            GROUP BY user_id 
            ORDER BY count DESC
        """)
        
        for user in users:
            user_id = user['user_id']
            if user_id.startswith('thread_user_'):
                status = "❌"
            elif user_id.isdigit():
                status = "✅"
            else:
                status = "⚠️"
            print(f"{status} user_id: {user_id} (count: {user['count']})")
        
        print("\n" + "=" * 80)
        print("✅ EXPECTED: user_id = '3' (numeric)")
        print("❌ PROBLEM: user_id = 'thread_user_xxx'")
        print("=" * 80)
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_database())
