class ragPrompt:
    """
    A class to manage prompt templates for language model input.

    This class provides different templates for generating prompts which are used to instruct
    a language model on how to process and respond to user queries.
    """

    def __init__(self) -> None:
        """
        Initializes the ragPrompt instance.

        The constructor currently does not carry out any operations.
        """
        pass

    def prompt_template(self) -> str:
        """
        Provides a prompt template for scenarios where contextual information is available.

        This template is used when there is additional context (e.g., related texts or documents)
        that can help the model in generating a more informed answer.

        Returns:
            A string containing the template with placeholders for context and the user's question.
        """
        prompt = """
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

        REMEMBER: Stick to the context. If uncertain, respond with I do not know.
        <question>
        QUESTION: {question}
        <question>

        ANSWER: 
        """
        return prompt