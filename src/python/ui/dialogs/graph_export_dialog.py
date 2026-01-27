# src/python/ui/dialogs/graph_export_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton, 
    QCheckBox, QComboBox, QLabel, QPushButton, QGraphicsView, 
    QGraphicsScene, QFileDialog, QMessageBox, QButtonGroup
)
from PySide6.QtCore import Qt, QRectF, QSize, QSizeF, QMarginsF
from PySide6.QtGui import QImage, QPainter, QColor, QPen, QPageSize, QPageLayout, QPixmap
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtPrintSupport import QPrinter
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

class GraphExportDialog(QDialog):
    """
    A dialog for exporting the relationship graph with preview and customization options.
    
    Provides options for export scope, format, and visual settings, along with a
    live
    """
    def __init__(self, scene: 'QGraphicsScene', view: 'QGraphicsView', parent=None) -> None:
        """
        Initialize the GraphExportDialog.
        
        :param scene: The QGraphicsScene containing the graph.
        :type scene: :py:class:`~PySide6.QtWidgets.QGraphicsScene`
        :param view: The QGraphicsView displaying the scene.
        :type view: :py:class:`~PySide6.QtWidgets.QGraphicsView`
        :param parent: The parent widget.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget` or None
        
        :rtype: None
        """
        super().__init__(parent)

        self.scene = scene
        self.view = view

        self.setWindowTitle("Export Relationship Graph")
        self.setMinimumSize(700, 600)
        
        self._setup_ui()
        self._connect_signals()
        self._update_preview()

    def _setup_ui(self) -> None:
        """
        Set up the dialog UI components.
        
        :rtype: None
        """
        main_layout = QVBoxLayout(self)

        # Preview Section
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_view = QGraphicsView()
        self.preview_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.preview_view.setFixedHeight(300)
        self.preview_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.preview_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.preview_view.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        
        preview_layout.addWidget(self.preview_view)
        main_layout.addWidget(preview_group)

        # Options Section
        options_layout = QHBoxLayout()

        # Left Column - Scope Options
        scope_group = QGroupBox("Export Scope")
        scope_layout = QVBoxLayout(scope_group)

        self.scope_button_group = QButtonGroup(self)

        self.entire_graph_radio = QRadioButton("Entire Graph")
        self.entire_graph_radio.setChecked(True)
        self.scope_button_group.addButton(self.entire_graph_radio, 0)
        scope_layout.addWidget(self.entire_graph_radio)

        self.current_view_radio = QRadioButton("Current View")
        self.scope_button_group.addButton(self.current_view_radio, 1)
        scope_layout.addWidget(self.current_view_radio)

        self.selected_items_radio = QRadioButton("Selected Items Only")
        self.scope_button_group.addButton(self.selected_items_radio, 2)
        scope_layout.addWidget(self.selected_items_radio)

        # Check if thre are selected items
        if not self.scene.selectedItems():
            self.selected_items_radio.setEnabled(False)
            self.selected_items_radio.setToolTip("No items are currently selected")

        scope_layout.addStretch()
        options_layout.addWidget(scope_group)

        # Right Column - Format and Visual Options
        right_column_layout = QVBoxLayout()

        # Format Options
        format_group = QGroupBox("Format")
        format_layout = QVBoxLayout(format_group)

        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("File Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "SVG", "PDF"])
        format_row.addWidget(self.format_combo)
        format_layout.addLayout(format_row)

        right_column_layout.addWidget(format_group)

        # Visual Options
        visual_group = QGroupBox("Visual Options")
        visual_layout = QVBoxLayout(visual_group)

        self.include_grid_checkbox = QCheckBox("Include Grid")
        self.include_grid_checkbox.setChecked(False)
        visual_layout.addWidget(self.include_grid_checkbox)

        self.transparent_bg_checkbox = QCheckBox("Transparent Background")
        self.transparent_bg_checkbox.setChecked(False)
        visual_layout.addWidget(self.transparent_bg_checkbox)
        
        # Resolution options
        resolution_row = QHBoxLayout()
        resolution_row.addWidget(QLabel("Resolution:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1x (Standard)", "2x (High)", "4x (Very High)"])
        self.resolution_combo.setCurrentIndex(0)
        resolution_row.addWidget(self.resolution_combo)
        visual_layout.addLayout(resolution_row)
        
        visual_layout.addStretch()
        right_column_layout.addWidget(visual_group)
        
        options_layout.addLayout(right_column_layout)
        main_layout.addLayout(options_layout)

        # Button Row
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.export_button = QPushButton("Export...")
        self.export_button.setDefault(True)
        self.export_button.clicked.connect(self._handle_export)
        button_layout.addWidget(self.export_button)
        
        main_layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """
        Connect UI signals to update preview when options change.
        
        :rtype: None
        """
        self.scope_button_group.buttonClicked.connect(self._update_preview)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        self.include_grid_checkbox.stateChanged.connect(self._update_preview)
        self.transparent_bg_checkbox.stateChanged.connect(self._update_preview)

    def _on_format_changed(self) -> None:
        """
        Handle format combo box changes to enable/disable transparent background.
        
        :rtype: None
        """
        is_png = self.format_combo.currentText() == "PNG"
        self.transparent_bg_checkbox.setEnabled(is_png)
        if not is_png:
            self.transparent_bg_checkbox.setChecked(False)

        self._update_preview()

    def _get_export_rect(self) -> QRectF:
        """
        Get the rectangle to export based on current scope selection.
        
        :returns: The rectangle defining the export bounds.
        :rtype: :py:class:`~PySide6.QtCore.QRectF`
        """
        if not self.entire_graph_radio:
            return self.scene.itemsBoundingRect()
        
        elif self.current_view_radio.isChecked():
            viewport_rect = self.view.viewport().rect()
            return self.view.mapToScene(viewport_rect).boundingRect()

        elif self.selected_items_radio.isChecked():
            selected_items = self.scene.selectedItems()
            if not selected_items:
                return self.scene.itemsBoundingRect()
            
            # Calculate bounding rect of selected items
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for item in selected_items:
                item_rect = item.sceneBoundingRect()
                min_x = min(min_x, item_rect.left())
                min_y = min(min_y, item_rect.top())
                max_x = max(max_x, item_rect.right())
                max_y = max(max_y, item_rect.bottom())
            
            return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
        
        return self.scene.itemsBoundingRect()
    
    def _update_preview(self) -> None:
        """
        Update the preview based on current settings.
        
        :rtype: None
        """
        export_rect = self._get_export_rect()

        padding = 20
        export_rect.adjust(-padding, -padding, padding, padding)

        preview_scene = QGraphicsScene()
        preview_scene.setBackgroundBrush(QColor('#212121'))

        # Render the export area to an image
        image_size = QSize(400, 300)
        image = QImage(image_size, QImage.Format.Format_ARGB32)

        if self.transparent_bg_checkbox.isChecked() and self.format_combo.currentText() == "PNG":
            image.fill(Qt.GlobalColor.transparent)
        else:
            image.fill(QColor('#212121'))
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.scene.render(painter, QRectF(image.rect()), export_rect)

        # Draw Grid if requested
        if self.include_grid_checkbox.isChecked() and hasattr(self.view, 'grid_size'):
            self._draw_grid_on_painter(painter, export_rect, image.rect())

        painter.end()

        # Add image to preview scene
        preview_scene.addPixmap(QPixmap.fromImage(image))
        self.preview_view.setScene(preview_scene)
        self.preview_view.fitInView(preview_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _draw_grid_on_painter(self, painter: QPainter, source_rect: QRectF, 
                               target_rect: 'QRectF') -> None:
        """
        Draw grid lines on the painter.
        
        :param painter: The QPainter to draw on.
        :type painter: :py:class:`~PySide6.QtGui.QPainter`
        :param source_rect: The source rectangle in scene coordinates.
        :type source_rect: :py:class:`~PySide6.QtCore.QRectF`
        :param target_rect: The target rectangle in image coordinates.
        :type target_rect: :py:class:`~PySide6.QtCore.QRectF`
        
        :rtype: None
        """
        grid_size = self.view.grid_size
        
        # Calculate scale factor
        scale_x = target_rect.width() / source_rect.width()
        scale_y = target_rect.height() / source_rect.height()
        
        painter.setPen(QPen(QColor(220, 220, 220), 0.5))
        
        # Draw vertical lines
        x = int(source_rect.left()) - (int(source_rect.left()) % grid_size)
        while x <= source_rect.right():
            screen_x = (x - source_rect.left()) * scale_x
            painter.drawLine(int(screen_x), 0, int(screen_x), int(target_rect.height()))
            x += grid_size
        
        # Draw horizontal lines
        y = int(source_rect.top()) - (int(source_rect.top()) % grid_size)
        while y <= source_rect.bottom():
            screen_y = (y - source_rect.top()) * scale_y
            painter.drawLine(0, int(screen_y), int(target_rect.width()), int(screen_y))
            y += grid_size

    def _handle_export(self) -> None:
        """
        Handle the export button click - show file dialog and perform export.
        
        :rtype: None
        """
        file_format = self.format_combo.currentText().lower()
        
        filters = {
            'png': "PNG Image (*.png)",
            'jpg': "JPEG Image (*.jpg *.jpeg)",
            'svg': "SVG Vector (*.svg)",
            'pdf': "PDF Document (*.pdf)"
        }
        
        # Generate default filename
        timestamp = datetime.now().strftime("%Y-%m-%d")
        default_name = f"relationship_graph_{timestamp}.{file_format}"
        
        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Graph",
            default_name,
            filters.get(file_format, "All Files (*.*)")
        )
        
        if not file_path:
            return  # User cancelled
        
        # Ensure correct extension
        path = Path(file_path)
        if path.suffix.lower() != f'.{file_format}':
            file_path = str(path.with_suffix(f'.{file_format}'))
        
        # Perform export
        try:
            if file_format in ['png', 'jpg']:
                self._export_raster(file_path, file_format)
            elif file_format == 'svg':
                self._export_svg(file_path)
            elif file_format == 'pdf':
                self._export_pdf(file_path)
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Graph exported successfully to:\n{file_path}"
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export graph:\n{str(e)}"
            )

    def _export_raster(self, file_path: str, format_type: str) -> None:
        """
        Export the graph as a raster image (PNG or JPG).
        
        :param file_path: The destination file path.
        :type file_path: str
        :param format_type: The image format ('png' or 'jpg').
        :type format_type: str
        
        :rtype: None
        """
        export_rect = self._get_export_rect()
        
        # Add padding
        padding = 20
        export_rect.adjust(-padding, -padding, padding, padding)
        
        # Get resolution multiplier
        resolution_text = self.resolution_combo.currentText()
        multiplier = int(resolution_text[0])  # Extract "1", "2", or "4" from text
        
        # Calculate image size
        width = int(export_rect.width() * multiplier)
        height = int(export_rect.height() * multiplier)
        
        # Create image
        if format_type == 'png' and self.transparent_bg_checkbox.isChecked():
            image = QImage(width, height, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
        else:
            image = QImage(width, height, QImage.Format.Format_RGB32)
            image.fill(QColor('#212121'))
        
        # Render scene
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        self.scene.render(painter, QRectF(0, 0, width, height), export_rect)
        
        # Draw grid if requested
        if self.include_grid_checkbox.isChecked():
            self._draw_grid_on_painter(painter, export_rect, QRectF(0, 0, width, height))
        
        painter.end()
        
        # Save image
        image.save(file_path, format_type.upper())
    
    def _export_svg(self, file_path: str) -> None:
        """
        Export the graph as an SVG vector image.
        
        :param file_path: The destination file path.
        :type file_path: str
        
        :rtype: None
        """
        export_rect = self._get_export_rect()
        
        # Add padding
        padding = 20
        export_rect.adjust(-padding, -padding, padding, padding)
        
        # Create SVG generator
        generator = QSvgGenerator()
        generator.setFileName(file_path)
        generator.setSize(QSize(int(export_rect.width()), int(export_rect.height())))
        generator.setViewBox(QRectF(0, 0, export_rect.width(), export_rect.height()))
        generator.setTitle("Relationship Graph")
        generator.setDescription("Exported from Forgerly")
        
        # Render scene
        painter = QPainter(generator)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background if not transparent
        if not self.transparent_bg_checkbox.isChecked():
            painter.fillRect(QRectF(0, 0, export_rect.width(), export_rect.height()), 
                           QColor('#212121'))
        
        self.scene.render(painter, QRectF(0, 0, export_rect.width(), export_rect.height()), 
                         export_rect)
        
        # Draw grid if requested
        if self.include_grid_checkbox.isChecked():
            self._draw_grid_on_painter(painter, export_rect, 
                                      QRectF(0, 0, export_rect.width(), export_rect.height()))
        
        painter.end()
    
    def _export_pdf(self, file_path: str) -> None:
        """
        Export the graph as a PDF document.
        
        :param file_path: The destination file path.
        :type file_path: str
        
        :rtype: None
        """
        export_rect = self._get_export_rect()
        
        # Add padding
        padding = 20
        export_rect.adjust(-padding, -padding, padding, padding)
        
        # Create PDF printer
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)
        
        # Set page size based on export rect aspect ratio
        page_width_mm = 210  # A4 width
        aspect_ratio = export_rect.height() / export_rect.width()
        page_height_mm = page_width_mm * aspect_ratio
        
        printer.setPageSize(QPageSize(QSizeF(page_width_mm, page_height_mm), 
                                     QPageSize.Unit.Millimeter))
        printer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Unit.Millimeter)
        
        # Render scene
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        self.scene.render(painter, printer.pageRect(QPrinter.Unit.DevicePixel).toRectF(), 
                         export_rect)
        
        # Draw grid if requested
        if self.include_grid_checkbox.isChecked():
            self._draw_grid_on_painter(painter, export_rect, 
                                      printer.pageRect(QPrinter.Unit.DevicePixel).toRectF())