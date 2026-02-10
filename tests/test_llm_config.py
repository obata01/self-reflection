"""YAML LLMクライアント設定のテスト."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from src.common.config.app_config_loader import (
    AppConfigLoader,
    resolve_env_vars,
)
from src.common.schema.llm_config import (
    AppYamlConfig,
    ChatClientEntry,
    ChatClientsConfig,
    LLMsConfig,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

_safe_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S", "Z")),
    min_size=1,
    max_size=50,
)

_safe_values = st.one_of(
    _safe_text,
    st.integers(min_value=-1000, max_value=1000),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    st.booleans(),
)

_config_dict = st.dictionaries(keys=_safe_text, values=_safe_values, min_size=1, max_size=5)

_chat_client_entry_st = st.builds(
    ChatClientEntry,
    name=_safe_text,
    config=_config_dict,
    default_params=_config_dict,
)


# ---------------------------------------------------------------------------
# Feature: yaml-llm-config, Property 2: 有効な設定のバリデーション通過
# ---------------------------------------------------------------------------


@given(
    name=_safe_text,
    config=_config_dict,
    default_params=_config_dict,
)
@settings(max_examples=100)
def test_valid_chat_client_entry_passes_validation(name, config, default_params):
    """有効なChat_Client_Entryはバリデーションが成功し、全フィールドが保持される."""
    entry = ChatClientEntry(name=name, config=config, default_params=default_params)
    assert entry.name == name
    assert entry.config == config
    assert entry.default_params == default_params


# ---------------------------------------------------------------------------
# Feature: yaml-llm-config, Property 3: 不正な設定のバリデーション拒否
# ---------------------------------------------------------------------------


def test_missing_name_raises_validation_error():
    """nameフィールドが欠落した場合、ValidationErrorが発生する."""
    with pytest.raises(ValidationError):
        ChatClientEntry(config={"model": "test"})


def test_missing_config_raises_validation_error():
    """configフィールドが欠落した場合、ValidationErrorが発生する."""
    with pytest.raises(ValidationError):
        ChatClientEntry(name="test")


# ---------------------------------------------------------------------------
# Feature: yaml-llm-config, Property 4: 環境変数解決とキー名変換
# ---------------------------------------------------------------------------


@given(
    config=st.dictionaries(
        keys=_safe_text,
        values=_safe_text,
        min_size=0,
        max_size=5,
    ),
)
@settings(max_examples=100)
def test_resolve_env_vars_key_transformation(config):
    """_envサフィックスを持つキーは解決後にサフィックスが除去される.
    _envサフィックスを持たないキーは変更されない."""
    resolved = resolve_env_vars(config)
    for key in config:
        if key.endswith("_env"):
            resolved_key = key[:-4]
            assert resolved_key in resolved
            assert key not in resolved
        else:
            assert key in resolved
            assert resolved[key] == config[key]


def test_resolve_env_vars_reads_environment():
    """_envフィールドの値を環境変数名として解決する."""
    config = {"api_key_env": "MY_TEST_KEY", "model": "gpt-4"}
    with patch.dict(os.environ, {"MY_TEST_KEY": "secret123"}):
        resolved = resolve_env_vars(config)
    assert resolved["api_key"] == "secret123"
    assert resolved["model"] == "gpt-4"
    assert "api_key_env" not in resolved


def test_resolve_env_vars_missing_env_returns_none():
    """未設定の環境変数はNoneを返し、エラーは発生しない."""
    config = {"api_key_env": "NONEXISTENT_VAR_12345"}
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("NONEXISTENT_VAR_12345", None)
        resolved = resolve_env_vars(config)
    assert resolved["api_key"] is None


# ---------------------------------------------------------------------------
# Feature: yaml-llm-config, Property 1: YAML設定のラウンドトリップ
# ---------------------------------------------------------------------------


@given(
    entries=st.lists(_chat_client_entry_st, min_size=0, max_size=3),
)
@settings(max_examples=100)
def test_yaml_round_trip(entries):
    """有効なAppYamlConfigはYAMLに書き出してから読み込むと同等のインスタンスが得られる."""
    original = AppYamlConfig(
        llms=LLMsConfig(
            chat_clients=ChatClientsConfig(
                bedrock=entries,
            ),
        ),
    )
    yaml_str = yaml.dump(original.model_dump())
    data = yaml.safe_load(yaml_str)
    restored = AppYamlConfig(**data)
    assert original == restored


# ---------------------------------------------------------------------------
# Feature: yaml-llm-config, Property 7: Noneパラメータのフィルタリング
# ---------------------------------------------------------------------------


@given(
    params=st.dictionaries(
        keys=_safe_text,
        values=st.one_of(st.none(), _safe_values),
        min_size=0,
        max_size=5,
    ),
)
@settings(max_examples=100)
def test_none_params_filtered(params):
    """None値を持つキーはフィルタリング後の結果に含まれない."""
    filtered = {k: v for k, v in params.items() if v is not None}
    for k, v in params.items():
        if v is None:
            assert k not in filtered
        else:
            assert filtered[k] == v


# ---------------------------------------------------------------------------
# ユニットテスト: AppConfigLoader
# ---------------------------------------------------------------------------


def test_loader_file_not_found():
    """存在しないファイルパスでFileNotFoundErrorが発生する."""
    loader = AppConfigLoader(config_path="nonexistent/path.yaml")
    with pytest.raises(FileNotFoundError, match="nonexistent/path.yaml"):
        loader.load()


def test_loader_loads_valid_yaml(tmp_path):
    """有効なYAMLファイルを正しく読み込む."""
    yaml_content = {
        "llms": {
            "chat_clients": {
                "bedrock": [
                    {
                        "name": "test-model",
                        "config": {"model_id": "test", "region_name": "us-east-1"},
                        "default_params": {"max_tokens": 1024},
                    },
                ],
            },
        },
    }
    yaml_path = tmp_path / "app.yaml"
    yaml_path.write_text(yaml.dump(yaml_content))

    loader = AppConfigLoader(config_path=str(yaml_path))
    result = loader.load()

    assert len(result.llms.chat_clients.bedrock) == 1
    assert result.llms.chat_clients.bedrock[0].name == "test-model"
    assert result.llms.chat_clients.bedrock[0].config["model_id"] == "test"
    assert result.llms.chat_clients.bedrock[0].default_params["max_tokens"] == 1024


def test_loader_invalid_yaml_syntax(tmp_path):
    """不正なYAML構文でyaml.YAMLErrorが発生する."""
    yaml_path = tmp_path / "bad.yaml"
    yaml_path.write_text("{{invalid: yaml: content")

    loader = AppConfigLoader(config_path=str(yaml_path))
    with pytest.raises(yaml.YAMLError):
        loader.load()


# ---------------------------------------------------------------------------
# ユニットテスト: default_params省略時のデフォルト値
# ---------------------------------------------------------------------------


def test_default_params_defaults_to_empty_dict():
    """default_paramsが省略された場合、空の辞書がデフォルトとなる."""
    entry = ChatClientEntry(name="test", config={"model": "x"})
    assert entry.default_params == {}


# ---------------------------------------------------------------------------
# ユニットテスト: プロバイダ別の設定例
# ---------------------------------------------------------------------------


def test_bedrock_config_structure():
    """bedrockプロバイダの設定構造."""
    entry = ChatClientEntry(
        name="sonnet",
        config={"model_id": "anthropic.claude-v2", "region_name": "us-east-1"},
        default_params={"max_tokens": 1024},
    )
    assert "model_id" in entry.config
    assert "region_name" in entry.config


def test_azure_config_structure():
    """azureプロバイダの設定構造."""
    entry = ChatClientEntry(
        name="gpt-4o",
        config={
            "model": "gpt-4o",
            "azure_deployment": "gpt-4o",
            "azure_endpoint_env": "AZURE_OPENAI_ENDPOINT",
            "api_key_env": "AZURE_OPENAI_API_KEY",
            "openai_api_version": "2024-12-01-preview",
        },
    )
    assert "azure_deployment" in entry.config
    assert "azure_endpoint_env" in entry.config
    assert "api_key_env" in entry.config
    assert "openai_api_version" in entry.config


def test_openai_config_structure():
    """openaiプロバイダの設定構造."""
    entry = ChatClientEntry(
        name="gpt-4",
        config={"model": "gpt-4", "api_key_env": "OPENAI_API_KEY"},
    )
    assert "model" in entry.config
    assert "api_key_env" in entry.config


# ---------------------------------------------------------------------------
# ユニットテスト: KeyError（存在しないname指定）
# ---------------------------------------------------------------------------


def test_get_chat_model_unknown_name_raises_key_error():
    """存在しないnameでKeyErrorが発生し、利用可能name一覧が含まれる."""
    from dependency_injector import providers as di_providers

    from src.common.di.container import Container, get_chat_model

    container = Container()

    # モック用の小さなレジストリを注入
    registry = {"sonnet": "mock_model", "haiku": "mock_model2"}
    container.chat_model_registry.override(di_providers.Object(registry))

    with pytest.raises(KeyError, match="nonexistent"):
        get_chat_model(container, "nonexistent")


# ---------------------------------------------------------------------------
# ユニットテスト: レジストリのSingleton性 (Property 6)
# ---------------------------------------------------------------------------


def test_registry_returns_same_instance():
    """レジストリから2回取得したインスタンスは同一オブジェクトである."""
    from dependency_injector import providers as di_providers

    from src.common.di.container import Container, get_chat_model

    container = Container()

    mock_model = object()
    registry = {"test": mock_model}
    container.chat_model_registry.override(di_providers.Object(registry))

    model1 = get_chat_model(container, "test")
    model2 = get_chat_model(container, "test")
    assert model1 is model2
