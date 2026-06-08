from unittest.mock import MagicMock, patch


def _mock_response(text: str):
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


@patch("agents.chatbot_agent.Anthropic")
def test_chat_appends_history(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = _mock_response("Hola!")

    from agents.chatbot_agent import ChatbotAgent
    bot = ChatbotAgent()
    reply = bot.chat("Hola")

    assert reply == "Hola!"
    assert len(bot.history) == 2
    assert bot.history[0] == {"role": "user", "content": "Hola"}
    assert bot.history[1] == {"role": "assistant", "content": "Hola!"}


@patch("agents.chatbot_agent.Anthropic")
def test_reset_clears_history(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = _mock_response("Hola!")

    from agents.chatbot_agent import ChatbotAgent
    bot = ChatbotAgent()
    bot.chat("Hola")
    bot.reset()

    assert bot.history == []
