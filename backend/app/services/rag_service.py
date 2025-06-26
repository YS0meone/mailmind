import os
import re
from typing import List, Dict, Any, Optional
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import DbEmail, DbThread, DbEmailAddress, address_has_threads
from app.core.config import settings
from app.logger_config import get_logger
import httpx
import json

logger = get_logger(__name__)


class RAGService:
    def __init__(self):
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.openai_model = getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo')

        # Simple in-memory storage for now (could be replaced with a proper vector DB)
        self.indexed_emails = {}  # user_email -> list of email documents

    async def index_user_emails(self, session: AsyncSession, user_email: str):
        """Index all emails for a user into memory storage"""
        try:
            # Get all emails accessible to the user
            query = (
                select(DbEmail, DbThread, DbEmailAddress)
                .join(DbThread, DbEmail.threadId == DbThread.id)
                .join(address_has_threads, DbThread.id == address_has_threads.c.thread_id)
                .join(DbEmailAddress, address_has_threads.c.address_id == DbEmailAddress.id)
                .where(DbEmailAddress.address == user_email)
            )

            results = await session.execute(query)
            email_data = results.all()

            documents = []

            for email, thread, _ in email_data:
                # Get from_address separately
                from_query = select(DbEmailAddress).where(
                    DbEmailAddress.id == email.fromId)
                from_result = await session.execute(from_query)
                from_address = from_result.scalar_one_or_none()

                # Create document text for searching
                email_doc = {
                    "email_id": str(email.id),
                    "thread_id": str(thread.id),
                    "subject": thread.subject,
                    "from_address": from_address.address if from_address else "Unknown",
                    "from_name": from_address.name if from_address and from_address.name else "",
                    "sent_at": email.sentAt.isoformat(),
                    "received_at": email.receivedAt.isoformat(),
                    "email_label": email.emailLabel,
                    "body": self._clean_html(email.body) if email.body else "",
                    "labels": email.labels or [],
                    "brief": thread.brief,
                    "searchable_text": self._create_searchable_text(email, thread, from_address)
                }

                documents.append(email_doc)

            # Store in memory
            self.indexed_emails[user_email] = documents
            logger.info(
                f"Indexed {len(documents)} emails for user {user_email}")

        except Exception as e:
            logger.error(f"Error indexing emails for user {user_email}: {e}")
            raise

    def _create_searchable_text(self, email: DbEmail, thread: DbThread, from_address: Optional[DbEmailAddress]) -> str:
        """Create a searchable document from email data"""
        body_text = self._clean_html(email.body) if email.body else ""

        searchable_parts = [
            f"Subject: {thread.subject}",
            f"From: {from_address.address if from_address else 'Unknown'}",
            f"From Name: {from_address.name if from_address and from_address.name else ''}",
            f"Date: {email.sentAt}",
            f"Labels: {', '.join(email.labels) if email.labels else ''}",
            f"Brief: {thread.brief}",
            f"Body: {body_text[:1000]}"  # Limit body length
        ]

        return " ".join(searchable_parts)

    def _clean_html(self, html_content: str) -> str:
        """Remove HTML tags and clean content"""
        if not html_content:
            return ""

        # Remove HTML tags
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', html_content)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

    def query_emails(self, user_email: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant emails based on query using simple text matching"""
        try:
            user_emails = self.indexed_emails.get(user_email, [])
            if not user_emails:
                return []

            query_lower = query.lower()
            scored_emails = []

            for email_doc in user_emails:
                score = 0
                searchable_text = email_doc["searchable_text"].lower()

                # Simple scoring based on keyword matches
                query_words = query_lower.split()
                for word in query_words:
                    if word in searchable_text:
                        score += searchable_text.count(word)

                # Boost score for matches in subject
                if query_lower in email_doc["subject"].lower():
                    score += 10

                # Boost score for matches in from address
                if query_lower in email_doc["from_address"].lower():
                    score += 5

                if score > 0:
                    scored_emails.append({
                        "email_doc": email_doc,
                        "score": score
                    })

            # Sort by score and return top results
            scored_emails.sort(key=lambda x: x["score"], reverse=True)
            return [item["email_doc"] for item in scored_emails[:limit]]

        except Exception as e:
            logger.error(f"Error querying emails: {e}")
            return []

    async def generate_response(self, user_query: str, relevant_emails: List[Dict[str, Any]]) -> str:
        """Generate response using OpenAI with retrieved context"""
        if not self.openai_api_key:
            return "I'm sorry, the AI service is not configured. Please contact your administrator."

        try:
            # Prepare context from relevant emails
            context = self._prepare_context(relevant_emails)

            # Create prompt
            prompt = self._create_prompt(user_query, context)

            # Call OpenAI API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.openai_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an AI assistant that helps users with their email management. Use the provided email context to answer questions accurately and helpfully. Be concise but informative."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 1000,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(
                    f"OpenAI API error: {response.status_code} - {response.text}")
                return "I'm sorry, I encountered an error while processing your request."

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm sorry, I encountered an error while processing your request."

    def _prepare_context(self, relevant_emails: List[Dict[str, Any]]) -> str:
        """Prepare context from relevant emails"""
        if not relevant_emails:
            return "No relevant emails found."

        context_parts = []
        # Limit to top 3 for context
        for i, email in enumerate(relevant_emails[:3]):
            context_parts.append(f"""
Email {i+1}:
- ID: {email['email_id']}
- Subject: {email['subject']}
- From: {email['from_name']} <{email['from_address']}>
- Date: {email['sent_at']}
- Labels: {', '.join(email['labels']) if email['labels'] else 'None'}
- Brief: {email['brief']}
- Content Preview: {email['body'][:300]}...
---""")

        return "\n".join(context_parts)

    def _create_prompt(self, user_query: str, context: str) -> str:
        """Create prompt for OpenAI"""
        return f"""Based on the following email context, please answer the user's question about their emails:

EMAIL CONTEXT:
{context}

USER QUESTION: {user_query}

Please provide a helpful and accurate response based on the email information provided. If the context doesn't contain enough information to answer the question completely, please say so and suggest what additional information might be helpful.

Focus on being practical and actionable in your response. If referring to specific emails, mention their subjects or senders for clarity.
"""


# Singleton instance
rag_service = RAGService()
