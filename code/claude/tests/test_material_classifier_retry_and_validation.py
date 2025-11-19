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


def test_retry_on_first_failure_then_success(monkeypatch):
    """Test that classifier retries on failure and eventually succeeds."""
    mc = MaterialClassifier()
    
    attempt_count = [0]
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        
        attempt_count[0] += 1
        if attempt_count[0] == 1:
            # First attempt fails
            raise Exception("Temporary API failure")
        # Second attempt succeeds
        return DummyResp('r1', '{"main_category":"电机/控制器及配套","sub_category":"普通/减速电机"}')
    
    mc.client = make_client_with_create(fake_create)
    
    # Should succeed on retry despite first failure
    parsed = mc._call_deepseek_api('test prompt')
    assert parsed['main_category'] == '电机/控制器及配套'
    assert parsed['sub_category'] == '普通/减速电机'


def test_max_retries_exceeded_raises(monkeypatch):
    """Test that classifier raises after max retries exceeded."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Always fails
        raise Exception("Persistent API failure")
    
    mc.client = make_client_with_create(fake_create)
    
    with pytest.raises(Exception) as exc_info:
        mc._call_deepseek_api('test prompt')
    assert "Persistent API failure" in str(exc_info.value)


def test_empty_response_raises(monkeypatch):
    """Test that empty API response raises ValueError."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Return empty response
        return DummyResp('r1', '')
    
    mc.client = make_client_with_create(fake_create)
    
    with pytest.raises(ValueError) as exc_info:
        mc._call_deepseek_api('test prompt')
    assert "内容为空" in str(exc_info.value)


def test_invalid_json_in_response_raises(monkeypatch):
    """Test that invalid JSON in response raises appropriate error."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Return invalid JSON
        return DummyResp('r1', 'This is not JSON at all')
    
    mc.client = make_client_with_create(fake_create)
    
    with pytest.raises(ValueError):
        mc._call_deepseek_api('test prompt')


def test_missing_required_field_raises(monkeypatch):
    """Test that JSON missing required field raises ValueError."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Missing sub_category
        return DummyResp('r1', '{"main_category":"电机/控制器及配套"}')
    
    mc.client = make_client_with_create(fake_create)
    
    with pytest.raises(ValueError) as exc_info:
        mc._call_deepseek_api('test prompt')
    assert "缺少必要字段" in str(exc_info.value)


def test_json_array_response_raises(monkeypatch):
    """Test that JSON array (not object) raises error."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Return JSON array instead of object
        return DummyResp('r1', '[{"main_category":"电机/控制器及配套","sub_category":"普通/减速电机"}]')
    
    mc.client = make_client_with_create(fake_create)
    
    with pytest.raises(ValueError) as exc_info:
        mc._call_deepseek_api('test prompt')
    assert "预期的对象格式" in str(exc_info.value)


def test_validate_invalid_category_raises(monkeypatch):
    """Test that invalid category combination raises during validation."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Return a category that doesn't exist in classification_mapping
        return DummyResp('r1', '{"main_category":"不存在的大类","sub_category":"不存在的二级类"}')
    
    mc.client = make_client_with_create(fake_create)
    
    with pytest.raises(ValueError) as exc_info:
        mc.classify_material({
            '物料名称': '测试物料',
            '图号/型号': 'TEST-001'
        })
    assert "不符合标准" in str(exc_info.value)


def test_classify_material_with_empty_data(monkeypatch):
    """Test classify_material with empty material data."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        return DummyResp('r1', '{"main_category":"气动类","sub_category":"气源系统、气源处理"}')
    
    mc.client = make_client_with_create(fake_create)
    
    # Call with minimal data
    result = mc.classify_material({
        '物料名称': '',
        '图号/型号': '',
    })
    
    assert result['main_category'] == '气动类'
    assert result['sub_category'] == '气源系统、气源处理'


def test_classify_material_with_unicode_characters(monkeypatch):
    """Test classify_material handles unicode properly."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        return DummyResp('r1', '{"main_category":"液压类","sub_category":"液压站、系统"}')
    
    mc.client = make_client_with_create(fake_create)
    
    # Call with unicode-heavy data
    result = mc.classify_material({
        '物料名称': '液压泵 - 中文测试 - 日本語',
        '图号/型号': 'HPP-001-日本',
        '材料': '钢铁、合金',
    })
    
    assert result['main_category'] == '液压类'
    assert result['sub_category'] == '液压站、系统'


def test_response_with_bytes_content(monkeypatch):
    """Test that response with bytes content is properly decoded."""
    mc = MaterialClassifier()
    
    # Create a JSON string first, then encode to bytes
    json_str = '{"main_category":"传感器类","sub_category":"温度传感器"}'
    json_bytes = json_str.encode('utf-8')
    
    class BytesResp:
        def __init__(self, rid, json_data):
            self.id = rid
            self.output = [type('O', (), {'content': [type('C', (), {'text': json_data})]})]
            # output_text is bytes
            self.output_text = json_data
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        return BytesResp('r1', json_bytes)
    
    mc.client = make_client_with_create(fake_create)
    
    parsed = mc._call_deepseek_api('test prompt')
    assert parsed['main_category'] == '传感器类'
    assert parsed['sub_category'] == '温度传感器'


def test_json_with_extra_fields(monkeypatch):
    """Test that JSON with extra fields (beyond main_category and sub_category) still parses."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Extra fields in response
        return DummyResp('r1', '{"main_category":"指示/灯/操控类","sub_category":"按钮、指示灯","confidence":0.95,"reason":"matched"}')
    
    mc.client = make_client_with_create(fake_create)
    
    parsed = mc._call_deepseek_api('test prompt')
    assert parsed['main_category'] == '指示/灯/操控类'
    assert parsed['sub_category'] == '按钮、指示灯'
    # Extra fields are preserved
    assert parsed.get('confidence') == 0.95


def test_consecutive_api_calls_update_context_id(monkeypatch):
    """Test that consecutive calls update conversation_context_id."""
    mc = MaterialClassifier()
    
    call_count = [0]
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        
        call_count[0] += 1
        resp_id = f'resp_{call_count[0]}'
        return DummyResp(resp_id, '{"main_category":"读码/视觉识别/追溯类","sub_category":"读码器"}')
    
    mc.client = make_client_with_create(fake_create)
    
    # First call
    mc._call_deepseek_api('prompt 1')
    first_context_id = mc.conversation_context_id
    
    # Second call
    mc._call_deepseek_api('prompt 2')
    second_context_id = mc.conversation_context_id
    
    # Context ID should have updated
    assert first_context_id == 'resp_1'
    assert second_context_id == 'resp_2'
    assert first_context_id != second_context_id
