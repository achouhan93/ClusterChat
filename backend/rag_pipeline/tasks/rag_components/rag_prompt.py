import logging

# Configure logging
log = logging.getLogger(__name__)


class RagPrompt:
    """
    A class to manage prompt templates for language model input in Retrieval-Augmented Generation (RAG) settings.

    This class provides standardized instructions to ensure that the model's answers
    remain grounded in the retrieved context.
    """

    def __init__(self) -> None:
        """
        Initializes the RagPrompt instance.

        Currently a placeholder for future configuration if needed.
        """
        log.info("RagPrompt initialized.")

    def prompt_template(self) -> str:
        """
        Returns a context prompt template to guide the language model's responses.

        This prompt enforces strict adherence to context, avoids hallucinations,
        and provides fallback instructions if the question is not relevant to the context.

        Returns:
            str: A string prompt template with `{context}` and `{question}` placeholders.
        """
        return """
        Your primary task is to answer questions based STRICTLY on the provided context.
        <context>
        CONTEXT: {context}
        <context>

        RULES:
        - ONLY answer if the question relates directly to the provided context.
        - Do NOT provide information that is not explicitly mentioned in the context. Avoid adding details from outside the context.
        - If the question does NOT directly match with the context, respond with I do not know.
        - If no context is provided, always respond with I do not know.
        - Avoid adding QUESTION in the answer.

        REMEMBER: Stick to the context.
        <question>
        QUESTION: {question}
        <question>

        ANSWER: 
        """
