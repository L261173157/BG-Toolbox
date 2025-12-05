import os
import sys
import pytest

# ensure repo root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from material_classifier import MaterialClassifier
from config import Config


class DummyResp:
    def __init__(self, rid, text):
        self.id = rid
        # mimic structure: output -> [ { 'content': [ { 'text': '...' } ] } ]
        self.output = [type('O', (), {'content': [type('C', (), {'text': text})]})]
        # some client wrappers expose a convenience property
        self.output_text = text


def make_client_with_create(fn):
    class C:
        class responses:
            @staticmethod
            def create(**kwargs):
                return fn(**kwargs)

    return C()


def test_plain_json_parsing_and_conversation_chain(monkeypatch):
    mc = MaterialClassifier()

    def fake_create(**kwargs):
        inp = kwargs.get('input') or kwargs.get('input_text') or ''
        # first call is initialization with PROMPT_TEMPLATE
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # subsequent call returns plain JSON
        return DummyResp('r1', '{"main_category":"化学品","sub_category":"溶剂"}')

    mc.client = make_client_with_create(fake_create)

    parsed = mc._call_deepseek_api('dummy prompt')
    assert isinstance(parsed, dict)
    assert parsed.get('main_category') == '化学品'
    assert parsed.get('sub_category') == '溶剂'
    # conversation_context_id must be updated to latest response id
    assert mc.conversation_context_id == 'r1'


def test_json_in_codeblock_parsing(monkeypatch):
    mc = MaterialClassifier()

    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init2', 'OK')
        text = 'Here is the result:\n```json\n{"main_category":"材料","sub_category":"金属"}\n```'
        return DummyResp('r2', text)

    mc.client = make_client_with_create(fake_create)
    parsed = mc._call_deepseek_api('p2')
    assert parsed.get('main_category') == '材料'
    assert parsed.get('sub_category') == '金属'
    assert mc.conversation_context_id == 'r2'


def test_embedded_json_parsing(monkeypatch):
    mc = MaterialClassifier()

    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init3', 'OK')
        text = 'Result is: {"main_category":"其它","sub_category":"包装"} Some trailing text.'
        return DummyResp('r3', text)

    mc.client = make_client_with_create(fake_create)
    parsed = mc._call_deepseek_api('p3')
    assert parsed.get('main_category') == '其它'
    assert parsed.get('sub_category') == '包装'
    assert mc.conversation_context_id == 'r3'


def test_no_json_raises(monkeypatch):
    mc = MaterialClassifier()

    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init4', 'OK')
        return DummyResp('r4', 'I cannot produce json here')

    mc.client = make_client_with_create(fake_create)
    with pytest.raises(ValueError):
        mc._call_deepseek_api('p4')
