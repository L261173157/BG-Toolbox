import os
import sys
import pandas as pd

# make project modules importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from update_config_from_excel import update_config_prompt_from_excel


def test_update_config_from_excel(tmp_path):
    # create a simple excel with rules
    df = pd.DataFrame([
        {"大类": "单元测试大类", "二级类": "测试子类1"},
        {"大类": "单元测试大类2", "二级类": "测试子类2"},
    ])
    excel_file = tmp_path / 'rules.xlsx'
    df.to_excel(excel_file, index=False)

    # create a temporary config file by copying original config.py
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    orig_config = os.path.join(repo_root, 'config.py')
    temp_config = tmp_path / 'config_tmp.py'
    with open(orig_config, 'r', encoding='utf-8') as fr, open(temp_config, 'w', encoding='utf-8') as fw:
        fw.write(fr.read())

    # run updater
    update_config_prompt_from_excel(str(excel_file), config_path=str(temp_config))

    # assert temp_config contains our rule lines
    with open(temp_config, 'r', encoding='utf-8') as f:
        content = f.read()

    assert '单元测试大类' in content
    assert '测试子类2' in content
