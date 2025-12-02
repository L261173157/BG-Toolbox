#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物料智能分类系统 - GUI主入口
"""

import sys
import os
import pandas as pd
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog, QProgressBar, QGroupBox, QFormLayout, QComboBox, QGridLayout, QSplitter, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSettings
from PySide6.QtGui import QIcon, QFont, QTextCursor, QColor

from material_classifier import MaterialClassifier
from material_manager import MaterialManager
from validate_classifier import ClassifierValidator
from config import Config
import logger


class ClassificationWorker(QThread):
    """分类工作线程，用于处理耗时的分类任务"""
    result_ready = Signal(dict)
    error_occurred = Signal(str)
    progress_update = Signal(int)
    
    def __init__(self, material_data):
        super().__init__()
        self.material_data = material_data
    
    def run(self):
        try:
            # 在后台线程中创建MaterialClassifier实例
            self.classifier = MaterialClassifier()
            result = self.classifier.classify_material(self.material_data)
            self.result_ready.emit(result)
        except Exception as e:
            import traceback
            import logging
            logging.error(f"分类工作线程异常: {str(e)}")
            logging.error(f"异常堆栈: {''.join(traceback.format_exc())}")
            self.error_occurred.emit(str(e))


class BatchProcessingWorker(QThread):
    """批量处理工作线程"""
    progress_update = Signal(int)
    result_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, file_path, max_samples=None):
        super().__init__()
        self.file_path = file_path
        self.max_samples = max_samples
    
    def run(self):
        try:
            # 在后台线程中创建MaterialManager实例
            self.material_manager = MaterialManager()
            # 读取物料数据
            if self.file_path.endswith('.csv'):
                materials = self.material_manager.read_materials_from_csv(self.file_path)
            else:
                materials = self.material_manager.read_materials_from_excel(self.file_path)
            
            # 应用最大样本数限制
            if self.max_samples:
                materials = materials[:self.max_samples]

            total = len(materials)
            results = []

            for i, material in enumerate(materials):
                result = self.material_manager.process_material(material)
                results.append(result)
                progress = int((i + 1) / total * 100)
                self.progress_update.emit(progress)
            
            self.result_ready.emit(results)
        except Exception as e:
            import traceback
            import logging
            logging.error(f"批量处理工作线程异常: {str(e)}")
            logging.error(f"异常堆栈: {''.join(traceback.format_exc())}")
            self.error_occurred.emit(str(e))


class ValidationWorker(QThread):
    """验证工作线程"""
    progress_update = Signal(int)
    result_ready = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, file_path, max_samples=None):
        super().__init__()
        self.file_path = file_path
        self.max_samples = max_samples
    
    def run(self):
        try:
            # 在后台线程中创建ClassifierValidator实例
            self.validator = ClassifierValidator(self.file_path)
            self.validator.load_validation_data()
            # 设置进度回调函数
            self.validator.set_progress_callback(self.progress_update.emit)
            self.validator.validate_batch(max_samples=self.max_samples)
            metrics = self.validator.calculate_metrics()
            self.result_ready.emit(metrics)
        except Exception as e:
            import traceback
            import logging
            logging.error(f"验证工作线程异常: {str(e)}")
            logging.error(f"异常堆栈: {''.join(traceback.format_exc())}")
            self.error_occurred.emit(str(e))


class LogHandler:
    """日志处理器，用于将日志显示到GUI"""
    def __init__(self, text_edit):
        self.text_edit = text_edit
    
    def write(self, message):
        self.text_edit.append(message.strip())
        # 自动滚动到最后
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
    
    def flush(self):
        pass


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_connections()
        self.load_config()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("物料智能分类系统")
        self.setMinimumSize(1000, 700)
        
        # 创建中心控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建TabWidget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(300)
        self.progress_bar.hide()
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 创建各功能标签页
        self.create_classification_tab()
        self.create_batch_processing_tab()
        self.create_validation_tab()
        self.create_config_tab()
        self.create_log_tab()
    
    def create_classification_tab(self):
        """创建单个物料分类标签页"""
        self.classification_tab = QWidget()
        layout = QHBoxLayout(self.classification_tab)
        
        # 左侧：输入表单
        form_group = QGroupBox("物料信息")
        form_layout = QFormLayout(form_group)
        
        self.material_name_edit = QLineEdit()
        self.model_edit = QLineEdit()
        self.brand_edit = QLineEdit()
        self.material_edit = QLineEdit()
        self.supplier_edit = QLineEdit()
        
        form_layout.addRow("物料名称:", self.material_name_edit)
        form_layout.addRow("图号/型号:", self.model_edit)
        form_layout.addRow("分类/品牌:", self.brand_edit)
        form_layout.addRow("材料:", self.material_edit)
        form_layout.addRow("供应商:", self.supplier_edit)
        
        # 分类按钮
        self.classify_button = QPushButton("开始分类")
        self.classify_button.setFixedHeight(40)
        form_layout.addRow("", self.classify_button)
        
        # 右侧：结果展示
        result_group = QGroupBox("分类结果")
        result_layout = QVBoxLayout(result_group)
        
        # 结果显示
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(self.result_text)
        
        # 历史记录
        history_group = QGroupBox("历史记录")
        history_layout = QVBoxLayout(history_group)
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setMaximumHeight(150)
        history_layout.addWidget(self.history_text)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(form_group)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(result_group)
        right_layout.addWidget(history_group)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
        self.tab_widget.addTab(self.classification_tab, "单个物料分类")
    
    def create_batch_processing_tab(self):
        """创建批量处理标签页"""
        self.batch_tab = QWidget()
        layout = QVBoxLayout(self.batch_tab)
        
        # 文件选择
        file_group = QGroupBox("文件选择")
        file_layout = QHBoxLayout(file_group)
        self.file_path_edit = QLineEdit()
        self.browse_button = QPushButton("浏览...")
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_button)
        
        # 批量处理选项
        options_group = QGroupBox("处理选项")
        options_layout = QGridLayout(options_group)
        
        self.max_samples_label = QLabel("最大样本数:")
        self.max_samples_edit = QLineEdit()
        self.max_samples_edit.setPlaceholderText("留空表示全部")
        self.process_button = QPushButton("开始批量处理")
        self.process_button.setFixedHeight(40)
        
        options_layout.addWidget(self.max_samples_label, 0, 0)
        options_layout.addWidget(self.max_samples_edit, 0, 1)
        options_layout.addWidget(self.process_button, 1, 0, 1, 2)
        
        # 结果展示
        result_group = QGroupBox("处理结果")
        result_layout = QVBoxLayout(result_group)
        self.batch_result_text = QTextEdit()
        self.batch_result_text.setReadOnly(True)
        result_layout.addWidget(self.batch_result_text)
        
        # 导出按钮
        export_layout = QHBoxLayout()
        self.export_csv_button = QPushButton("导出为CSV")
        self.export_excel_button = QPushButton("导出为Excel")
        export_layout.addWidget(self.export_csv_button)
        export_layout.addWidget(self.export_excel_button)
        export_layout.addStretch()
        
        layout.addWidget(file_group)
        layout.addWidget(options_group)
        layout.addWidget(result_group)
        layout.addLayout(export_layout)
        
        self.tab_widget.addTab(self.batch_tab, "批量处理")
    
    def create_validation_tab(self):
        """创建分类验证标签页"""
        self.validation_tab = QWidget()
        layout = QVBoxLayout(self.validation_tab)
        
        # 验证文件选择
        file_group = QGroupBox("验证文件选择")
        file_layout = QHBoxLayout(file_group)
        self.validation_file_edit = QLineEdit()
        self.validation_browse_button = QPushButton("浏览...")
        file_layout.addWidget(self.validation_file_edit)
        file_layout.addWidget(self.validation_browse_button)
        
        # 验证选项
        options_group = QGroupBox("验证选项")
        options_layout = QGridLayout(options_group)
        
        self.validation_max_samples_label = QLabel("最大样本数:")
        self.validation_max_samples_edit = QLineEdit()
        self.validation_max_samples_edit.setPlaceholderText("留空表示全部")
        self.validate_button = QPushButton("开始验证")
        self.validate_button.setFixedHeight(40)
        
        options_layout.addWidget(self.validation_max_samples_label, 0, 0)
        options_layout.addWidget(self.validation_max_samples_edit, 0, 1)
        options_layout.addWidget(self.validate_button, 1, 0, 1, 2)
        
        # 验证结果
        result_group = QGroupBox("验证结果")
        result_layout = QGridLayout(result_group)
        
        self.main_accuracy_label = QLabel("大类准确率:")
        self.main_accuracy_value = QLabel("0%")
        self.sub_accuracy_label = QLabel("二级类准确率:")
        self.sub_accuracy_value = QLabel("0%")
        self.full_accuracy_label = QLabel("完全准确率:")
        self.full_accuracy_value = QLabel("0%")
        
        result_layout.addWidget(self.main_accuracy_label, 0, 0)
        result_layout.addWidget(self.main_accuracy_value, 0, 1)
        result_layout.addWidget(self.sub_accuracy_label, 1, 0)
        result_layout.addWidget(self.sub_accuracy_value, 1, 1)
        result_layout.addWidget(self.full_accuracy_label, 2, 0)
        result_layout.addWidget(self.full_accuracy_value, 2, 1)
        
        # 生成报告按钮
        self.generate_report_button = QPushButton("生成详细报告")
        result_layout.addWidget(self.generate_report_button, 3, 0, 1, 2)
        
        layout.addWidget(file_group)
        layout.addWidget(options_group)
        layout.addWidget(result_group)
        
        self.tab_widget.addTab(self.validation_tab, "分类验证")
    
    def create_config_tab(self):
        """创建配置标签页"""
        self.config_tab = QWidget()
        layout = QVBoxLayout(self.config_tab)
        
        # API配置
        api_group = QGroupBox("API配置")
        api_layout = QFormLayout(api_group)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_url_edit = QLineEdit()
        self.api_model_edit = QLineEdit()
        
        api_layout.addRow("DeepSeek API密钥:", self.api_key_edit)
        api_layout.addRow("API URL:", self.api_url_edit)
        api_layout.addRow("模型名称:", self.api_model_edit)
        
        # 请求配置
        request_group = QGroupBox("请求配置")
        request_layout = QFormLayout(request_group)
        
        self.timeout_edit = QLineEdit()
        self.max_retries_edit = QLineEdit()
        self.api_rate_limit_edit = QLineEdit()
        
        request_layout.addRow("超时时间(秒):", self.timeout_edit)
        request_layout.addRow("最大重试次数:", self.max_retries_edit)
        request_layout.addRow("API调用间隔(秒):", self.api_rate_limit_edit)
        
        # 分类文件配置
        file_group = QGroupBox("分类文件配置")
        file_layout = QHBoxLayout(file_group)
        
        self.classification_file_edit = QLineEdit()
        self.classification_file_browse_button = QPushButton("浏览...")
        file_layout.addWidget(self.classification_file_edit)
        file_layout.addWidget(self.classification_file_browse_button)
        
        # 保存按钮
        self.save_config_button = QPushButton("保存配置")
        self.save_config_button.setFixedHeight(40)
        
        layout.addWidget(api_group)
        layout.addWidget(request_group)
        layout.addWidget(file_group)
        layout.addWidget(self.save_config_button, alignment=Qt.AlignRight)
        
        self.tab_widget.addTab(self.config_tab, "配置管理")
    
    def create_log_tab(self):
        """创建日志标签页"""
        self.log_tab = QWidget()
        layout = QVBoxLayout(self.log_tab)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 日志级别
        log_level_layout = QHBoxLayout()
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["INFO", "DEBUG", "ERROR", "WARNING", "CRITICAL"])
        log_level_layout.addWidget(QLabel("日志级别:"))
        log_level_layout.addWidget(self.log_level_combo)
        log_level_layout.addStretch()
        
        # 导出日志按钮
        self.export_log_button = QPushButton("导出日志")
        log_level_layout.addWidget(self.export_log_button)
        
        layout.addLayout(log_level_layout)
        
        self.tab_widget.addTab(self.log_tab, "系统日志")
    
    def init_connections(self):
        """初始化信号和槽连接"""
        # 单个物料分类
        self.classify_button.clicked.connect(self.on_classify_button_clicked)
        
        # 批量处理
        self.browse_button.clicked.connect(self.on_browse_button_clicked)
        self.process_button.clicked.connect(self.on_process_button_clicked)
        self.export_csv_button.clicked.connect(self.on_export_csv_button_clicked)
        self.export_excel_button.clicked.connect(self.on_export_excel_button_clicked)
        
        # 验证功能
        self.validation_browse_button.clicked.connect(self.on_validation_browse_button_clicked)
        self.validate_button.clicked.connect(self.on_validate_button_clicked)
        self.generate_report_button.clicked.connect(self.on_generate_report_button_clicked)
        
        # 配置管理
        self.classification_file_browse_button.clicked.connect(self.on_classification_file_browse_button_clicked)
        self.save_config_button.clicked.connect(self.on_save_config_button_clicked)
        
        # 日志功能
        self.log_level_combo.currentTextChanged.connect(self.on_log_level_changed)
        self.export_log_button.clicked.connect(self.on_export_log_button_clicked)
    
    def on_classify_button_clicked(self):
        """分类按钮点击事件"""
        # 获取物料数据
        material_data = {
            "物料名称": self.material_name_edit.text().strip(),
            "图号/型号": self.model_edit.text().strip(),
            "分类/品牌": self.brand_edit.text().strip(),
            "材料": self.material_edit.text().strip(),
            "供应商": self.supplier_edit.text().strip()
        }
        
        # 验证必填字段
        if not material_data["物料名称"]:
            QMessageBox.warning(self, "警告", "请输入物料名称")
            return
        
        # 禁用分类按钮
        self.classify_button.setEnabled(False)
        self.status_bar.showMessage("正在分类...")
        
        # 创建并启动工作线程
        self.classification_worker = ClassificationWorker(material_data)
        self.classification_worker.result_ready.connect(self.on_classification_result_ready)
        self.classification_worker.error_occurred.connect(self.on_classification_error)
        self.classification_worker.start()
    
    def on_classification_result_ready(self, result):
        """分类结果准备就绪"""
        # 显示结果
        result_str = f"大类: {result['main_category']}\n"
        result_str += f"二级类: {result['sub_category']}\n"
        result_str += f"分类来源: {result['classification_source']}\n"
        self.result_text.setText(result_str)
        
        # 添加到历史记录
        material_name = self.material_name_edit.text().strip()
        history_entry = f"{material_name} -> {result['main_category']}/{result['sub_category']}\n"
        self.history_text.append(history_entry)
        
        # 恢复按钮状态
        self.classify_button.setEnabled(True)
        self.status_bar.showMessage("分类完成")
    
    def on_classification_error(self, error):
        """分类错误处理"""
        QMessageBox.critical(self, "错误", f"分类失败: {error}")
        self.classify_button.setEnabled(True)
        self.status_bar.showMessage("分类失败")
    
    def on_browse_button_clicked(self):
        """浏览文件按钮点击事件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择物料文件", ".", "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def on_process_button_clicked(self):
        """批量处理按钮点击事件"""
        file_path = self.file_path_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择物料文件")
            return
        
        # 获取最大样本数
        max_samples = self.max_samples_edit.text().strip()
        max_samples = int(max_samples) if max_samples else None
        
        # 禁用按钮
        self.process_button.setEnabled(False)
        self.export_csv_button.setEnabled(False)
        self.export_excel_button.setEnabled(False)
        self.status_bar.showMessage("正在批量处理...")
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # 创建并启动工作线程
        self.batch_worker = BatchProcessingWorker(file_path, max_samples)
        self.batch_worker.progress_update.connect(self.on_batch_progress_update)
        self.batch_worker.result_ready.connect(self.on_batch_result_ready)
        self.batch_worker.error_occurred.connect(self.on_batch_error)
        self.batch_worker.start()
    
    def on_batch_progress_update(self, progress):
        """批量处理进度更新"""
        self.progress_bar.setValue(progress)
    
    def on_batch_result_ready(self, results):
        """批量处理结果准备就绪"""
        # 显示结果
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = len(results) - success_count
        result_str = f"处理完成！\n"
        result_str += f"总数量: {len(results)}\n"
        result_str += f"成功: {success_count}\n"
        result_str += f"失败: {failed_count}\n"
        self.batch_result_text.setText(result_str)
        
        # 保存结果供导出使用
        self.batch_results = results
        
        # 恢复按钮状态
        self.process_button.setEnabled(True)
        self.export_csv_button.setEnabled(True)
        self.export_excel_button.setEnabled(True)
        self.status_bar.showMessage("批量处理完成")
        self.progress_bar.hide()
    
    def on_batch_error(self, error):
        """批量处理错误处理"""
        QMessageBox.critical(self, "错误", f"批量处理失败: {error}")
        self.process_button.setEnabled(True)
        self.export_csv_button.setEnabled(True)
        self.export_excel_button.setEnabled(True)
        self.status_bar.showMessage("批量处理失败")
        self.progress_bar.hide()
    
    def on_export_csv_button_clicked(self):
        """导出CSV按钮点击事件"""
        if not hasattr(self, 'batch_results'):
            QMessageBox.warning(self, "警告", "请先进行批量处理")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存结果文件", f"material_classification_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv", "CSV文件 (*.csv)"
        )
        if file_path:
            try:
                # 使用MaterialManager的写入方法
                material_manager = MaterialManager()
                material_manager.write_results_to_csv(self.batch_results, file_path)
                QMessageBox.information(self, "成功", "结果已导出为CSV文件")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")
    
    def on_export_excel_button_clicked(self):
        """导出Excel按钮点击事件"""
        if not hasattr(self, 'batch_results'):
            QMessageBox.warning(self, "警告", "请先进行批量处理")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存结果文件", f"material_classification_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "Excel文件 (*.xlsx)"
        )
        if file_path:
            try:
                # 使用MaterialManager的增量写入方法
                material_manager = MaterialManager()
                for result in self.batch_results:
                    material_manager.write_results_incremental(result, output_excel_path=file_path)
                QMessageBox.information(self, "成功", "结果已导出为Excel文件")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")
    
    def on_validation_browse_button_clicked(self):
        """验证文件浏览按钮点击事件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择验证文件", ".", "Excel文件 (*.xlsx *.xls)"
        )
        if file_path:
            self.validation_file_edit.setText(file_path)
    
    def on_validate_button_clicked(self):
        """验证按钮点击事件"""
        file_path = self.validation_file_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择验证文件")
            return
        
        # 获取最大样本数
        max_samples = self.validation_max_samples_edit.text().strip()
        max_samples = int(max_samples) if max_samples else None
        
        # 禁用按钮
        self.validate_button.setEnabled(False)
        self.generate_report_button.setEnabled(False)
        self.status_bar.showMessage("正在验证...")
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # 创建并启动工作线程
        self.validation_worker = ValidationWorker(file_path, max_samples)
        self.validation_worker.progress_update.connect(self.on_validation_progress_update)
        self.validation_worker.result_ready.connect(self.on_validation_result_ready)
        self.validation_worker.error_occurred.connect(self.on_validation_error)
        self.validation_worker.start()
    
    def on_validation_progress_update(self, progress):
        """验证进度更新"""
        self.progress_bar.setValue(progress)
    
    def on_validation_result_ready(self, metrics):
        """验证结果准备就绪"""
        # 显示结果
        self.main_accuracy_value.setText(f"{metrics['main_accuracy']:.2f}%")
        self.sub_accuracy_value.setText(f"{metrics['sub_accuracy']:.2f}%")
        self.full_accuracy_value.setText(f"{metrics['full_accuracy']:.2f}%")
        
        # 恢复按钮状态
        self.validate_button.setEnabled(True)
        self.generate_report_button.setEnabled(True)
        self.status_bar.showMessage("验证完成")
        self.progress_bar.hide()
    
    def on_validation_error(self, error):
        """验证错误处理"""
        QMessageBox.critical(self, "错误", f"验证失败: {error}")
        self.validate_button.setEnabled(True)
        self.generate_report_button.setEnabled(True)
        self.status_bar.showMessage("验证失败")
        self.progress_bar.hide()
    
    def on_generate_report_button_clicked(self):
        """生成报告按钮点击事件"""
        if not hasattr(self, 'validation_worker'):
            QMessageBox.warning(self, "警告", "请先进行验证")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存验证报告", f"验证报告_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "Excel文件 (*.xlsx)"
        )
        if file_path:
            try:
                report_file = self.validation_worker.validator.generate_report(file_path)
                QMessageBox.information(self, "成功", f"验证报告已生成: {report_file}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"报告生成失败: {e}")
    
    def on_classification_file_browse_button_clicked(self):
        """分类文件浏览按钮点击事件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择分类说明文件", ".", "Excel文件 (*.xlsx *.xls)"
        )
        if file_path:
            self.classification_file_edit.setText(file_path)
    
    def on_save_config_button_clicked(self):
        """保存配置按钮点击事件"""
        # 获取配置
        config = {
            "api_key": self.api_key_edit.text().strip(),
            "api_url": self.api_url_edit.text().strip(),
            "api_model": self.api_model_edit.text().strip(),
            "timeout": self.timeout_edit.text().strip(),
            "max_retries": self.max_retries_edit.text().strip(),
            "api_rate_limit": self.api_rate_limit_edit.text().strip(),
            "classification_file": self.classification_file_edit.text().strip()
        }
        
        # 保存配置
        settings = QSettings("MaterialClassifier", "Config")
        for key, value in config.items():
            settings.setValue(key, value)
        
        QMessageBox.information(self, "成功", "配置已保存")
    
    def on_log_level_changed(self, level):
        """日志级别变化事件"""
        # 更新日志级别
        import logging
        level_map = {
            "INFO": logging.INFO,
            "DEBUG": logging.DEBUG,
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
            "CRITICAL": logging.CRITICAL
        }
        logging.getLogger().setLevel(level_map[level])
    
    def on_export_log_button_clicked(self):
        """导出日志按钮点击事件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存日志文件", f"material_classifier_log_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt", "文本文件 (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "成功", "日志已导出")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"日志导出失败: {e}")
    
    def load_config(self):
        """加载配置"""
        settings = QSettings("MaterialClassifier", "Config")
        
        # 加载API配置
        self.api_key_edit.setText(settings.value("api_key", Config.DEEPSEEK_API_KEY or ""))
        self.api_url_edit.setText(settings.value("api_url", Config.DEEPSEEK_API_URL or ""))
        self.api_model_edit.setText(settings.value("api_model", Config.DEEPSEEK_MODEL or ""))
        
        # 加载请求配置
        self.timeout_edit.setText(settings.value("timeout", str(Config.REQUEST_TIMEOUT or 30)))
        self.max_retries_edit.setText(settings.value("max_retries", str(Config.MAX_RETRIES or 3)))
        self.api_rate_limit_edit.setText(settings.value("api_rate_limit", str(Config.API_RATE_LIMIT or 0.5)))
        
        # 加载分类文件配置
        self.classification_file_edit.setText(settings.value("classification_file", Config.CLASSIFICATION_EXPLANATION_FILE or ""))
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存配置
        self.on_save_config_button_clicked()
        event.accept()


def main():
    """主函数"""
    # 配置全局异常处理，确保任何异常都不会导致程序退出
    import sys
    import traceback
    import logging
    
    def exception_hook(exctype, value, tb):
        """全局异常处理函数"""
        logging.critical(f"全局异常: {exctype.__name__}: {value}")
        logging.critical(f"异常堆栈: {''.join(traceback.format_tb(tb))}")
        # 显示错误对话框
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("应用程序错误")
        msg.setText(f"发生未预期的错误: {exctype.__name__}")
        msg.setInformativeText(str(value))
        msg.setDetailedText(''.join(traceback.format_tb(tb)))
        msg.exec()
    
    # 设置全局异常钩子
    sys.excepthook = exception_hook
    
    # 配置线程异常处理，确保线程中的未捕获异常不会导致程序退出
    import threading
    
    def thread_excepthook(args):
        """线程异常处理函数"""
        logging.critical(f"线程异常: {args.exc_type.__name__}: {args.exc_value}")
        logging.critical(f"异常堆栈: {''.join(traceback.format_tb(args.exc_traceback))}")
    
    # 设置线程异常处理函数
    threading.excepthook = thread_excepthook
    
    # 配置日志处理器，将日志输出到GUI
    # 获取所有现有的日志记录器，并添加GUI日志处理器
    root_logger = logging.getLogger()
    app_logger = logging.getLogger('logger')  # 匹配logger.py中的logger名称
    
    # 设置日志级别
    root_logger.setLevel(logging.INFO)
    app_logger.setLevel(logging.INFO)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # 创建日志处理器，将日志输出到GUI
    log_handler = LogHandler(window.log_text)
    stream_handler = logging.StreamHandler(log_handler)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # 添加处理器到所有相关日志记录器
    root_logger.addHandler(stream_handler)
    app_logger.addHandler(stream_handler)
    
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
