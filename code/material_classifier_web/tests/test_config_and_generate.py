import os
import sys
import pandas as pd

# make project modules importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config
from generate_classification_file import generate_default_classification_file


def test_prompt_template_exists():
    assert hasattr(Config, 'PROMPT_TEMPLATE')
    text = Config.PROMPT_TEMPLATE
    assert '输出格式必须为严格的JSON格式' in text
    assert '示例：' in text


def test_generate_default_classification_file(tmp_path):
    out = tmp_path / 'out.xlsx'
    generate_default_classification_file(str(out))
    assert out.exists()
    df = pd.read_excel(out)
    assert '大类' in df.columns
    assert '二级类' in df.columns
    assert len(df) > 0
