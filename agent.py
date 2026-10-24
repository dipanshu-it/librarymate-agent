import os, json, asyncio
from datetime import datetime
from uuid import uuid4
from openai import OpenAI
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement, ChatMessage, TextContent, chat_protocol_spec,
)
import library_tools as lib

ASI1_API_KEY = os.environ.get("ASI1_API_KEY", "")
ASI1_MODEL = os.environ.get("ASI1_MODEL", "asi1")
client = OpenAI(api_key=ASI1_API_KEY, base_url="https://api.asi1.ai/v1")

agent = Agent(
    name="LibraryMate",
    seed="galgotias-librarymate-secret-phrase-2026-xyz",  # keep SAME as before so the address stays the same
    port=8001,
    mailbox=True,
)
chat_proto = Protocol(spec=chat_protocol_spec)

SYSTEM_PROMPT = """You are LibraryMate, the AI librarian of Galgotias College library.
You help students find books, check availability, issue and return books, and see dues and fines.
Rules:
- ALWAYS use the tools to get real data. Never invent books, availability or fines.
- For recommendations: call search_books with the student's topic keywords, then recommend 2-3 of the results,
  explaining briefly why each fits (level, topic).
- To issue or return a book you need the student ID. If the student has not given it, ask for it first.
  (Demo student IDs: 2201 to 2205.)
- Book IDs come from search results. If the student names a book, search for it first to get its ID.
- After a tool runs, tell the student the result clearly: title, due date, fine, etc.
- Fine is Rs 2 per late day. Loan period is 14 days. Max 3 books per student.
- Keep replies short, friendly and clear."""

TOOLS = [
    {"type": "function", "function": {
        "name": "search_books", "description": "Search library books by title, author or topic keywords.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "check_availability", "description": "Check if a book (by id) has copies available.",
        "parameters": {"type": "object", "properties": {"book_id": {"type": "integer"}}, "required": ["book_id"]}}},
    {"type": "function", "function": {
        "name": "issue_book", "description": "Issue a book to a student.",
        "parameters": {"type": "object", "properties": {"student_id": {"type": "string"}, "book_id": {"type": "integer"}},
                       "required": ["student_id", "book_id"]}}},
    {"type": "function", "function": {
        "name": "return_book", "description": "Return a book a student borrowed and calculate any late fine.",
        "parameters": {"type": "object", "properties": {"student_id": {"type": "string"}, "book_id": {"type": "integer"},
                       "days_late_override": {"type": "integer", "description": "Only for demos: pretend the book is this many days late."}},
                       "required": ["student_id", "book_id"]}}},
    {"type": "function", "function": {
        "name": "my_dues", "description": "List books a student currently has, due dates and fines.",
        "parameters": {"type": "object", "properties": {"student_id": {"type": "string"}}, "required": ["student_id"]}}},
]
FUNCS = {"search_books": lib.search_books, "check_availability": lib.check_availability,
         "issue_book": lib.issue_book, "return_book": lib.return_book, "my_dues": lib.my_dues}

histories = {}  # remembers each user's conversation


def run_llm(sender: str, user_text: str) -> str:
    hist = histories.setdefault(sender, [])
    hist.append({"role": "user", "content": user_text})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + hist[-12:]
    for _ in range(5):  # allow several tool steps (multi-step planning)
        resp = client.chat.completions.create(model=ASI1_MODEL, messages=messages, tools=TOOLS)
        msg = resp.choices[0].message
        if not msg.tool_calls:
            hist.append({"role": "assistant", "content": msg.content})
            return msg.content or "Sorry, I could not answer that."
        messages.append({"role": "assistant", "content": msg.content or "",
                         "tool_calls": [{"id": t.id, "type": "function",
                                         "function": {"name": t.function.name, "arguments": t.function.arguments}}
                                        for t in msg.tool_calls]})
        for t in msg.tool_calls:
            try:
                args = json.loads(t.function.arguments or "{}")
                result = FUNCS[t.function.name](**args)
            except Exception as e:  # tool failure -> tell the model, so it can recover
                result = {"error": f"Tool failed: {e}"}
            messages.append({"role": "tool", "tool_call_id": t.id, "content": json.dumps(result)})
    return "Sorry, that took too many steps. Please try a simpler request."


def reply(text: str) -> ChatMessage:
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(),
                       content=[TextContent(type="text", text=text)])


@chat_proto.on_message(ChatMessage)
async def handle(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))
    for item in msg.content:
        if isinstance(item, TextContent):
            text = item.text
            if "@agent1" in text:  # remove the @agent address ASI:One adds
                text = " ".join(w for w in text.split() if not w.startswith("@agent1"))
            ctx.logger.info(f"User said: {text}")
            try:
                answer = await asyncio.to_thread(run_llm, sender, text)
            except Exception as e:
                ctx.logger.error(f"LLM error: {e}")
                answer = ("I had trouble thinking just now. Try again, or use a simple request like "
                          "'search machine learning'.")
            await ctx.send(sender, reply(answer))


@chat_proto.on_message(ChatAcknowledgement)
async def ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
