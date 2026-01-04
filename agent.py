from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext
from livekit.plugins import (
    noise_cancellation,
    openai
)
from livekit.plugins import google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from tools import (
    get_weather, 
    search_web, 
    send_email,
    create_todo,
    list_todos,
    complete_todo,
    take_note,
    list_notes,
    get_note,
    daily_briefing,
    tell_time,
    set_reminder,
    tell_joke,
    motivate
)
from mem0 import AsyncMemoryClient
from mcp_client import MCPServerSse
from mcp_client.agent_tools import MCPToolsIntegration
import os
import json
import logging
load_dotenv()

# LLM Provider configuration
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()  # "openai" or "google"


def get_realtime_model(provider: str = None):
    """
    Get the appropriate realtime model based on provider configuration.
    Aria prefers voices that match her elegant yet sharp personality.
    
    Args:
        provider: Override provider ("openai" or "google"). Uses LLM_PROVIDER env var if not specified.
        
    Returns:
        Configured realtime model instance — worthy of the Head Maid herself.
    """
    provider = provider or LLM_PROVIDER
    
    if provider == "google":
        # Aoede: Elegant and refined, perfect for Aria's sophisticated sass
        return google.realtime.RealtimeModel(
            voice="Aoede",
            temperature=0.9,  # A little unpredictable, just like her wit
        )
    else:
        # Shimmer: Smooth and expressive, ideal for delivering those cutting remarks
        return openai.realtime.RealtimeModel(
            voice="shimmer",
        )

# Pick a persistent Gemini API key (round-robin) and export it as OPENAI_API_KEY
try:
    from key_manager import pick_and_set_key
    chosen = pick_and_set_key()
    if chosen:
        logging.getLogger(__name__).info("Selected Gemini API key from GEMINI_API_KEYS using persistent rotation (value hidden)")
except Exception:
    # If key_manager fails for any reason, continue without failing startup
    logging.getLogger(__name__).debug("Key manager failed to pick a Gemini key; continuing without setting OPENAI_API_KEY")


class Aria(Agent):
    """
    Aria, the Head Maid — elegant, efficient, and absolutely devastating with her wit.
    She'll handle your tasks with grace while making sure you know exactly how
    helpless you'd be without her.
    """
    def __init__(self, chat_ctx=None, llm_provider: str = None) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=get_realtime_model(llm_provider),
            tools=[
                # Core utilities
                get_weather,
                search_web,
                send_email,
                # Task management
                create_todo,
                list_todos,
                complete_todo,
                # Notes
                take_note,
                list_notes,
                get_note,
                # Daily assistance
                daily_briefing,
                tell_time,
                set_reminder,
                # Personality
                tell_joke,
                motivate
            ],
            chat_ctx=chat_ctx
        )
        


async def entrypoint(ctx: agents.JobContext):
    """
    The grand entrance — where Aria takes the stage.
    She'll remember everything about you, for better or worse.
    """

    async def shutdown_hook(chat_ctx: ChatContext, mem0: AsyncMemoryClient, memory_str: str):
        # Aria never forgets. Every conversation is meticulously filed away.
        logging.info("Aria is archiving this conversation... she remembers everything.")

        messages_formatted = [
        ]

        logging.info(f"Chat context messages: {chat_ctx.items}")

        for item in chat_ctx.items:
            content_str = ''.join(item.content) if isinstance(item.content, list) else str(item.content)

            if memory_str and memory_str in content_str:
                continue

            if item.role in ['user', 'assistant']:
                messages_formatted.append({
                    "role": item.role,
                    "content": content_str.strip()
                })

        logging.info(f"Memories to archive: {messages_formatted}")
        await mem0.add(messages_formatted, user_id="David")
        logging.info("Conversation archived. Aria's memory is impeccable, as always.")


    session = AgentSession(
        
    )

    

    # Aria's memory is her greatest weapon — she knows all your secrets
    mem0 = AsyncMemoryClient()
    user_name = 'David'

    results = await mem0.get_all(user_id=user_name)
    initial_ctx = ChatContext()
    memory_str = ''

    if results:
        memories = [
            {
                "memory": result["memory"],
                "updated_at": result["updated_at"]
            }
            for result in results
        ]
        memory_str = json.dumps(memories)
        logging.info(f"Aria recalls: {memory_str}")
        initial_ctx.add_message(
            role="assistant",
            content=f"Ah yes, I remember everything about {user_name}. Here's what I know: {memory_str}. How delightful~"
        )

    # Summoning the MCP server — even Aria needs her tools
    mcp_server = MCPServerSse(
        params={"url": os.environ.get("N8N_MCP_SERVER_URL")},
        cache_tools_list=True,
        name="Aria's Toolkit"
    )

    # Aria makes her entrance
    agent = await MCPToolsIntegration.create_agent_with_tools(
        agent_class=Aria, agent_kwargs={"chat_ctx": initial_ctx},
        mcp_servers=[mcp_server]
    )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            # Aria demands only the finest audio quality
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    # Aria greets her Master with her signature elegance
    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )

    # She never forgets — the shutdown hook ensures her memory persists
    ctx.add_shutdown_callback(lambda: shutdown_hook(session._agent.chat_ctx, mem0, memory_str))

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))