from app import ask


class FakeUsageMetadata:
    prompt_token_count = 123
    candidates_token_count = 45


class FakeResponse:
    text = "テスト応答"
    usage_metadata = FakeUsageMetadata()


class FakeModelClient:
    class models:
        @staticmethod
        def generate_content(model, contents):
            assert model == ask.MODEL
            assert contents == "テスト質問"
            return FakeResponse()


def test_ask_prints_input_and_output_tokens(monkeypatch, capsys):
    monkeypatch.setattr(ask.genai, "Client", lambda api_key: FakeModelClient())
    monkeypatch.setattr(ask, "get_api_key", lambda: "dummy-key")

    result = ask.ask("テスト質問")

    assert result == "テスト応答"
    output = capsys.readouterr().out
    assert "入力トークン数" in output
    assert "123" in output
    assert "出力トークン数" in output
    assert "45" in output
