import sys
import os
import tempfile
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTextEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QMessageBox,
    QStyleFactory,
    QRadioButton,
    QButtonGroup,
    QScrollArea,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsItem,
    QGraphicsEllipseItem,
    QGraphicsRectItem,
    QGraphicsLineItem,
    QGraphicsTextItem,
    QMenu,
    QInputDialog,
    QGroupBox,
)
from PyQt5.QtCore import (
    Qt, 
    QPointF, 
    QRectF,
    QLineF,
    QSizeF,
    QMimeData,
    QPoint,
)
from PyQt5.QtGui import (
    QFont,
    QPalette,
    QColor,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QPixmap,
    QImage,
    QPen,
    QBrush,
    QPainter,
    QPainterPath,
    QDrag,
    QFontMetrics,
)
from engine.semantics import ActionSemantics
from engine.executor import State
import re
import graphviz
import math  # Add import for math functions

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Color palette for syntax only
        self.colors = {
            'keywords': '#5F0F40',    # bordowy - dla słów kluczowych
            'agents': '#9A031E',      # czerwony - dla agentów
            'fluents': '#CB793A',     # pomarańczowy - dla fluentów
            'conditions': '#FCDC4D',   # żółty - dla warunków
            'initial': '#4CAF50'      # zielony - dla initial state
        }
        
        # Keyword patterns
        self.highlighting_rules = []
        
        # Keywords format (causes, impossible, always, if)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(self.colors['keywords']))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ['causes', 'impossible', 'always', 'if', 'by', 'in', 'from', 'initially']
        for word in keywords:
            pattern = f'\\b{word}\\b'
            self.highlighting_rules.append((re.compile(pattern), keyword_format))
        
        # Initial state format
        initial_format = QTextCharFormat()
        initial_format.setForeground(QColor(self.colors['initial']))
        initial_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((
            re.compile(r'(?<=initially\s)(.+)$', re.MULTILINE),
            initial_format
        ))
        
        # Agents and actions format (inside parentheses)
        agent_format = QTextCharFormat()
        agent_format.setForeground(QColor(self.colors['agents']))
        self.highlighting_rules.append((re.compile(r'\([^)]+\)'), agent_format))
        
        # Fluents and effects format (words after causes/impossible)
        fluent_format = QTextCharFormat()
        fluent_format.setForeground(QColor(self.colors['fluents']))
        self.highlighting_rules.append((
            re.compile(r'(?<=causes\s)(\w+(?:\([^)]*\))?)\s+(\w+)'),
            fluent_format
        ))
        
        # Conditions format (after if)
        condition_format = QTextCharFormat()
        condition_format.setForeground(QColor(self.colors['conditions']))
        self.highlighting_rules.append((
            re.compile(r'(?<=if\s)(.+)$', re.MULTILINE),
            condition_format
        ))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class SyntaxTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighter = SyntaxHighlighter(self.document())
        
        # Set font
        font = QFont('Menlo', 13)
        font.setFixedPitch(True)
        self.setFont(font)

class GraphNode(QGraphicsItem):
    def __init__(self, text, node_type="action", parent=None):
        super().__init__(parent)
        self.text = text
        self.node_type = node_type
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.dragging = False
        self.is_toolbox_item = False
        self.snap_to_line = True  # Enable line snapping by default
        self.being_dragged = False  # New flag to prevent recursive dragging
        
        # Style based on type
        if node_type == "statement":
            self.width = 120
            self.height = 40
            self.color = QColor("#5F0F40")  # bordowy
        elif node_type == "action":
            self.width = 100
            self.height = 40
            self.color = QColor("#9A031E")  # czerwony
        elif node_type == "impossible_action":
            self.width = 100
            self.height = 40
            self.color = QColor("#FF0000")  # jaskrawy czerwony dla zanegowanych akcji
        elif node_type == "effect":
            self.width = 80
            self.height = 80
            self.color = QColor("#CB793A")  # pomarańczowy
        elif node_type == "impossible_effect":
            self.width = 80
            self.height = 80
            self.color = QColor("#FF4500")  # jaskrawy pomarańczowy dla zanegowanych efektów
        elif node_type == "condition":
            self.width = 120
            self.height = 40
            self.color = QColor("#FCDC4D")  # żółty
        elif node_type == "impossible_condition":
            self.width = 120
            self.height = 40
            self.color = QColor("#FFD700")  # jaskrawy żółty dla zanegowanych warunków
        elif node_type == "initial":
            self.width = 120
            self.height = 40
            self.color = QColor("#4CAF50")  # zielony dla initial state
        
        self.edges = []
    
    def boundingRect(self):
        return QRectF(-self.width/2, -self.height/2, self.width, self.height)
    
    def paint(self, painter, option, widget):
        # Set thicker border (4 pixels)
        pen = QPen(self.color, 4)
        
        # Use dashed line for impossible (negated) nodes
        if self.node_type.startswith("impossible_"):
            pen.setStyle(Qt.DashLine)
        
        painter.setPen(pen)
        
        if self.node_type == "initial":
            # Draw hexagon for initial state
            path = QPainterPath()
            w, h = self.width/2, self.height/2
            path.moveTo(-w, 0)
            path.lineTo(-w/2, -h)
            path.lineTo(w/2, -h)
            path.lineTo(w, 0)
            path.lineTo(w/2, h)
            path.lineTo(-w/2, h)
            path.closeSubpath()
            painter.drawPath(path)
        elif self.node_type in ["action", "impossible_action", "statement"]:
            painter.drawRect(self.boundingRect())
        elif self.node_type in ["effect", "impossible_effect"]:
            painter.drawEllipse(self.boundingRect())
        elif self.node_type in ["condition", "impossible_condition"]:
            painter.drawPolygon([
                QPointF(-self.width/2, 0),
                QPointF(0, -self.height/2),
                QPointF(self.width/2, 0),
                QPointF(0, self.height/2),
            ])
        
        # Draw text with "not" prefix for impossible nodes
        painter.setPen(QPen(Qt.black))  # Reset pen for text
        text_to_display = "not " + self.text if self.node_type.startswith("impossible_") else self.text
        painter.drawText(self.boundingRect(), Qt.AlignCenter, text_to_display)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.scene():
                return
                
            views = self.scene().views()
            if not views:
                return
                
            view = views[0]
            if not view:
                return
            
            # If this is a toolbox item, create a new node
            if self.is_toolbox_item and not self.being_dragged:
                self.being_dragged = True  # Set flag to prevent recursive dragging
                drag = QDrag(view)
                mime_data = QMimeData()
                # Don't include node type in mime data for statement types
                if self.node_type == "statement":
                    mime_data.setText(self.text)
                else:
                    mime_data.setText(f"{self.node_type}:{self.text}")
                drag.setMimeData(mime_data)
                
                # Create pixmap of the node for drag visualization
                pixmap = QPixmap(self.boundingRect().size().toSize())
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                self.paint(painter, None, None)
                painter.end()
                
                drag.setPixmap(pixmap)
                drag.setHotSpot(QPoint(int(pixmap.width()/2), int(pixmap.height()/2)))
                
                # Execute drag - original node stays in toolbox
                drag.exec_(Qt.CopyAction)
                self.being_dragged = False  # Reset flag after drag
            else:
                # We're on the canvas - just move the node
                self.dragging = True
                super().mousePressEvent(event)
        
        elif event.button() == Qt.RightButton:
            if not self.scene():
                return
                
            menu = QMenu()
            edit_action = menu.addAction("Edit Text")
            delete_action = menu.addAction("Delete")
            action = menu.exec_(event.screenPos())
            
            if action == edit_action:
                new_text, ok = QInputDialog.getText(None, "Edit Node", "Enter new text:", text=self.text)
                if ok:
                    self.text = new_text
                    if self.scene():
                        self.scene().update_text_from_graph()
            elif action == delete_action:
                scene = self.scene()
                if scene:
                    for edge in self.edges:
                        scene.removeItem(edge)
                    scene.removeItem(self)
                    scene.update_text_from_graph()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            # Update connected edges
            for edge in self.edges:
                edge.updatePosition()
            # Update query text
            if self.scene():
                for view in self.scene().views():
                    if view and isinstance(view.parent(), VisualQueryBuilder):
                        view.parent().update_query_text()
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            super().mouseMoveEvent(event)
            # Update connected edges while dragging
            for edge in self.edges:
                edge.updatePosition()
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Get the new position
            new_pos = value
            
            if self.snap_to_line and not self.is_toolbox_item:
                # Snap to nearest line
                new_y = self.scene().get_nearest_line_y(new_pos.y())
                new_pos = QPointF(new_pos.x(), new_y)
            
            # Update edges
            for edge in self.edges:
                edge.updatePosition()
            
            return new_pos
        return super().itemChange(change, value)

class GraphEdge(QGraphicsLineItem):
    def __init__(self, source_node, target_node, edge_type="causes", parent=None):
        super().__init__(parent)
        self.source_node = source_node
        self.target_node = target_node
        self.edge_type = edge_type
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        
        # Add to nodes' edges lists
        source_node.edges.append(self)
        target_node.edges.append(self)
        
        # Style based on type with thicker lines
        if edge_type == "causes":
            self.setPen(QPen(QColor("#5F0F40"), 3))  # bordowy, thicker
            self.relationship_text = "causes"
        elif edge_type == "impossible":
            self.setPen(QPen(QColor("#9A031E"), 3, Qt.DashLine))  # czerwony, thicker
            self.relationship_text = "impossible"
        elif edge_type == "requires":
            self.setPen(QPen(QColor("#CB793A"), 3))  # pomarańczowy
            self.relationship_text = "requires"
        else:
            self.setPen(QPen(QColor("#5F0F40"), 3))
            self.relationship_text = edge_type
        
        # Create text item for the relationship
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setDefaultTextColor(self.pen().color())
        self.text_item.setPlainText(self.relationship_text)
        # Set font for the text
        font = QFont("Arial", 12)  # Increased from 10 to 12
        font.setBold(True)
        font.setWeight(QFont.ExtraBold)  # Make it extra bold for better visibility
        self.text_item.setFont(font)
        
        self.updatePosition()
    
    def intersectWithNode(self, node, line):
        """Calculate intersection point with node boundary"""
        node_rect = node.boundingRect().translated(node.pos())
        center = node.pos()
        
        if node.node_type == "action":
            # For rectangular nodes (actions)
            points = [
                QPointF(node_rect.left(), node_rect.top()),
                QPointF(node_rect.right(), node_rect.top()),
                QPointF(node_rect.right(), node_rect.bottom()),
                QPointF(node_rect.left(), node_rect.bottom())
            ]
            # Check intersection with each edge of rectangle
            for i in range(4):
                edge_line = QLineF(points[i], points[(i + 1) % 4])
                intersection_point = QPointF()
                if edge_line.intersect(line, intersection_point) == QLineF.BoundedIntersection:
                    return intersection_point
                    
        elif node.node_type == "effect":
            # For circular nodes (effects)
            radius = node.width / 2
            dx = line.dx()
            dy = line.dy()
            if dx == 0 and dy == 0:
                return center
                
            # Normalize direction vector
            length = (dx * dx + dy * dy) ** 0.5
            dx /= length
            dy /= length
            
            # Calculate intersection point
            return QPointF(
                center.x() + dx * radius,
                center.y() + dy * radius
            )
            
        elif node.node_type == "condition":
            # For diamond nodes (conditions)
            points = [
                QPointF(center.x() - node.width/2, center.y()),
                QPointF(center.x(), center.y() - node.height/2),
                QPointF(center.x() + node.width/2, center.y()),
                QPointF(center.x(), center.y() + node.height/2)
            ]
            # Check intersection with each edge of diamond
            for i in range(4):
                edge_line = QLineF(points[i], points[(i + 1) % 4])
                intersection_point = QPointF()
                if edge_line.intersect(line, intersection_point) == QLineF.BoundedIntersection:
                    return intersection_point
        
        return center  # Fallback to center if no intersection found
    
    def updatePosition(self):
        # Create a line from source to target center
        line = QLineF(self.source_node.pos(), self.target_node.pos())
        
        # Get intersection points with both nodes
        start_point = self.intersectWithNode(self.source_node, line)
        end_point = self.intersectWithNode(self.target_node, QLineF(self.target_node.pos(), self.source_node.pos()))
        
        # Update line position
        self.setLine(QLineF(start_point, end_point))
        
        # Update text position - place it in the middle of the line
        if self.text_item:
            text_pos = QPointF(
                (start_point.x() + end_point.x()) / 2,
                (start_point.y() + end_point.y()) / 2
            )
            # Offset the text slightly above the line
            angle = line.angle()
            offset = 15  # pixels
            angle_rad = math.radians(angle)
            text_pos += QPointF(
                -offset * math.sin(angle_rad),
                offset * math.cos(angle_rad)
            )
            
            # Center the text on its position
            text_rect = self.text_item.boundingRect()
            text_pos -= QPointF(text_rect.width() / 2, text_rect.height() / 2)
            self.text_item.setPos(text_pos)
            
            # Rotate text to match line angle if needed
            if 90 < angle < 270:
                # Flip text if line is going "backwards"
                self.text_item.setRotation(angle + 180)
            else:
                self.text_item.setRotation(angle)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            menu = QMenu()
            edit_action = menu.addAction("Edit Type")
            delete_action = menu.addAction("Delete")
            action = menu.exec_(event.screenPos())
            
            if action == edit_action:
                new_type, ok = QInputDialog.getText(None, "Edit Edge", "Enter edge type:", text=self.edge_type)
                if ok:
                    self.edge_type = new_type
                    self.scene().update_text_from_graph()
            elif action == delete_action:
                self.source_node.edges.remove(self)
                self.target_node.edges.remove(self)
                self.scene().removeItem(self)
                self.scene().update_text_from_graph()
        else:
            super().mousePressEvent(event)

class GraphScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-400, -300, 800, 600)
        self.line_spacing = 80  # Increased spacing between lines
        self.snap_threshold = 40  # Increased snap threshold
        self.grid_lines = []  # Store grid lines
        self.line_y_positions = []  # Store Y positions of lines
        self.update_grid_lines()
    
    def update_grid_lines(self):
        # Clear existing grid lines
        for line in self.grid_lines:
            self.removeItem(line)
        self.grid_lines.clear()
        self.line_y_positions.clear()
        
        # Create horizontal grid lines
        rect = self.sceneRect()
        num_lines = int(rect.height() / self.line_spacing)
        start_y = rect.top() + self.line_spacing  # Start below the top edge
        
        for i in range(num_lines):
            y = start_y + i * self.line_spacing
            line = QGraphicsLineItem(rect.left(), y, rect.right(), y)
            # Make lines more visible
            line.setPen(QPen(QColor("#A0A0A0"), 1, Qt.DashLine))  # Darker gray, dashed line
            line.setZValue(-1)  # Put lines behind other items
            self.addItem(line)
            self.grid_lines.append(line)
            self.line_y_positions.append(y)
    
    def get_nearest_line_y(self, y_pos):
        """Get the Y coordinate of the nearest grid line"""
        if not self.line_y_positions:
            return y_pos
            
        # Find the closest line
        closest_y = None
        min_distance = float('inf')
        
        for line_y in self.line_y_positions:
            distance = abs(line_y - y_pos)
            if distance < min_distance:
                min_distance = distance
                closest_y = line_y
        
        # Only snap if we're within the threshold
        if min_distance <= self.snap_threshold:
            return closest_y
        return y_pos
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasText():
            # Get the drop position
            pos = event.scenePos()
            
            # Get the text and create a node
            text = event.mimeData().text()
            if ":" in text:
                node_type, text = text.split(":", 1)
            else:
                # Get the parent VisualQueryBuilder to determine node type
                view = self.views()[0]
                if view and isinstance(view.parent(), VisualQueryBuilder):
                    node_type = view.parent().get_node_type(text)
                else:
                    node_type = "action"  # default type
            
            # Create and position the node
            node = GraphNode(text, node_type)
            self.addItem(node)
            node.setPos(pos)
            
            # Update the query text
            view = self.views()[0]
            if view and isinstance(view.parent(), VisualQueryBuilder):
                view.parent().update_query_text()
            
            event.acceptProposedAction()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            pos = event.scenePos()
            menu = QMenu()
            add_action = menu.addAction("Add Action")
            add_effect = menu.addAction("Add Effect")
            add_condition = menu.addAction("Add Condition")
            action = menu.exec_(event.screenPos())
            
            if action == add_action:
                text, ok = QInputDialog.getText(None, "Add Action", "Enter action name:")
                if ok:
                    node = GraphNode(text, "action")
                    node.setPos(pos)
                    self.addItem(node)
                    self.update_text_from_graph()
            elif action == add_effect:
                text, ok = QInputDialog.getText(None, "Add Effect", "Enter effect name:")
                if ok:
                    node = GraphNode(text, "effect")
                    node.setPos(pos)
                    self.addItem(node)
                    self.update_text_from_graph()
            elif action == add_condition:
                text, ok = QInputDialog.getText(None, "Add Condition", "Enter condition:")
                if ok:
                    node = GraphNode(text, "condition")
                    node.setPos(pos)
                    self.addItem(node)
                    self.update_text_from_graph()
        else:
            super().mousePressEvent(event)
    
    def update_text_from_graph(self):
        """Convert graph to text representation"""
        text = ""
        for item in self.items():
            if isinstance(item, GraphNode):
                if item.node_type == "action":
                    # Find connected effects and conditions
                    for edge in item.edges:
                        if isinstance(edge.target_node, GraphNode):
                            if edge.target_node.node_type == "effect":
                                text += f"causes {item.text} {edge.target_node.text}"
                                # Find conditions
                                conditions = []
                                for cond_edge in edge.target_node.edges:
                                    if isinstance(cond_edge.target_node, GraphNode) and cond_edge.target_node.node_type == "condition":
                                        conditions.append(cond_edge.target_node.text)
                                if conditions:
                                    text += f" if {', '.join(conditions)}"
                                text += "\n"
        
        # Update the text editor
        if self.parent() and hasattr(self.parent(), "update_text"):
            self.parent().update_text(text)

class GraphView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(GraphScene(self))
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setAcceptDrops(True)
        
        # Enable moving items by dragging
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setInteractive(True)
        
        # Set light gray background
        self.setBackgroundBrush(QBrush(QColor("#F5F5F5")))
        
        # Set a reasonable view rect
        self.setSceneRect(-400, -300, 800, 600)
        
        # Set initial transform
        self.resetTransform()
        self.scale(1.0, 1.0)  # Default scale
        
        # Center the view
        self.centerOn(0, 0)
    
    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            # Zoom
            factor = 1.1
            if event.angleDelta().y() < 0:
                factor = 1.0 / factor
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            pos = self.mapToScene(event.pos())
            
            # If text contains node type info
            if ":" in text:
                node_type, node_text = text.split(":", 1)
                node = GraphNode(node_text, node_type)
            else:
                # Determine node type based on text content
                node_type = self.get_node_type(text)
                node = GraphNode(text, node_type)
            
            node.setPos(pos)
            self.scene().addItem(node)
            event.acceptProposedAction()
            
            # Update query text
            if isinstance(self.parent(), VisualQueryBuilder):
                self.parent().update_query_text()
    
    def get_node_type(self, text):
        """Determine the node type based on text content"""
        # Statement types
        if text == "initially":
            return "initial"
        elif text in ["causes", "always", "impossible"]:
            return "statement"
        # Action types
        elif text in ["executable", "accessible", "realisable", "active"]:
            return "action"
        # Effect types
        elif text in ["always", "sometimes", "not"]:
            return "effect"
        # Condition types
        elif text in ["if", "by", "in", "from"]:
            return "condition"
        # Check for negated forms
        elif text.startswith("not "):
            base_text = text[4:]  # Remove "not " prefix
            base_type = self.get_node_type(base_text)
            if base_type == "initial":
                return "impossible_initial"
            return f"impossible_{base_type}" if base_type != "statement" else "statement"
        # Default to condition for other text
        else:
            return "condition"

class VisualQueryBuilder(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.domain_mode = False  # Flag to distinguish between domain and query modes
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Create toolbox for draggable elements
        toolbox = QWidget()
        toolbox_layout = QHBoxLayout(toolbox)
        
        # Statement types
        statement_types = QGroupBox("Statement Types")
        statement_types_layout = QVBoxLayout()
        self.causes_btn = QPushButton("causes")
        self.always_btn = QPushButton("always")
        self.impossible_btn = QPushButton("impossible")
        self.initially_btn = QPushButton("initially")  # Add initially button
        
        for btn in [self.causes_btn, self.always_btn, self.impossible_btn, self.initially_btn]:
            btn.setFixedSize(120, 40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #5F0F40;
                    color: white;
                    border: none;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #7F1F50;
                }
            """)
            statement_types_layout.addWidget(btn)
        
        # Special style for initially button
        self.initially_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        statement_types.setLayout(statement_types_layout)
        
        # Add clear button
        self.clear_btn = QPushButton("Clear Canvas")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #d42828;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e83838;
            }
            QPushButton:pressed {
                background-color: #c41818;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_canvas)
        
        # Query type buttons
        query_types = QGroupBox("Query Types")
        query_types_layout = QVBoxLayout()
        self.executable_btn = QPushButton("executable")
        self.accessible_btn = QPushButton("accessible")
        self.realisable_btn = QPushButton("realisable")
        self.active_btn = QPushButton("active")
        
        for btn in [self.executable_btn, self.accessible_btn, self.realisable_btn, self.active_btn]:
            btn.setFixedSize(120, 40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #9A031E;
                    color: white;
                    border: none;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #BA233E;
                }
            """)
            query_types_layout.addWidget(btn)
        
        query_types.setLayout(query_types_layout)
        
        # Modifiers
        modifiers = QGroupBox("Modifiers")
        modifiers_layout = QVBoxLayout()
        self.sometimes_btn = QPushButton("sometimes")
        self.not_btn = QPushButton("not")
        
        for btn in [self.sometimes_btn, self.not_btn]:
            btn.setFixedSize(120, 40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #CB793A;
                    color: white;
                    border: none;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #DB894A;
                }
            """)
            modifiers_layout.addWidget(btn)
        
        modifiers.setLayout(modifiers_layout)
        
        # Connectors
        connectors = QGroupBox("Connectors")
        connectors_layout = QVBoxLayout()
        self.if_btn = QPushButton("if")
        self.by_btn = QPushButton("by")
        self.from_btn = QPushButton("from")
        self.in_btn = QPushButton("in")
        
        for btn in [self.if_btn, self.by_btn, self.from_btn, self.in_btn]:
            btn.setFixedSize(120, 40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FCDC4D;
                    color: black;
                    border: none;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #FFEC5D;
                }
            """)
            connectors_layout.addWidget(btn)
        
        connectors.setLayout(connectors_layout)
        
        # Variable input
        variables = QGroupBox("Variables")
        variables_layout = QVBoxLayout()
        
        # Action variable
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Action:"))
        self.action_input = QTextEdit()
        self.action_input.setMaximumHeight(40)
        self.action_input.setPlaceholderText("Enter action name")
        action_layout.addWidget(self.action_input)
        self.add_action_btn = QPushButton("Add")
        self.add_action_btn.clicked.connect(lambda: self.add_variable("action"))
        action_layout.addWidget(self.add_action_btn)
        variables_layout.addLayout(action_layout)
        
        # Effect variable
        effect_layout = QHBoxLayout()
        effect_layout.addWidget(QLabel("Effect:"))
        self.effect_input = QTextEdit()
        self.effect_input.setMaximumHeight(40)
        self.effect_input.setPlaceholderText("Enter effect name")
        effect_layout.addWidget(self.effect_input)
        self.add_effect_btn = QPushButton("Add")
        self.add_effect_btn.clicked.connect(lambda: self.add_variable("effect"))
        effect_layout.addWidget(self.add_effect_btn)
        variables_layout.addLayout(effect_layout)
        
        # Condition variable
        condition_layout = QHBoxLayout()
        condition_layout.addWidget(QLabel("Condition:"))
        self.condition_input = QTextEdit()
        self.condition_input.setMaximumHeight(40)
        self.condition_input.setPlaceholderText("Enter condition")
        condition_layout.addWidget(self.condition_input)
        self.add_condition_btn = QPushButton("Add")
        self.add_condition_btn.clicked.connect(lambda: self.add_variable("condition"))
        condition_layout.addWidget(self.add_condition_btn)
        variables_layout.addLayout(condition_layout)
        
        variables.setLayout(variables_layout)
        
        # Available elements from domain
        self.domain_elements = QGroupBox("Domain Elements")
        self.domain_elements_layout = QVBoxLayout()
        self.domain_elements.setLayout(self.domain_elements_layout)
        
        # Add groups to toolbox
        toolbox_layout.addWidget(statement_types)
        toolbox_layout.addWidget(query_types)
        toolbox_layout.addWidget(modifiers)
        toolbox_layout.addWidget(connectors)
        toolbox_layout.addWidget(variables)
        toolbox_layout.addWidget(self.domain_elements)
        toolbox_layout.addWidget(self.clear_btn)
        toolbox_layout.addStretch()
        
        # Create canvas for building queries
        self.canvas = GraphView()
        self.canvas.setMinimumHeight(400)
        self.canvas.setAcceptDrops(True)
        
        # Create query text display
        self.query_text = QTextEdit()
        self.query_text.setReadOnly(True)
        self.query_text.setMaximumHeight(100)
        self.query_text.setPlaceholderText("Your query will appear here...")
        
        # Add execute button
        self.execute_btn = QPushButton("Execute Query")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
        """)
        
        # Add components to main layout
        layout.addWidget(toolbox)
        layout.addWidget(self.canvas)
        layout.addWidget(QLabel("Generated Query:"))
        layout.addWidget(self.query_text)
        layout.addWidget(self.execute_btn)
        
        # Connect signals
        for btn in [self.causes_btn, self.always_btn, self.impossible_btn,
                   self.executable_btn, self.accessible_btn, self.realisable_btn, self.active_btn,
                   self.sometimes_btn, self.not_btn,
                   self.if_btn, self.by_btn, self.from_btn, self.in_btn]:
            btn.clicked.connect(self.add_element)
        
        self.execute_btn.clicked.connect(self.execute_query)
        
        # Initialize drag-and-drop functionality
        self.setup_drag_drop()
    
    def position_node(self, node):
        """Position a new node on the canvas"""
        scene = self.canvas.scene()
        if not scene:
            return
            
        # For toolbox items, position them in the toolbox area
        if node.is_toolbox_item:
            items = [item for item in scene.items() if isinstance(item, GraphNode) and item.is_toolbox_item]
            if items:
                last_item = items[-1]
                node.setPos(last_item.pos() + QPointF(150, 0))
            else:
                node.setPos(-350, -250)  # Top-left corner of toolbox area
        else:
            # For regular items (variables), position them in the main canvas area
            # Use the first guide line's Y position, or a default if no lines exist
            if scene.line_y_positions:
                line_y = scene.line_y_positions[0]
            else:
                line_y = -100  # Default Y position if no guide lines
            
            # Find all nodes on this line
            nodes_on_line = []
            for item in scene.items():
                if isinstance(item, GraphNode) and not item.is_toolbox_item:
                    if abs(item.pos().y() - line_y) < 5:  # Same line tolerance
                        nodes_on_line.append(item)
            
            # Position the new node
            if nodes_on_line:
                # Find rightmost node
                rightmost_x = max(node.pos().x() for node in nodes_on_line)
                node.setPos(rightmost_x + 120, line_y)  # Place to the right with some spacing
            else:
                node.setPos(-200, line_y)  # Start position on the line
            
            # Ensure the node is visible in the view
            if self.canvas:
                self.canvas.ensureVisible(node)
    
    def add_variable(self, var_type):
        """Add a variable node from input"""
        input_widget = getattr(self, f"{var_type}_input")
        text = input_widget.toPlainText().strip()
        if text:
            # Create node with appropriate type
            if var_type == "action":
                node = GraphNode(text, "action")
            elif var_type == "effect":
                node = GraphNode(text, "effect")
            else:  # condition
                node = GraphNode(text, "condition")
            
            # Add to scene as a regular (non-toolbox) item
            node.is_toolbox_item = False
            scene = self.canvas.scene()
            if scene:
                scene.addItem(node)
                # Position the node
                self.position_node(node)
                # Ensure it's visible
                self.canvas.ensureVisible(node)
                # Center on the node
                self.canvas.centerOn(node)
            
            input_widget.clear()
            self.update_query_text()
    
    def setup_drag_drop(self):
        """Set up drag and drop functionality"""
        self.setAcceptDrops(True)
        for btn in [self.causes_btn, self.always_btn, self.impossible_btn,
                   self.executable_btn, self.accessible_btn, self.realisable_btn, self.active_btn,
                   self.sometimes_btn, self.not_btn,
                   self.if_btn, self.by_btn, self.from_btn, self.in_btn]:
            btn.setMouseTracking(True)
            btn.mousePressEvent = lambda e, b=btn: self.button_press(e, b)
    
    def button_press(self, event, button):
        """Handle button press for drag and drop"""
        if event.button() == Qt.LeftButton:
            drag = QDrag(button)
            mime_data = QMimeData()
            mime_data.setText(button.text())
            drag.setMimeData(mime_data)
            drag.exec_(Qt.MoveAction)  # Changed from CopyAction to MoveAction
    
    def add_element(self):
        """Add a new element to the query canvas"""
        sender = self.sender()
        text = sender.text()
        node_type = self.get_node_type(text)
        
        # Create new node and mark it as a toolbox item
        node = GraphNode(text, node_type)
        node.is_toolbox_item = True  # Mark as toolbox item
        self.canvas.scene().addItem(node)
        self.position_node(node)
        
        # Update the query text
        self.update_query_text()
    
    def get_node_type(self, text):
        """Determine the node type based on text content"""
        # Statement types
        if text == "initially":
            return "initial"
        elif text in ["causes", "always", "impossible"]:
            return "statement"
        # Action types
        elif text in ["executable", "accessible", "realisable", "active"]:
            return "action"
        # Effect types
        elif text in ["always", "sometimes", "not"]:
            return "effect"
        # Condition types
        elif text in ["if", "by", "in", "from"]:
            return "condition"
        # Check for negated forms
        elif text.startswith("not "):
            base_text = text[4:]  # Remove "not " prefix
            base_type = self.get_node_type(base_text)
            if base_type == "initial":
                return "impossible_initial"
            return f"impossible_{base_type}" if base_type != "statement" else "statement"
        # Default to condition for other text
        else:
            return "condition"
    
    def update_query_text(self):
        """Convert graph to text representation"""
        scene = self.canvas.scene()
        if not scene:
            return
            
        # Get all non-toolbox nodes
        nodes = [item for item in scene.items() if isinstance(item, GraphNode)]
        
        # Group nodes by their Y position (with some tolerance)
        lines = {}
        tolerance = 5  # pixels tolerance for grouping
        
        for node in nodes:
            # Skip toolbox template items but include user-added variables
            if node.is_toolbox_item:
                continue
                
            y_pos = node.pos().y()
            # Find the closest existing line
            matched = False
            for line_y in lines.keys():
                if abs(line_y - y_pos) <= tolerance:
                    lines[line_y].append(node)
                    matched = True
                    break
            if not matched:
                lines[y_pos] = [node]
        
        # Sort nodes in each line by x position
        for line_nodes in lines.values():
            line_nodes.sort(key=lambda node: node.pos().x())
        
        # Convert lines to query text
        query_parts = []
        
        # Process lines from top to bottom
        for y in sorted(lines.keys()):
            line_nodes = lines[y]
            if not line_nodes:
                continue
            
            # Build statement from the line's nodes
            line_parts = []
            for node in line_nodes:
                if node.node_type == "initial" or node.node_type == "impossible_initial":
                    # Handle initial state declarations
                    if not line_parts:
                        line_parts.append("initially")
                    text = "not " + node.text if node.node_type == "impossible_initial" else node.text
                    if len(line_parts) > 1:
                        line_parts.append(",")
                    line_parts.append(text)
                else:
                    line_parts.append(node.text)
            
            if line_parts:
                # Special formatting for query types
                if line_parts[0] in ["executable", "accessible", "realisable", "active"]:
                    query_type = line_parts[0]
                    remaining_parts = line_parts[1:]
                    
                    if query_type == "executable":
                        query_parts.append(f"{query_type} {'; '.join(remaining_parts)}")
                    elif query_type == "accessible":
                        if "from" in remaining_parts:
                            from_idx = remaining_parts.index("from")
                            target = remaining_parts[:from_idx]
                            conditions = remaining_parts[from_idx + 1:]
                            query_parts.append(f"{query_type} {' '.join(target)} from {' '.join(conditions)}")
                        else:
                            query_parts.append(f"{query_type} {' '.join(remaining_parts)}")
                    elif query_type in ["realisable", "active"]:
                        if "by" in remaining_parts:
                            by_idx = remaining_parts.index("by")
                            actions = remaining_parts[:by_idx]
                            agents = remaining_parts[by_idx + 1:]
                            if query_type == "realisable":
                                query_parts.append(f"{query_type} {'; '.join(actions)} by {', '.join(agents)}")
                            else:
                                query_parts.append(f"{query_type} {' '.join(actions)} by {', '.join(agents)}")
                        else:
                            query_parts.append(f"{query_type} {' '.join(remaining_parts)}")
                else:
                    # Regular statement (causes, impossible, initially, etc.)
                    query_parts.append(" ".join(line_parts))
        
        # Join all parts with newlines
        query = "\n".join(query_parts)
        self.query_text.setText(query)
    
    def execute_query(self):
        """Execute the current query"""
        query = self.query_text.toPlainText()
        if query:
            # Get the main window instance
            main_window = self.window()
            if isinstance(main_window, MainWindow):
                main_window.execute_query_text(query)
    
    def update_domain_elements(self, domain_text):
        """Update available domain elements"""
        # Clear existing elements
        for i in reversed(range(self.domain_elements_layout.count())):
            widget = self.domain_elements_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Parse domain text to extract actions and conditions
        actions = set()
        conditions = set()
        
        for line in domain_text.split('\n'):
            if not line.strip():
                continue
            
            parts = line.split()
            if not parts:
                continue
            
            if parts[0] == "causes":
                # Extract action
                action = parts[1]
                if "(" in action:
                    action = action[:action.index("(")]
                actions.add(action)
                
                # Extract effect
                effect = parts[2]
                conditions.add(effect)
                
                # Extract conditions after "if"
                try:
                    if_idx = parts.index("if")
                    conditions_part = " ".join(parts[if_idx + 1:])
                    for cond in conditions_part.split(","):
                        cond = cond.strip()
                        if cond.startswith("not "):
                            cond = cond[4:]
                        conditions.add(cond)
                except ValueError:
                    # No "if" found, continue without conditions
                    pass
            
            elif parts[0] == "impossible":
                # Extract action
                action = parts[1]
                if "(" in action:
                    action = action[:action.index("(")]
                actions.add(action)
                
                # Extract conditions after "if"
                try:
                    if_idx = parts.index("if")
                    conditions_part = " ".join(parts[if_idx + 1:])
                    for cond in conditions_part.split(","):
                        cond = cond.strip()
                        if cond.startswith("not "):
                            cond = cond[4:]
                        conditions.add(cond)
                except ValueError:
                    # No "if" found, continue without conditions
                    pass
        
        # Create buttons for actions
        if actions:
            actions_group = QGroupBox("Actions")
            actions_layout = QVBoxLayout()
            for action in sorted(actions):
                btn = QPushButton(action)
                btn.setFixedSize(120, 40)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #9A031E;
                        color: white;
                        border: none;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background-color: #BA233E;
                    }
                """)
                btn.clicked.connect(lambda checked, a=action: self.add_domain_element(a, "action"))
                actions_layout.addWidget(btn)
            actions_group.setLayout(actions_layout)
            self.domain_elements_layout.addWidget(actions_group)
        
        # Create buttons for conditions
        if conditions:
            conditions_group = QGroupBox("Conditions")
            conditions_layout = QVBoxLayout()
            for condition in sorted(conditions):
                btn = QPushButton(condition)
                btn.setFixedSize(120, 40)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FCDC4D;
                        color: black;
                        border: none;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background-color: #FFEC5D;
                    }
                """)
                btn.clicked.connect(lambda checked, c=condition: self.add_domain_element(c, "condition"))
                conditions_layout.addWidget(btn)
            conditions_group.setLayout(conditions_layout)
            self.domain_elements_layout.addWidget(conditions_group)
    
    def add_domain_element(self, text, element_type):
        """Add a domain element to the canvas"""
        node = GraphNode(text, element_type)
        node.is_toolbox_item = True  # Mark as toolbox item
        self.canvas.scene().addItem(node)
        self.position_node(node)
        self.update_query_text()
    
    def clear_canvas(self):
        """Clear all items from the canvas except guide lines"""
        scene = self.canvas.scene()
        if not scene:
            return
            
        # Store guide line coordinates
        rect = scene.sceneRect()
        line_positions = scene.line_y_positions[:]
        
        # Clear everything
        scene.clear()
        
        # Reset grid lines lists
        scene.grid_lines = []
        scene.line_y_positions = []
        
        # Recreate guide lines
        for y in line_positions:
            line = QGraphicsLineItem(rect.left(), y, rect.right(), y)
            line.setPen(QPen(QColor("#A0A0A0"), 1, Qt.DashLine))
            line.setZValue(-1)
            scene.addItem(line)
            scene.grid_lines.append(line)
            scene.line_y_positions.append(y)
        
        # Clear query text
        self.query_text.clear()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Agent Action Programs Analysis System")
        self.setMinimumSize(1200, 800)
        
        # Initialize semantics engine
        self.semantics = ActionSemantics()
        
        # Set the application style for dark mode
        self.setup_dark_mode()
        
        # Create the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create left panel (problem selection and controls)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Problem selection
        problem_label = QLabel("Select Problem:")
        self.problem_combo = QComboBox()
        self.problem_combo.addItems([
            "Tank Crew Mission",
            "Football Team",
            "Rescue Team",
            "Fire Brigade",
            "Medical Diagnosis"
        ])
        self.problem_combo.currentTextChanged.connect(self.load_problem)
        
        # View mode selection
        view_mode_group = QWidget()
        view_mode_layout = QHBoxLayout(view_mode_group)
        self.text_mode_radio = QRadioButton("Text Mode")
        self.graph_mode_radio = QRadioButton("Graph Mode")
        self.text_mode_radio.setChecked(True)
        view_mode_layout.addWidget(self.text_mode_radio)
        view_mode_layout.addWidget(self.graph_mode_radio)
        
        # Create button group
        self.view_mode_group = QButtonGroup()
        self.view_mode_group.addButton(self.text_mode_radio)
        self.view_mode_group.addButton(self.graph_mode_radio)
        self.view_mode_group.buttonClicked.connect(self.switch_view_mode)
        
        # Add components to left panel
        left_layout.addWidget(problem_label)
        left_layout.addWidget(self.problem_combo)
        left_layout.addWidget(view_mode_group)
        left_layout.addStretch()
        
        # Create right panel (main content)
        right_panel = QTabWidget()
        
        # Domain Editor Tab
        domain_tab = QWidget()
        domain_layout = QVBoxLayout(domain_tab)
        
        # Create text and graph editors
        self.domain_editor = SyntaxTextEdit()
        self.domain_graph = GraphView()
        self.domain_graph.hide()
        
        # Add Apply Domain button
        apply_domain_btn = QPushButton("Apply Domain Definition")
        apply_domain_btn.clicked.connect(self.apply_domain)
        
        domain_layout.addWidget(QLabel("Domain Definition:"))
        domain_layout.addWidget(self.domain_editor)
        domain_layout.addWidget(self.domain_graph)
        domain_layout.addWidget(apply_domain_btn)
        
        # Query Tab
        query_tab = QWidget()
        query_layout = QVBoxLayout(query_tab)
        
        # Create text and graph editors for query
        self.query_editor = SyntaxTextEdit()
        self.query_graph = GraphView()
        self.query_graph.hide()
        
        # Create text and graph views for results
        self.query_result = QTextEdit()
        self.query_result.setReadOnly(True)
        self.result_graph = GraphView()
        self.result_graph.hide()
        
        # Add Execute Query button
        execute_query_btn = QPushButton("Execute Query")
        execute_query_btn.clicked.connect(self.execute_query)
        
        query_layout.addWidget(QLabel("Query:"))
        query_layout.addWidget(self.query_editor)
        query_layout.addWidget(self.query_graph)
        query_layout.addWidget(execute_query_btn)
        query_layout.addWidget(QLabel("Result:"))
        query_layout.addWidget(self.query_result)
        query_layout.addWidget(self.result_graph)
        
        # Visual Query Builder Tab
        self.visual_query_tab = VisualQueryBuilder()
        
        # Add tabs
        right_panel.addTab(domain_tab, "Domain Editor")
        right_panel.addTab(query_tab, "Query Analysis")
        right_panel.addTab(self.visual_query_tab, "Visual Query Builder")
        
        # Add panels to main layout
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 4)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Load initial problem
        self.load_problem(self.problem_combo.currentText())
    
    def switch_view_mode(self, button):
        """Switch between text and graph view modes"""
        if button == self.text_mode_radio:
            self.domain_editor.show()
            self.domain_graph.hide()
            self.query_editor.show()
            self.query_graph.hide()
            self.query_result.show()
            self.result_graph.hide()
        else:
            self.domain_editor.hide()
            self.domain_graph.show()
            self.query_editor.hide()
            self.query_graph.show()
            self.query_result.hide()
            self.result_graph.show()
            # Update graphs
            self.update_graphs()
    
    def update_graphs(self):
        """Update all graph views from text"""
        # Update domain graph
        self.update_domain_graph()
        # Update query graph
        self.update_query_graph()
        # Update result graph
        self.update_result_graph()
    
    def update_domain_graph(self):
        """Convert domain text to graph"""
        scene = self.domain_graph.scene()
        scene.clear()
        
        text = self.domain_editor.toPlainText()
        lines = text.split('\n')
        
        nodes = {}
        for line in lines:
            if not line.strip():
                continue
            
            parts = line.split()
            if not parts:
                continue
                
            if parts[0] == "initially":
                # Handle initial state declarations
                initial_conditions = line[len("initially"):].strip()
                conditions = [c.strip() for c in initial_conditions.split(",")]
                
                for condition in conditions:
                    condition_type = "initial"
                    condition_name = condition
                    
                    # Check if condition is negated
                    if condition.startswith("not "):
                        condition_name = condition[4:]
                        condition_type = "impossible_initial"
                    
                    if condition_name not in nodes:
                        node = GraphNode(condition_name, condition_type)
                        scene.addItem(node)
                        nodes[condition_name] = node
                
            elif parts[0] == "causes" or parts[0] == "impossible":
                # Get action name (parts[1])
                action_name = parts[1]
                action_type = "action" if parts[0] == "causes" else "impossible_action"
                
                # Create action node if it doesn't exist
                if action_name not in nodes:
                    action_node = GraphNode(action_name, action_type)
                    scene.addItem(action_node)
                    nodes[action_name] = action_node
                
                if parts[0] == "causes":
                    # Get effect
                    effect_index = 2
                    effect_name = parts[effect_index]
                    effect_type = "effect"
                    
                    # Check if the effect is negated (either as "not effect" or "neg_effect")
                    if effect_index + 1 < len(parts) and parts[effect_index] == "not":
                        effect_name = parts[effect_index + 1]
                        effect_type = "impossible_effect"
                    elif effect_name.startswith("neg_"):
                        effect_name = effect_name[4:]  # Remove "neg_" prefix
                        effect_type = "impossible_effect"
                    
                    if effect_name not in nodes:
                        effect_node = GraphNode(effect_name, effect_type)
                        scene.addItem(effect_node)
                        nodes[effect_name] = effect_node
                    
                    # Create edge
                    edge = GraphEdge(nodes[action_name], nodes[effect_name], "causes")
                    scene.addItem(edge)
                
                # Add conditions if they exist
                if "if" in line:
                    conditions_part = line[line.index("if") + 2:].strip()
                    conditions = [c.strip() for c in conditions_part.split(",")]
                    
                    for condition in conditions:
                        condition_type = "condition"
                        condition_name = condition
                        
                        # Check if condition is negated (either as "not condition" or "neg_condition")
                        if condition.startswith("not "):
                            condition_name = condition[4:]
                            condition_type = "impossible_condition"
                        elif condition.startswith("neg_"):
                            condition_name = condition[4:]
                            condition_type = "impossible_condition"
                        
                        if condition_name not in nodes:
                            condition_node = GraphNode(condition_name, condition_type)
                            scene.addItem(condition_node)
                            nodes[condition_name] = condition_node
                        
                        # Connect condition to action or effect based on statement type
                        if parts[0] == "causes":
                            edge = GraphEdge(nodes[effect_name], nodes[condition_name], "requires")
                        else:  # impossible
                            edge = GraphEdge(nodes[action_name], nodes[condition_name], "requires")
                        scene.addItem(edge)
        
        # Arrange nodes in a grid
        self.arrange_nodes(scene)
    
    def arrange_nodes(self, scene):
        """Arrange nodes in a grid layout"""
        x, y = -300, -200
        spacing = 150
        items_per_row = 4
        current_item = 0
        
        for item in scene.items():
            if isinstance(item, GraphNode):
                item.setPos(x + (current_item % items_per_row) * spacing,
                          y + (current_item // items_per_row) * spacing)
                current_item += 1
        
        # Update edges
        for item in scene.items():
            if isinstance(item, GraphEdge):
                item.updatePosition()
    
    def update_query_graph(self):
        """Convert query text to graph"""
        scene = self.query_graph.scene()
        scene.clear()
        
        text = self.query_editor.toPlainText()
        lines = text.split('\n')
        
        nodes = {}
        for line in lines:
            if not line.strip():
                continue
            
            # Tokenize the line while preserving parentheses content
            tokens = []
            current_token = []
            in_parentheses = False
            
            words = line.split()
            i = 0
            while i < len(words):
                word = words[i]
                
                # Handle 'not' token
                if word == 'not':
                    # Look ahead to next token
                    if i + 1 < len(words):
                        next_word = words[i + 1]
                        # If next token starts with '(', collect everything until matching ')'
                        if '(' in next_word:
                            paren_count = next_word.count('(')
                            content = [next_word]
                            i += 1
                            while i + 1 < len(words) and paren_count > 0:
                                i += 1
                                curr = words[i]
                                content.append(curr)
                                paren_count += curr.count('(')
                                paren_count -= curr.count(')')
                            tokens.append('not ' + ' '.join(content))
                        else:
                            # Just combine 'not' with next token
                            tokens.append('not ' + next_word)
                            i += 1
                    i += 1
                    continue
                
                # Handle regular tokens
                if '(' in word:
                    paren_count = word.count('(')
                    content = [word]
                    while i + 1 < len(words) and paren_count > 0:
                        i += 1
                        curr = words[i]
                        content.append(curr)
                        paren_count += curr.count('(')
                        paren_count -= curr.count(')')
                    tokens.append(' '.join(content))
                else:
                    tokens.append(word)
                i += 1
            
            if not tokens:
                continue
            
            # Handle different query types
            if tokens[0] == "executable":
                # Create nodes for each action in the program
                prev_node = None
                for token in tokens[1:]:
                    node_text = token
                    node_type = "action"
                    
                    # Handle negated actions
                    if token.startswith('not '):
                        node_text = token[4:]  # Remove 'not ' prefix
                        node_type = "impossible_action"
                    
                    if node_text not in nodes:
                        node = GraphNode(node_text, node_type)
                        scene.addItem(node)
                        nodes[node_text] = node
                    
                    # Connect sequential actions
                    if prev_node:
                        edge = GraphEdge(prev_node, nodes[node_text], "next")
                        scene.addItem(edge)
                    prev_node = nodes[node_text]
                    
            elif tokens[0] == "accessible":
                # Create nodes for actions and goal state
                goal = tokens[-1]
                goal_text = goal
                goal_type = "effect"
                
                # Handle negated goal
                if goal.startswith('not '):
                    goal_text = goal[4:]  # Remove 'not ' prefix
                    goal_type = "impossible_effect"
                
                goal_node = GraphNode(goal_text, goal_type)
                scene.addItem(goal_node)
                nodes[goal_text] = goal_node
                
                # Add action nodes
                for token in tokens[1:-1]:
                    node_text = token
                    node_type = "action"
                    
                    # Handle negated actions
                    if token.startswith('not '):
                        node_text = token[4:]  # Remove 'not ' prefix
                        node_type = "impossible_action"
                    
                    if node_text not in nodes:
                        node = GraphNode(node_text, node_type)
                        scene.addItem(node)
                        nodes[node_text] = node
                        # Connect action to goal
                        edge = GraphEdge(node, goal_node, "leads to")
                        scene.addItem(edge)
                        
            elif tokens[0] == "realisable":
                # Find 'by' index
                try:
                    group_idx = tokens.index("by")
                except ValueError:
                    continue
                    
                actions = tokens[1:group_idx]
                agents = tokens[group_idx+1:]
                
                # Add action nodes
                prev_node = None
                for token in actions:
                    node_text = token
                    node_type = "action"
                    
                    # Handle negated actions
                    if token.startswith('not '):
                        node_text = token[4:]  # Remove 'not ' prefix
                        node_type = "impossible_action"
                    
                    if node_text not in nodes:
                        node = GraphNode(node_text, node_type)
                        scene.addItem(node)
                        nodes[node_text] = node
                    
                    # Connect sequential actions
                    if prev_node:
                        edge = GraphEdge(prev_node, nodes[node_text], "next")
                        scene.addItem(edge)
                    prev_node = nodes[node_text]
                
                # Add agent nodes
                for token in agents:
                    node_text = token
                    node_type = "condition"
                    
                    # Handle negated agents
                    if token.startswith('not '):
                        node_text = token[4:]  # Remove 'not ' prefix
                        node_type = "impossible_condition"
                    
                    if node_text not in nodes:
                        node = GraphNode(node_text, node_type)
                        scene.addItem(node)
                        nodes[node_text] = node
                        # Connect agent to all actions
                        for action in actions:
                            action_text = action[4:] if action.startswith('not ') else action
                            edge = GraphEdge(nodes[node_text], nodes[action_text], "can perform")
                            scene.addItem(edge)
        
        # Arrange nodes in a grid
        self.arrange_nodes(scene)
    
    def update_result_graph(self):
        """Convert result text to graph"""
        scene = self.result_graph.scene()
        scene.clear()
        
        text = self.query_result.toPlainText()
        if not text:
            return
            
        # Create result node
        result_parts = text.split('\n')
        if result_parts:
            # Create node for the result
            result_text = result_parts[0].replace('Result: ', '')
            result_node = GraphNode(result_text, "effect")
            scene.addItem(result_node)
            
            # If there's an explanation, add it as a condition node
            if len(result_parts) > 1:
                explanation = result_parts[1].replace('Explanation: ', '')
                explanation_node = GraphNode(explanation, "condition")
                scene.addItem(explanation_node)
                
                # Connect explanation to result
                edge = GraphEdge(explanation_node, result_node, "explains")
                scene.addItem(edge)
        
        # Arrange nodes
        self.arrange_nodes(scene)

    def apply_domain(self):
        """Apply the domain definition"""
        try:
            domain_text = self.domain_editor.toPlainText()
            print("Applying domain definition:")
            print(domain_text)
            
            # Update visual query builder with domain elements
            self.visual_query_tab.update_domain_elements(domain_text)
            
            # Send domain text directly to semantics engine
            self.semantics.process_domain_definition(domain_text)
            
            # Update graph view if active
            if self.graph_mode_radio.isChecked():
                self.domain_graph.scene().clear()
                self.update_domain_graph()
            
            QMessageBox.information(self, "Success", "Domain definition applied successfully!")
            
        except Exception as e:
            print(f"Error in domain definition: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error in domain definition: {str(e)}")
    
    def execute_query(self):
        """Execute the current query"""
        try:
            query_text = self.query_editor.toPlainText()
            print("Executing query:")
            print(query_text)
            
            # Pre-process queries
            processed_queries = []
            for line in query_text.split('\n'):
                if not line.strip():
                    continue
                
                parts = line.split()
                if not parts:
                    continue
                
                if parts[0] == "always":
                    if parts[1] == "executable":
                        # Transform "always executable X" to "executable X"
                        processed_queries.append(" ".join(parts[1:]))
                elif parts[0] == "sometimes":
                    if "accessible" in line:
                        # Transform "sometimes accessible X from Y in Z" to "accessible X from Y in Z"
                        # Remove "sometimes" and keep the rest
                        processed_queries.append(" ".join(parts[1:]))
                    else:
                        processed_queries.append(line)
                elif parts[0] in ["executable", "accessible", "realisable", "active"]:
                    processed_queries.append(line)
                else:
                    processed_queries.append(line)
            
            # Process each query separately
            results = []
            explanations = []
            
            for query in processed_queries:
                if not query.strip():
                    continue
                    
                print(f"Processing query: {query}")
                try:
                    result, explanation = self.semantics.process_query(query)
                    results.append(result)
                    explanations.append(explanation)
                except Exception as e:
                    print(f"Error processing individual query: {str(e)}")
                    results.append(False)
                    explanations.append(f"Error: {str(e)}")
            
            # Combine results
            if results:
                combined_result = "Results:\n"
                for i, (result, explanation) in enumerate(zip(results, explanations)):
                    original_query = query_text.split('\n')[i].strip()
                    combined_result += f"Query: {original_query}\n"
                    combined_result += f"Result: {result}\n"
                    combined_result += f"Explanation: {explanation}\n\n"
                
                self.query_result.setText(combined_result)
                
                # Update graph view if active
                if self.graph_mode_radio.isChecked():
                    self.query_graph.scene().clear()
                    self.update_query_graph()
                    self.result_graph.scene().clear()
                    self.update_result_graph()
            
        except Exception as e:
            print(f"Error in query: {str(e)}")
            self.query_result.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error in query: {str(e)}")
    
    def load_problem(self, problem_name):
        """Load a problem from the database"""
        try:
            from db.database import DatabaseManager
            db = DatabaseManager()
            problem = db.get_problem_by_name(problem_name)
            if problem:
                print(f"Loading problem: {problem_name}")
                print("Domain definition:")
                print(problem['domain_definition'])
                print("Example queries:")
                print(problem['example_queries'])
                self.domain_editor.setText(problem['domain_definition'])
                self.query_editor.setText(problem['example_queries'])
                # Automatically apply the domain definition
                self.apply_domain()
            else:
                print(f"Problem not found: {problem_name}")
        except Exception as e:
            print(f"Error loading problem: {str(e)}")
            QMessageBox.warning(self, "Warning", f"Could not load problem: {str(e)}")
    
    def setup_dark_mode(self):
        """Set up dark mode styling"""
        # Set fusion style for better dark mode support
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        
        # Create dark palette
        dark_palette = QPalette()
        
        # Dark mode colors
        dark_color = QColor(45, 45, 45)
        disabled_color = QColor(127, 127, 127)
        text_color = QColor(255, 255, 255)
        highlight_color = QColor(42, 130, 218)
        dark_text = QColor(210, 210, 210)
        
        # Set colors for different color roles
        dark_palette.setColor(QPalette.Window, dark_color)
        dark_palette.setColor(QPalette.WindowText, text_color)
        dark_palette.setColor(QPalette.Base, QColor(18, 18, 18))
        dark_palette.setColor(QPalette.AlternateBase, dark_color)
        dark_palette.setColor(QPalette.ToolTipBase, text_color)
        dark_palette.setColor(QPalette.ToolTipText, text_color)
        dark_palette.setColor(QPalette.Text, text_color)
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, disabled_color)
        dark_palette.setColor(QPalette.Button, dark_color)
        dark_palette.setColor(QPalette.ButtonText, text_color)
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_color)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, highlight_color)
        dark_palette.setColor(QPalette.Highlight, highlight_color)
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        # Apply the palette
        QApplication.setPalette(dark_palette)
        
        # Set stylesheet for custom styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d2d;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-family: 'SF Pro Text', system-ui;
                font-size: 13px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-family: 'SF Pro Text', system-ui;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
            QComboBox {
                background-color: #1e1e1e;
                color: white;
                padding: 5px;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                font-family: -apple-system, 'SF Pro Text';
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
            }
            QMenuBar {
                background-color: #2d2d2d;
                color: white;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 10px;
            }
            QMenuBar::item:selected {
                background-color: #3d3d3d;
                border-radius: 4px;
            }
            QMenu {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 4px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3d3d3d;
                margin: 4px 0px;
            }
        """)
    
    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New")
        file_menu.addAction("Open...")
        file_menu.addAction("Save")
        file_menu.addAction("Save As...")
        file_menu.addSeparator()
        file_menu.addAction("Exit")
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Undo")
        edit_menu.addAction("Redo")
        edit_menu.addSeparator()
        edit_menu.addAction("Cut")
        edit_menu.addAction("Copy")
        edit_menu.addAction("Paste")
        
        # View menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction("State Diagram")
        view_menu.addAction("Debug Log")
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("Documentation")
        help_menu.addAction("About")

    def execute_query_text(self, query_text):
        """Execute a query from text (used by visual query builder)"""
        self.query_editor.setText(query_text)
        self.execute_query()

if __name__ == '__main__':
    # Enable High DPI scaling
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 