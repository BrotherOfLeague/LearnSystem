"""CLI 测试"""


def test_cli_module_importable():
    from learn_system.cli import main as cli_main

    assert hasattr(cli_main, "CLI")


def test_cli_initialize_requires_api_key(monkeypatch):
    from learn_system.cli import main as cli_main
    from learn_system.config import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "llm_api_key", None)
    cli = cli_main.CLI()
    assert cli.initialize() is False
