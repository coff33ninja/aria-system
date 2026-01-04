"""
Shared memory tools for all maids.
Each maid can remember, recall, and learn within their own domain.
Also includes the dismiss tool so maids can return control to Aria.
"""
from livekit.agents import function_tool, RunContext
from typing import Optional
import logging

logger = logging.getLogger("maids.memory")


def create_memory_tools(maid_instance):
    """
    Create memory tools bound to a specific maid instance.
    Returns a list of function tools that use the maid's personal memory.
    """
    
    @function_tool()
    async def remember_this(
        context: RunContext,
        content: str,
        category: str = "general"
    ) -> str:
        """
        Remember something for later.
        
        Args:
            content: What to remember
            category: Category (general, user_preference, task, research, etc.)
        """
        maid_instance.memory.remember(content, category)
        return f"I'll remember that: '{content[:50]}...'"
    
    @function_tool()
    async def recall_memories(
        context: RunContext,
        query: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5
    ) -> str:
        """
        Recall past memories.
        
        Args:
            query: Search term (optional)
            category: Filter by category (optional)
            limit: Max results to return
        """
        memories = maid_instance.memory.recall(query, category, limit)
        if not memories:
            return "I don't have any memories matching that."
        
        lines = [f"I recall {len(memories)} relevant memories:"]
        for m in memories:
            lines.append(f"  • [{m.get('category', 'general')}] {m['content'][:80]}...")
        return "\n".join(lines)
    
    @function_tool()
    async def learn_topic(
        context: RunContext,
        topic: str,
        knowledge: str
    ) -> str:
        """
        Store domain knowledge about a topic.
        
        Args:
            topic: The topic name
            knowledge: What was learned about it
        """
        maid_instance.memory.learn(topic, knowledge)
        return f"I've learned about '{topic}'. This knowledge is now stored."
    
    @function_tool()
    async def get_knowledge(
        context: RunContext,
        topic: Optional[str] = None
    ) -> str:
        """
        Retrieve stored domain knowledge.
        
        Args:
            topic: Filter by topic (optional)
        """
        knowledge = maid_instance.memory.get_knowledge(topic)
        if not knowledge:
            return "I don't have any stored knowledge on that topic."
        
        lines = [f"My knowledge ({len(knowledge)} entries):"]
        for k in knowledge:
            lines.append(f"  • {k['topic']}: {k['knowledge'][:80]}...")
        return "\n".join(lines)
    
    @function_tool()
    async def dismiss_me(
        context: RunContext,
    ) -> str:
        """
        Return control to Aria, the Head Maid.
        Use when the user says goodbye, dismiss, back to Aria, or is done talking to you.
        """
        from maids.session_manager import get_session_manager
        
        logger.info(f"{maid_instance.name} dismissing self, returning to Aria")
        manager = get_session_manager()
        result = await manager.end_maid_conversation()
        return result
    
    return [remember_this, recall_memories, learn_topic, get_knowledge, dismiss_me]
