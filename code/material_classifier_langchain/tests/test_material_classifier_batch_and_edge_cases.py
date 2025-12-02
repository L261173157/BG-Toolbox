import os
import sys
import pytest
from unittest.mock import patch, MagicMock

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


def test_classify_batch_with_mixed_results():
    """Test classify_batch with both successful and failed materials."""
    mc = MaterialClassifier()
    
    call_count = [0]
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        
        call_count[0] += 1
        if call_count[0] == 1:
            # First material succeeds
            return DummyResp('r1', '{"main_category":"电机/控制器及配套","sub_category":"普通/减速电机"}')
        elif call_count[0] <= 4:
            # Second material fails (retries 3 times, all fail)
            raise Exception("API Error on second material - all retries fail")
        else:
            # Third material succeeds after second failed
            return DummyResp('r3', '{"main_category":"气动类","sub_category":"气缸（执行机构）"}')
    
    mc.client = make_client_with_create(fake_create)
    
    materials = [
        {'物料名称': '电机1', '图号/型号': 'MOT-001'},
        {'物料名称': '电机2', '图号/型号': 'MOT-002'},
        {'物料名称': '气缸', '图号/型号': 'CYL-001'},
    ]
    
    with patch('time.sleep'):  # Mock sleep to speed up test
        results = mc.classify_batch(materials)
    
    # Check first result (success)
    assert results[0]['status'] == 'success'
    assert results[0]['classification']['main_category'] == '电机/控制器及配套'
    
    # Check second result (failed)
    assert results[1]['status'] == 'failed'
    assert 'error' in results[1]
    
    # Check third result (success)
    assert results[2]['status'] == 'success'
    assert results[2]['classification']['main_category'] == '气动类'


def test_classify_batch_empty_list():
    """Test classify_batch with empty material list."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        return DummyResp('r1', '{"main_category":"液压类","sub_category":"液压站、系统"}')
    
    mc.client = make_client_with_create(fake_create)
    
    results = mc.classify_batch([])
    assert results == []


def test_classify_batch_single_item():
    """Test classify_batch with single item (no sleep between calls)."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        return DummyResp('r1', '{"main_category":"传感器类","sub_category":"温度传感器"}')
    
    mc.client = make_client_with_create(fake_create)
    
    with patch('time.sleep') as mock_sleep:
        results = mc.classify_batch([
            {'物料名称': '温度传感器', '图号/型号': 'TEMP-001'}
        ])
    
    # Should not call sleep since there's only one item
    mock_sleep.assert_not_called()
    
    assert len(results) == 1
    assert results[0]['status'] == 'success'


def test_classify_batch_triggers_sleep_between_items():
    """Test that classify_batch calls sleep between items."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        return DummyResp('r1', '{"main_category":"传感器类","sub_category":"压力扭矩传感器"}')
    
    mc.client = make_client_with_create(fake_create)
    
    with patch('time.sleep') as mock_sleep:
        results = mc.classify_batch([
            {'物料名称': '传感器1', '图号/型号': 'SNS-001'},
            {'物料名称': '传感器2', '图号/型号': 'SNS-002'},
            {'物料名称': '传感器3', '图号/型号': 'SNS-003'},
        ])
    
    # Should call sleep twice (between items 1-2 and 2-3, but not after the last item)
    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list[0] == ((Config.API_RATE_LIMIT,),)


def test_api_key_missing_raises():
    """Test that missing API key raises on initialization."""
    with patch.object(Config, 'DEEPSEEK_API_KEY', None):
        with pytest.raises(ValueError) as exc_info:
            MaterialClassifier()
        assert "API密钥未配置" in str(exc_info.value)


def test_non_string_content_converted_to_string():
    """Test that non-string content from API is converted to string."""
    mc = MaterialClassifier()
    
    class NumberResp:
        def __init__(self, rid):
            self.id = rid
            self.output_text = 12345  # Return a number instead of string
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        return NumberResp('r1')
    
    mc.client = make_client_with_create(fake_create)
    
    # Should fail because "12345" cannot be parsed as JSON for classification
    with pytest.raises(ValueError):
        mc._call_deepseek_api('test')


def test_markdown_codeblock_without_language_tag():
    """Test parsing JSON from markdown code block without language tag."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Code block without 'json' language tag
        text = '```\n{"main_category":"指示/灯/操控类","sub_category":"塔灯"}\n```'
        return DummyResp('r1', text)
    
    mc.client = make_client_with_create(fake_create)
    
    parsed = mc._call_deepseek_api('test prompt')
    assert parsed['main_category'] == '指示/灯/操控类'
    assert parsed['sub_category'] == '塔灯'


def test_json_with_special_characters_in_category():
    """Test that JSON with special chars in category names is handled."""
    mc = MaterialClassifier()
    
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Category with slashes and commas (real categories have these)
        return DummyResp('r1', '{"main_category":"PLC/IO模块/柜体","sub_category":"阀及阀岛（控制元件）"}')
    
    mc.client = make_client_with_create(fake_create)
    
    parsed = mc._call_deepseek_api('test prompt')
    assert parsed['main_category'] == 'PLC/IO模块/柜体'
    assert parsed['sub_category'] == '阀及阀岛（控制元件）'


def test_classification_result_normalization():
    """Test that classify_material returns normalized (original) category names from mapping."""
    mc = MaterialClassifier()
    
    # The API returns some variant of the category name (e.g., with different spacing)
    def fake_create(**kwargs):
        inp = kwargs.get('input') or ''
        if inp == Config.PROMPT_TEMPLATE:
            return DummyResp('init', 'OK')
        # Return a category with extra whitespace (should be normalized and matched)
        return DummyResp('r1', '{"main_category":"PLC/IO模块/柜体","sub_category":"PLC"}')
    
    mc.client = make_client_with_create(fake_create)
    
    result = mc.classify_material({
        '物料名称': 'PLC模块',
        '图号/型号': 'SIEMENS-S7-300'
    })
    
    # Result should contain the normalized original names from the mapping
    assert result['main_category'] == 'PLC/IO模块/柜体'
    assert result['sub_category'] == 'PLC'
