# LibraryMate – College Library AI Agent

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

LibraryMate is an AI librarian agent for Galgotias College students, built for Fetch-A-Thon 3.0.
It is registered on Agentverse, discoverable through ASI:One, and implements the Agent Chat Protocol.

**Agent name:** LibraryMate
**Agent address:** agent1qv0u4l8rh7pa4mcaltwvjqtrssh50qh9yk08thc0ucn5nfu4lzhjvd6lqkr

## Problem
Students waste time finding books, checking availability, and tracking due dates and fines.

## Target users
College students and library staff.

## What the agent does
The ASI1 LLM understands the student's intent, plans multiple steps and calls tools:
- search_books: search the catalog by topic, title or author
- check_availability: see if copies are free
- issue_book: issue a book (14-day loan, max 3 books per student)
- return_book: return a book and calculate the fine (Rs 2 per late day)
- my_dues: list borrowed books, due dates and fines

Example: "I am in 2nd year CSE, suggest ML books" -> the agent searches the catalog, checks availability,
recommends books, and then issues the chosen one and reports the due date.

## How to run
1. pip install -r requirements.txt
2. Get an ASI:One API key from https://asi1.ai
3. export ASI1_API_KEY="your-key"
4. python agent.py
5. Open the inspector link printed in the terminal, click Connect, then Mailbox.
6. In ASI:One, start a chat with the agent address above.

Demo student IDs: 2201 to 2205.

## Tech stack
uAgents, Agentverse mailbox, Agent Chat Protocol, ASI1 LLM (OpenAI-compatible tool calling), Python.

## Links
- ASI:One shared chat: https://asi1.ai/chat/09e35e40-eb64-41a5-b5cc-208ca3219e93?from=profile
- Agentverse profile: https://agentverse.ai/agents/details/agent1qv0u4l8rh7pa4mcaltwvjqtrssh50qh9yk08thc0ucn5nfu4lzhjvd6lqkr/profile
