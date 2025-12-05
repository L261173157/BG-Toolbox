import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from material_classifier import MaterialClassifier
from config import Config


class DummyResp:
    def __init__(self, rid, text):
        self.id = rid
        self.output = [type('O', (), {'content': [type('C', (), {'text': text})]})]
        self.output_text = text


def make_client_with_create(fn):
    class C:
        class responses:
            @staticmethod
            def create(**kwargs):
                return fn(**kwargs)
    return C()


def test_json_found_via_regex_extraction():
    """Test that JSON is extracted via regex when not in clear blocks."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # JSON embedded in middle of text without clear markers
        text = 'The classification is: {"main_category":"输送类","sub_category":"倍速链线"} according to our standards.'
        return DummyResp('r1', text)
    
    mc.client = make_client_with_create(fake_create)
    
    parsed = mc._call_deepseek_api('test prompt')
    assert parsed['main_category'] == '输送类'
    assert parsed['sub_category'] == '倍速链线'


def test_multiple_json_objects_extracts_last_one():
    """Test that when multiple JSON objects exist, the last one is extracted."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Multiple JSON objects - last one should be used
        text = '{"main_category":"错误大类","sub_category":"错误二级类"} The correct one is: {"main_category":"机器人","sub_category":"六轴机器人"}'
        return DummyResp('r1', text)
    
    mc.client = make_client_with_create(fake_create)
    
    parsed = mc._call_deepseek_api('test prompt')
    # Should extract the last JSON object
    assert parsed['main_category'] == '机器人'
    assert parsed['sub_category'] == '六轴机器人'


def test_json_array_extraction_uses_last():
    """Test that when JSON is an array (not an object), it properly fails validation."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Array with objects inside - will fail validation since result is array not object
        text = '[{"main_category":"打标/激光类","sub_category":"激光打标"}]'
        return DummyResp('r1', text)
    
    mc.client = make_client_with_create(fake_create)
    
    # Array will be parsed as JSON but fails validation check (must be dict)
    with pytest.raises(ValueError) as exc_info:
        mc._call_deepseek_api('test prompt')
    assert "预期的对象格式" in str(exc_info.value)


def test_cleanup_with_markdown_block_no_json_tag():
    """Test markdown code block cleanup when there's no 'json' language tag."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Markdown block without language identifier
        text = '```\n{"main_category":"拧紧类","sub_category":"气动拧紧工具"}\n```'
        return DummyResp('r1', text)
    
    mc.client = make_client_with_create(fake_create)
    
    parsed = mc._call_deepseek_api('test prompt')
    assert parsed['main_category'] == '拧紧类'
    assert parsed['sub_category'] == '气动拧紧工具'


def test_partial_response_missing_fields_after_validation():
    """Test that response with explicitly missing required fields fails validation."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # JSON without sub_category field (not null, but missing)
        return DummyResp('r1', '{"main_category":"上料/送钉类"}')
    
    mc.client = make_client_with_create(fake_create)
    
    with pytest.raises(ValueError) as exc_info:
        mc._call_deepseek_api('test prompt')
    assert "缺少必要字段" in str(exc_info.value)


def test_exception_in_load_classification_standards_propagates():
    """Test that exceptions during load_classification_standards propagate."""
    with pytest.raises(ValueError) as exc_info:
        # Temporarily modify Config to have a malformed PROMPT_TEMPLATE
        original_template = Config.PROMPT_TEMPLATE
        try:
            Config.PROMPT_TEMPLATE = "No classification rules here"
            MaterialClassifier()
        finally:
            Config.PROMPT_TEMPLATE = original_template
    assert "无法找到分类规则" in str(exc_info.value)


def test_material_with_all_available_fields():
    """Test classify_material with all possible fields populated."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        return DummyResp('r1', '{"main_category":"其他FA/连接/定位零件","sub_category":"弹簧、氮气弹簧"}')
    
    mc.client = make_client_with_create(fake_create)
    
    result = mc.classify_material({
        '物料名称': '弹簧',
        '图号/型号': 'SPRING-001',
        '材料': '不锈钢',
        '分类/品牌': 'UNKNOWN',
        '供应商': 'Supplier1',
    })
    
    assert result['main_category'] == '其他FA/连接/定位零件'
    assert result['sub_category'] == '弹簧、氮气弹簧'


def test_conversation_context_none_at_start():
    """Test that conversation_context_id is None before first call."""
    mc = MaterialClassifier()
    assert mc.conversation_context_id is None


def test_response_text_none_or_falsy():
    """Test handling of None or falsy response text."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Return response with None or empty string
        return DummyResp('r1', None)
    
    mc.client = make_client_with_create(fake_create)
    
    with pytest.raises(ValueError) as exc_info:
        mc._call_deepseek_api('test prompt')
    assert "内容为空" in str(exc_info.value)
