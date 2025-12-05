#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物料分类器验证模块
读取已经人工分类的验证数据,对比AI分类结果,生成详细验证报告
"""

import sys
import io
import pandas as pd
import time
import concurrent.futures
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from material_classifier import MaterialClassifier
from config import Config
from logger import logger

# 设置stdout编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class ClassifierValidator:
    """分类器验证类"""

    def __init__(self, validation_file: str):
        """
        初始化验证器

        参数:
            validation_file: 验证数据Excel文件路径
        """
        self.validation_file = validation_file
        self.classifier = MaterialClassifier()
        self.validation_data = []
        self.results = []
        # 跟踪临时文件
        self.temp_files = []

    def load_validation_data(self) -> List[Dict]:
        """
        加载验证数据

        返回:
            验证数据列表
        """
        try:
            logger.info(f"开始加载验证数据: {self.validation_file}")

            # 读取Excel
            df = pd.read_excel(self.validation_file, engine='openpyxl')

            # 填充NaN
            df = df.fillna("")

            logger.info(f"Excel数据形状: {df.shape}")
            logger.info(f"列名: {df.columns.tolist()}")

            # 提取需要的列
            required_columns = ['物料名称', '图号/型号', '分类/品牌', '功能大类', '二级分类']

            # 检查必需列是否存在
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"缺少必需列: {missing_columns}")

            # 转换为字典列表
            validation_data = []
            for index, row in df.iterrows():
                # 提取物料信息
                material_data = {
                    '物料编码': row.get('物料编码', ''),
                    '物料名称': row.get('物料名称', ''),
                    '图号/型号': row.get('图号/型号', ''),
                    '材料': row.get('材料/描述', ''),
                    '分类/品牌': row.get('分类/品牌', ''),
                    '供应商': row.get('对应品牌或供应商', ''),
                    # 人工分类结果(标准答案)
                    '人工大类': row.get('功能大类', ''),
                    '人工二级类': row.get('二级分类', ''),
                }

                # 只处理有人工分类结果的数据
                if material_data['人工大类'] and material_data['人工二级类']:
                    validation_data.append(material_data)
                else:
                    logger.warning(f"跳过第{index+2}行: 缺少人工分类结果")

            self.validation_data = validation_data
            logger.info(f"成功加载 {len(validation_data)} 条验证数据")

            return validation_data

        except Exception as e:
            logger.error(f"加载验证数据失败: {e}")
            raise

    def normalize_category(self, category: str) -> str:
        """
        标准化分类名称(用于对比)

        处理:
        - 去除前导数字和空格(如"24 辅料/标识广告" -> "辅料/标识广告")
        - 转小写
        - 去除空格和制表符

        参数:
            category: 原始分类名称

        返回:
            标准化后的分类名称
        """
        if not category:
            return ""

        # 转字符串并去除首尾空格
        category = str(category).strip()

        # 去除前导数字和空格(如"24 辅料/标识广告")
        import re
        category = re.sub(r'^\d+\s+', '', category)

        # 标准化:小写、去空格、去制表符
        return category.lower().replace(" ", "").replace("\t", "")

    def validate_single(self, material_data: Dict, classifier = None) -> Dict:
        """
        验证单个物料分类

        参数:
            material_data: 物料数据(包含人工分类结果)
            classifier: 可选的MaterialClassifier实例，如果不提供则使用自己的实例

        返回:
            验证结果
        """
        try:
            # 提取用于分类的信息
            classify_info = {
                '物料名称': material_data['物料名称'],
                '图号/型号': material_data['图号/型号'],
                '材料': material_data['材料'],
                '分类/品牌': material_data['分类/品牌'],
                '供应商': material_data['供应商'],
            }

            # 调用分类器
            logger.info(f"正在分类: {material_data['物料名称']}")
            use_classifier = classifier or self.classifier
            ai_result = use_classifier.classify_material(classify_info)

            # 提取结果
            ai_main = ai_result.get('main_category', '')
            ai_sub = ai_result.get('sub_category', '')
            ai_source = ai_result.get('classification_source', '')  # 识别来源: keyword_matcher 或 ai
            human_main = material_data['人工大类']
            human_sub = material_data['人工二级类']

            # 标准化后对比
            ai_main_norm = self.normalize_category(ai_main)
            ai_sub_norm = self.normalize_category(ai_sub)
            human_main_norm = self.normalize_category(human_main)
            human_sub_norm = self.normalize_category(human_sub)

            # 判断是否匹配
            main_match = (ai_main_norm == human_main_norm)
            sub_match = (ai_sub_norm == human_sub_norm)
            full_match = main_match and sub_match

            # 构建结果
            result = {
                # 物料信息
                '物料编码': material_data.get('物料编码', ''),
                '物料名称': material_data['物料名称'],
                '图号/型号': material_data['图号/型号'],
                '分类/品牌': material_data['分类/品牌'],

                # 人工分类
                '人工大类': human_main,
                '人工二级类': human_sub,

                # AI分类
                'AI大类': ai_main,
                'AI二级类': ai_sub,
                '识别来源': ai_source,  # 新增字段：关键词验证还是AI生成

                # 匹配结果
                '大类匹配': '✓' if main_match else '✗',
                '二级类匹配': '✓' if sub_match else '✗',
                '完全匹配': '✓' if full_match else '✗',

                # 状态
                'status': 'success',
                'error': ''
            }

            logger.info(
                f"分类完成: {material_data['物料名称']} | "
                f"人工: {human_main}/{human_sub} | "
                f"AI: {ai_main}/{ai_sub} | "
                f"匹配: {'✓' if full_match else '✗'}"
            )

            return result

        except Exception as e:
            logger.error(f"验证失败: {material_data['物料名称']} - {e}")
            return {
                '物料编码': material_data.get('物料编码', ''),
                '物料名称': material_data['物料名称'],
                '图号/型号': material_data['图号/型号'],
                '分类/品牌': material_data['分类/品牌'],
                '人工大类': material_data['人工大类'],
                '人工二级类': material_data['人工二级类'],
                'AI大类': '',
                'AI二级类': '',
                '大类匹配': '✗',
                '二级类匹配': '✗',
                '完全匹配': '✗',
                'status': 'failed',
                'error': str(e)
            }

    def validate_batch(self, max_samples: int = None, max_workers: int = 5) -> List[Dict]:
        """
        批量验证

        参数:
            max_samples: 最大样本数(None表示全部)
            max_workers: 最大线程数，默认为5

        返回:
            验证结果列表
        """
        if not self.validation_data:
            raise ValueError("请先调用load_validation_data()加载数据")

        # 限制样本数
        if max_samples:
            # 随机选择指定数量的样本
            import random
            samples = random.sample(self.validation_data, max_samples)
        else:
            samples = self.validation_data
        total_samples = len(samples)

        logger.info(f"开始批量验证: 共 {total_samples} 个样本，使用 {max_workers} 个线程")

        # 创建线程安全的结果列表和锁
        results = []
        results_lock = threading.Lock()

        # 创建临时结果文件用于增量保存
        temp_result_file = f"temp_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self._write_results_header(temp_result_file)
        # 保存临时文件路径，用于后续清理
        self.temp_files.append(temp_result_file)

        # 线程函数，用于初始化自己的MaterialClassifier实例并处理单个物料
        def process_material(idx, material_data):

            try:
                # 为每个线程创建独立的MaterialClassifier实例
                classifier = MaterialClassifier()

                logger.info(f"进度: {idx+1}/{total_samples}")
                result = self.validate_single(material_data, classifier=classifier)

                # 将结果添加到线程安全列表
                with results_lock:
                    results.append(result)
                    self._write_result_to_file(temp_result_file, result)

                # API调用间隔
                time.sleep(Config.API_RATE_LIMIT)

            except Exception as e:
                logger.error(f"处理物料失败: {material_data['物料名称']} - {e}")
                # 即使失败也记录结果
                failed_result = {
                    '物料编码': material_data.get('物料编码', ''),
                    '物料名称': material_data['物料名称'],
                    '图号/型号': material_data['图号/型号'],
                    '分类/品牌': material_data['分类/品牌'],
                    '人工大类': material_data['人工大类'],
                    '人工二级类': material_data['人工二级类'],
                    'AI大类': '',
                    'AI二级类': '',
                    '大类匹配': '✗',
                    '二级类匹配': '✗',
                    '完全匹配': '✗',
                    'status': 'failed',
                    'error': str(e)
                }
                with results_lock:
                    results.append(failed_result)
                    self._write_result_to_file(temp_result_file, failed_result)

        # 使用多线程处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_idx = {executor.submit(process_material, idx, material): idx for idx, material in enumerate(samples)}

            # 等待所有任务完成或捕获异常
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"线程任务 {idx} 失败: {e}")
                    # 异常会在process_material中处理，这里只需记录日志

        logger.info(f"批量验证完成，共处理 {len(results)} 个样本")
        logger.info(f"临时结果文件: {temp_result_file}")

        self.results = results
        return results

    def calculate_metrics(self) -> Dict:
        """
        计算验证指标

        返回:
            指标字典
        """
        if not self.results:
            raise ValueError("请先调用validate_batch()执行验证")

        total = len(self.results)
        success_count = sum(1 for r in self.results if r['status'] == 'success')
        failed_count = total - success_count

        # 只统计成功的样本
        success_results = [r for r in self.results if r['status'] == 'success']

        if not success_results:
            return {
                'total': total,
                'success': 0,
                'failed': failed_count,
                'main_accuracy': 0.0,
                'sub_accuracy': 0.0,
                'full_accuracy': 0.0,
            }

        main_correct = sum(1 for r in success_results if r['大类匹配'] == '✓')
        sub_correct = sum(1 for r in success_results if r['二级类匹配'] == '✓')
        full_correct = sum(1 for r in success_results if r['完全匹配'] == '✓')

        success_total = len(success_results)

        metrics = {
            'total': total,
            'success': success_count,
            'failed': failed_count,
            'main_correct': main_correct,
            'sub_correct': sub_correct,
            'full_correct': full_correct,
            'main_accuracy': (main_correct / success_total * 100) if success_total > 0 else 0,
            'sub_accuracy': (sub_correct / success_total * 100) if success_total > 0 else 0,
            'full_accuracy': (full_correct / success_total * 100) if success_total > 0 else 0,
        }

        return metrics

    def generate_report(self, output_file: str = None) -> str:
        """
        生成验证报告

        参数:
            output_file: 输出文件路径(默认为当前目录下的验证报告_时间戳.xlsx)

        返回:
            报告文件路径
        """
        if not self.results:
            raise ValueError("请先调用validate_batch()执行验证")

        # 生成输出文件名
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"验证报告_{timestamp}.xlsx"

        logger.info(f"开始生成验证报告: {output_file}")

        # 计算指标
        metrics = self.calculate_metrics()

        # 创建Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 1. 详细结果表
            df_results = pd.DataFrame(self.results)
            df_results.to_excel(writer, sheet_name='详细结果', index=False)

            # 2. 汇总统计表
            summary_data = {
                '指标': [
                    '总样本数',
                    '成功样本数',
                    '失败样本数',
                    '大类正确数',
                    '二级类正确数',
                    '完全正确数',
                    '大类准确率(%)',
                    '二级类准确率(%)',
                    '完全准确率(%)',
                ],
                '数值': [
                    metrics['total'],
                    metrics['success'],
                    metrics['failed'],
                    metrics['main_correct'],
                    metrics['sub_correct'],
                    metrics['full_correct'],
                    f"{metrics['main_accuracy']:.2f}",
                    f"{metrics['sub_accuracy']:.2f}",
                    f"{metrics['full_accuracy']:.2f}",
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='汇总统计', index=False)

            # 3. 错误分析表(只包含不匹配的样本)
            error_results = [r for r in self.results if r['完全匹配'] == '✗']
            if error_results:
                df_errors = pd.DataFrame(error_results)
                df_errors.to_excel(writer, sheet_name='错误分析', index=False)

            # 4. 大类混淆矩阵
            confusion_main = self._build_confusion_matrix('大类')
            if not confusion_main.empty:
                confusion_main.to_excel(writer, sheet_name='大类混淆矩阵')

            # 5. 二级类混淆矩阵(可能很大,只记录有错误的)
            confusion_sub = self._build_confusion_matrix('二级类', only_errors=True)
            if not confusion_sub.empty:
                confusion_sub.to_excel(writer, sheet_name='二级类错误矩阵')

        logger.info(f"验证报告生成完成: {output_file}")

        return output_file

    def _build_confusion_matrix(self, category_type: str, only_errors: bool = False) -> pd.DataFrame:
        """
        构建混淆矩阵

        参数:
            category_type: '大类' 或 '二级类'
            only_errors: 是否只包含错误的样本

        返回:
            混淆矩阵DataFrame
        """
        if category_type == '大类':
            human_col = '人工大类'
            ai_col = 'AI大类'
        else:
            human_col = '人工二级类'
            ai_col = 'AI二级类'

        # 过滤成功的结果
        success_results = [r for r in self.results if r['status'] == 'success']

        if not success_results:
            return pd.DataFrame()

        # 如果只要错误,再过滤
        if only_errors:
            match_col = '大类匹配' if category_type == '大类' else '二级类匹配'
            success_results = [r for r in success_results if r[match_col] == '✗']

        if not success_results:
            return pd.DataFrame()

        # 提取数据
        human_categories = [r[human_col] for r in success_results]
        ai_categories = [r[ai_col] for r in success_results]

        # 创建混淆矩阵
        data = []
        for human_cat, ai_cat in zip(human_categories, ai_categories):
            data.append({
                '人工分类': human_cat,
                'AI分类': ai_cat,
                '数量': 1
            })

        df_data = pd.DataFrame(data)

        # 聚合统计
        confusion = df_data.groupby(['人工分类', 'AI分类']).sum().reset_index()
        confusion = confusion.pivot(index='人工分类', columns='AI分类', values='数量')
        confusion = confusion.fillna(0).astype(int)

        return confusion

    def _write_results_header(self, file_path: str):
        """
        写入结果文件的表头

        参数:
            file_path: 结果文件路径
        """
        import csv

        # 定义CSV表头
        fieldnames = ['物料编码', '物料名称', '图号/型号', '分类/品牌',
                     '人工大类', '人工二级类', 'AI大类', 'AI二级类', '识别来源',
                     '大类匹配', '二级类匹配', '完全匹配', 'status', 'error']

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    def _write_result_to_file(self, file_path: str, result: Dict):
        """
        将单个结果写入文件

        参数:
            file_path: 结果文件路径
            result: 验证结果字典
        """
        import csv

        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=result.keys())
            writer.writerow(result)

    def print_summary(self):
        """打印验证摘要"""
        if not self.results:
            print("没有验证结果")
            return

        metrics = self.calculate_metrics()

        print("\n" + "="*80)
        print("验证报告摘要")
        print("="*80)
        print(f"\n总样本数: {metrics['total']}")
        print(f"成功样本数: {metrics['success']}")
        print(f"失败样本数: {metrics['failed']}")
        print(f"\n大类正确数: {metrics['main_correct']}")
        print(f"二级类正确数: {metrics['sub_correct']}")
        print(f"完全正确数: {metrics['full_correct']}")
        print(f"\n大类准确率: {metrics['main_accuracy']:.2f}%")
        print(f"二级类准确率: {metrics['sub_accuracy']:.2f}%")
        print(f"完全准确率: {metrics['full_accuracy']:.2f}%")
        print("="*80)

        # 显示部分错误样本
        error_results = [r for r in self.results if r['完全匹配'] == '✗']
        if error_results:
            print(f"\n错误样本示例(共{len(error_results)}个):")
            print("-"*80)
            for i, err in enumerate(error_results[:5]):  # 只显示前5个
                print(f"\n{i+1}. {err['物料名称']}")
                print(f"   人工分类: {err['人工大类']} / {err['人工二级类']}")
                print(f"   AI分类: {err['AI大类']} / {err['AI二级类']}")

    def cleanup(self):
        """清理临时文件"""
        import os
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.info(f"临时文件已清理: {temp_file}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {temp_file} - {e}")
        # 清空临时文件列表
        self.temp_files.clear()

    def __del__(self):
        """析构函数，自动清理临时文件"""
        self.cleanup()


def main():
    """主函数"""
    print("="*80)
    print("物料分类器验证程序")
    print("="*80)

    # 验证文件路径 - 从配置文件获取
    validation_file = Config.VALIDATION_FILE

    # 创建验证器
    validator = ClassifierValidator(validation_file)

    # 加载验证数据
    print("\n[步骤1] 加载验证数据...")
    validator.load_validation_data()
    print(f"✓ 成功加载 {len(validator.validation_data)} 条验证数据")

    # 询问用户要验证多少条
    print("\n[步骤2] 选择验证样本数")
    print(f"可用样本总数: {len(validator.validation_data)}")
    print("输入要验证的样本数(直接回车验证全部):")

    try:
        user_input = input().strip()
        max_samples = int(user_input) if user_input else None
    except:
        max_samples = None

    if max_samples:
        print(f"将随机验证 {max_samples} 个样本")
    else:
        print("将验证全部样本")

    # 执行验证
    print("\n[步骤3] 执行验证...")
    validator.validate_batch(max_samples=max_samples)

    # 打印摘要
    print("\n[步骤4] 验证完成,生成摘要...")
    validator.print_summary()

    # 生成报告
    print("\n[步骤5] 生成详细报告...")
    report_file = validator.generate_report()
    print(f"✓ 报告已生成: {report_file}")

    print("\n" + "="*80)
    print("验证完成!")
    print("="*80)

    # 手动清理临时文件
    validator.cleanup()


if __name__ == "__main__":
    main()
