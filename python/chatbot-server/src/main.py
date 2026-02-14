from langchain_core.messages import AIMessage, HumanMessage

from src.chatbot.graph import get_agent
from src.utils.clients import create_clients


def run_chat() -> None:
    clients = create_clients()
    agent = get_agent(clients)
    messages: list = []

    print("Chatbot CLI — type 'quit' or 'exit' to end the conversation.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        messages.append(HumanMessage(content=user_input))
        result = agent.invoke({"messages": messages})
        messages = result["messages"]

        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                print(f"Assistant: {msg.content}\n")
                break


def main() -> None:
    run_chat()


if __name__ == "__main__":
    main()
