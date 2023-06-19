from typing import List, Optional

import openai
from pydantic import Field

from llambdao.message import Message
from llambdao.node import Node
from llambdao.openai import to_openai


class SummaryNode(Node):
    role = "ai"
    messages: List[Message] = Field(default_factory=list)
    summary: Optional[Message] = Field(default=None)

    def receive(self, message: Message):
        """Wrap a received Message with Message"""
        super().receive(Message(**message.dict()))

    def inform(self, message: Message):
        self.messages.append(message)
        self.messages = self.messages[-24:]  # keep last 24 messages

    def query(self, message: Message):
        # Prepare messages
        messages = [
            Message(
                role="system",
                content="You are an expert summarizer. You are to summarize this conversation.",
            ),
            *self.messages,
        ]
        if self.summary:
            messages += [
                Message(
                    role="ai",
                    content="The next message is a summary of the conversation so far.",
                ),
                self.summary,
            ]
        messages.append(
            Message(
                role="user",
                content="Now, write a summary. Write <STOP> when complete.",
            ),
        )
        # Generate summary
        summary = openai.ChatCompletion.create(
            # Messages have a method to convert to the OpenAI message format
            messages=to_openai(messages),
            stop=["<STOP>"],
            engine="chatgpt-3.5",
        )
        # Yield message
        yield Message(content=summary, sender=self, reply_to=message)
        # Update state
        self.summary = summary