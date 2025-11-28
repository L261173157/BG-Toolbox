import os
import sys
import json
from types import SimpleNamespace
import pytest

# make project modules importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from material_classifier import MaterialClassifier
from config import Config


@pytest.fixture(autouse=True)
def set_config(monkeypatch):
    monkeypatch.setattr(Config, "DEEPSEEK_API_KEY", "testkey")
    monkeypatch.setattr(Config, "DEEPSEEK_API_URL", "https://example.com/api")
    monkeypatch.setattr(Config, "DEEPSEEK_MODEL", "dummy-model")
    # speed up retry behavior in tests when needed
    monkeypatch.setattr(Config, "MAX_RETRIES", 2)
    yield


def make_response(id, text):
    return SimpleNamespace(id=id, output_text=text)


def test_call_deepseek_api_simple_json(monkeypatch):
    clf = MaterialClassifier()

    calls = []

    def fake_create(**kwargs):
        # first call: initialization, return an id
        if not calls:
            calls.append(1)
            return make_response("init-id", "initialized")
        # second call: return clean JSON
        calls.append(2)
        return make_response("resp-1", json.dumps({"main_category": "PLC/IO模块/柜体", "sub_category": "PLC"}))

    monkeypatch.setattr(clf.client, "responses", SimpleNamespace(create=lambda **k: fake_create(**k)))

    result = clf._call_deepseek_api("测试提示")
    assert isinstance(result, dict)
    assert result["main_category"] == "PLC/IO模块/柜体"
    assert clf.conversation_context_id == "resp-1"


def test_call_deepseek_api_codeblock_json(monkeypatch):
    clf = MaterialClassifier()

    seq = [0]

    def fake_create(**kwargs):
        # init
        if seq[0] == 0:
            seq[0] += 1
            return make_response("init-2", "ok")
        # return json inside markdown code block
        return make_response("resp-2", "```json\n{\"main_category\": \"HMI/工控机/UPS\", \"sub_category\": \"UPS电源\"}\n```")

    monkeypatch.setattr(clf.client, "responses", SimpleNamespace(create=lambda **k: fake_create(**k)))

    result = clf._call_deepseek_api("prompt")
    assert result["main_category"] == "HMI/工控机/UPS"


def test_call_deepseek_api_embedded_json(monkeypatch):
    clf = MaterialClassifier()

    seq = [0]

    def fake_create(**kwargs):
        if seq[0] == 0:
            seq[0] += 1
            return make_response("init-3", "ok")
        # response contains extra commentary and an embedded JSON object
        text = "分析: ... \n最终结果: {\"main_category\": \"传感器类\", \"sub_category\": \"接近传感器\"} \n结束"
        return make_response("resp-3", text)

    monkeypatch.setattr(clf.client, "responses", SimpleNamespace(create=lambda **k: fake_create(**k)))

    result = clf._call_deepseek_api("prompt")
    assert result["sub_category"] == "接近传感器"


def test_call_deepseek_api_no_json_raises(monkeypatch):
    clf = MaterialClassifier()

    # set retries to 1 for faster failure
    monkeypatch.setattr(Config, "MAX_RETRIES", 1)

    seq = [0]

    def fake_create(**kwargs):
        if seq[0] == 0:
            seq[0] += 1
            return make_response("init-4", "ok")
        return make_response("resp-4", "这里没有JSON")

    monkeypatch.setattr(clf.client, "responses", SimpleNamespace(create=lambda **k: fake_create(**k)))

    with pytest.raises(Exception):
        clf._call_deepseek_api("prompt")
