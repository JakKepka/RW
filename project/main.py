import sys
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
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor
from engine.semantics import ActionSemantics
from engine.executor import State

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
        
        # Add components to left panel
        left_layout.addWidget(problem_label)
        left_layout.addWidget(self.problem_combo)
        left_layout.addStretch()
        
        # Create right panel (main content)
        right_panel = QTabWidget()
        
        # Domain Editor Tab
        domain_tab = QWidget()
        domain_layout = QVBoxLayout(domain_tab)
        self.domain_editor = QTextEdit()
        
        # Add Apply Domain button
        apply_domain_btn = QPushButton("Apply Domain Definition")
        apply_domain_btn.clicked.connect(self.apply_domain)
        
        domain_layout.addWidget(QLabel("Domain Definition:"))
        domain_layout.addWidget(self.domain_editor)
        domain_layout.addWidget(apply_domain_btn)
        
        # Query Tab
        query_tab = QWidget()
        query_layout = QVBoxLayout(query_tab)
        self.query_editor = QTextEdit()
        self.query_result = QTextEdit()
        self.query_result.setReadOnly(True)
        
        # Add Execute Query button
        execute_query_btn = QPushButton("Execute Query")
        execute_query_btn.clicked.connect(self.execute_query)
        
        query_layout.addWidget(QLabel("Query:"))
        query_layout.addWidget(self.query_editor)
        query_layout.addWidget(execute_query_btn)
        query_layout.addWidget(QLabel("Result:"))
        query_layout.addWidget(self.query_result)
        
        # Add tabs
        right_panel.addTab(domain_tab, "Domain Editor")
        right_panel.addTab(query_tab, "Query Analysis")
        
        # Add panels to main layout
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 4)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Load initial problem
        self.load_problem(self.problem_combo.currentText())
    
    def apply_domain(self):
        """Apply the domain definition"""
        try:
            domain_text = self.domain_editor.toPlainText()
            print("Applying domain definition:")
            print(domain_text)
            self.semantics.process_domain_definition(domain_text)
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
            result, explanation = self.semantics.process_query(query_text)
            print(f"Query result: {result}")
            print(f"Explanation: {explanation}")
            self.query_result.setText(f"Result: {'True' if result else 'False'}\nExplanation: {explanation}")
        except Exception as e:
            print(f"Error in query: {str(e)}")
            self.query_result.setText(f"Error: {str(e)}")
    
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
                font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-family: -apple-system, 'SF Pro Text';
                font-size: 13px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-family: -apple-system, 'SF Pro Text';
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Enable High DPI scaling
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 