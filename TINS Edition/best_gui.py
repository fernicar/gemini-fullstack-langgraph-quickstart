import sys
import os
import shutil
from pathlib import Path

# Import Qt Components
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QTabWidget, QSplitter, QMenuBar, QToolBar, QFileDialog,
    QMessageBox, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QSizePolicy,
    QDialog, QDialogButtonBox, QFormLayout, QStyleFactory, QStatusBar, QGroupBox,
    QRadioButton, QCheckBox, QToolButton, QCommandLinkButton, QDateTimeEdit,
    QSlider, QScrollBar, QDial, QProgressBar, QGridLayout, QMenu, QInputDialog
)
from PySide6.QtGui import QAction, QKeySequence, QTextCursor, QShortcut
from PySide6.QtCore import Qt, Slot, QSize, QSettings, QFile, QTextStream, QDateTime, QTimer, QObject

# --- Constants ---
APP_NAME = "Cool GUI Example"
APP_VERSION = "1.0"
SETTINGS_ORG = "ExampleOrg"
SETTINGS_APP = "CoolGUIExample"
DEFAULT_WINDOW_SIZE = QSize(1200, 800)
DEFAULT_FONT_SIZE = 11
RESOURCES_DIR = Path("resources")
DEFAULT_THEME_PATH = RESOURCES_DIR / "default_theme.qss"
STYLE_THEMES = ['windows11', 'windowsvista', 'Windows', 'Fusion']
STYLE_SELECTED_THEME = STYLE_THEMES[3]  # Fusion style
COLOR_SCHEMES = ['Auto', 'Light', 'Dark']
DEFAULT_COLOR_SCHEME = COLOR_SCHEMES[0]  # Auto by default

# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)

        # Create resources directory if it doesn't exist
        if not RESOURCES_DIR.exists():
            RESOURCES_DIR.mkdir(parents=True)

        # Create empty default theme file if it doesn't exist
        if not DEFAULT_THEME_PATH.exists():
            with open(DEFAULT_THEME_PATH, 'w', encoding='utf-8') as file:
                file.write('')  # Write empty content

        self._init_ui()
        self._load_settings()
        self._apply_current_theme()
        self.app = QApplication.instance()

    def _init_ui(self):
        """Creates the user interface elements."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(100, 100, DEFAULT_WINDOW_SIZE.width(), DEFAULT_WINDOW_SIZE.height())

        # --- Central Widget & Main Layout ---
        central_widget = QWidget() # QWidget central widget
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) # QVBoxLayout for main layout

        # --- Menu Bar ---
        menu_bar = self.menuBar() # QMenuBar for menu bar

        # File Menu
        file_menu = menu_bar.addMenu("&File") # QMenu for file menu

        exit_action = QAction("E&xit", self) # QAction for exit
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menu_bar.addMenu("&View") # QMenu for view menu

        # Color Scheme Submenu
        color_scheme_menu = view_menu.addMenu("&Color Scheme") # QMenu for color scheme submenu

        # Add color scheme options
        self.color_scheme_actions = []

        # Auto color scheme action
        auto_scheme_action = QAction("Auto", self) # QAction for auto color scheme
        auto_scheme_action.setCheckable(True)
        auto_scheme_action.setData(0)  # Index for Auto in Qt.ColorScheme
        auto_scheme_action.triggered.connect(self._on_color_scheme_selected)
        color_scheme_menu.addAction(auto_scheme_action)
        self.color_scheme_actions.append(auto_scheme_action)

        # Light color scheme action
        light_scheme_action = QAction("Light", self) # QAction for light color scheme
        light_scheme_action.setCheckable(True)
        light_scheme_action.setData(1)  # Index for Light in Qt.ColorScheme
        light_scheme_action.triggered.connect(self._on_color_scheme_selected)
        color_scheme_menu.addAction(light_scheme_action)
        self.color_scheme_actions.append(light_scheme_action)

        # Dark color scheme action
        dark_scheme_action = QAction("Dark", self) # QAction for dark color scheme
        dark_scheme_action.setCheckable(True)
        dark_scheme_action.setData(2)  # Index for Dark in Qt.ColorScheme
        dark_scheme_action.triggered.connect(self._on_color_scheme_selected)
        color_scheme_menu.addAction(dark_scheme_action)
        self.color_scheme_actions.append(dark_scheme_action)

        # Theme Submenu
        theme_menu = view_menu.addMenu("&Theme") # QMenu for theme submenu

        # Add theme options
        self.theme_actions = []

        # Load Custom QSS action
        load_qss_action = QAction("Load Custom QSS...", self) # QAction for loading custom QSS
        load_qss_action.triggered.connect(self._load_custom_qss)
        theme_menu.addAction(load_qss_action)

        # Add separator
        theme_menu.addSeparator()

        # Default Fusion Style action
        default_fusion_action = QAction("Default Fusion Style", self) # QAction for default Fusion style
        default_fusion_action.triggered.connect(self._apply_default_fusion_style)
        theme_menu.addAction(default_fusion_action)

        # --- Main Horizontal Splitter (Top/Bottom Panes) ---
        main_splitter_h = QSplitter(Qt.Orientation.Vertical) # QSplitter for main horizontal split
        main_layout.addWidget(main_splitter_h, 1) # Make splitter stretch

        # --- Example Widgets Section ---
        example_widgets_layout = QHBoxLayout()
        main_layout.addLayout(example_widgets_layout)

        # Create Buttons Group Box
        buttons_group_box = self._create_buttons_group_box()
        example_widgets_layout.addWidget(buttons_group_box)

        # Create Input Widgets Group Box
        input_widgets_group_box = self._create_input_widgets_group_box()
        example_widgets_layout.addWidget(input_widgets_group_box)

        # Create Progress Bar
        self.progress_bar = self._create_progress_bar()
        main_layout.addWidget(self.progress_bar)

        # --- Top Pane (Display Area) ---
        top_pane_widget = QWidget() # QWidget for top pane
        top_pane_layout = QHBoxLayout(top_pane_widget) # QHBoxLayout for top pane
        top_pane_layout.setContentsMargins(0, 0, 0, 0)
        display_splitter_v = QSplitter(Qt.Orientation.Horizontal) # QSplitter for vertical display split
        top_pane_layout.addWidget(display_splitter_v)
        main_splitter_h.addWidget(top_pane_widget)

        # --- Left Display (Story) ---
        left_display_widget = QWidget() # QWidget for left display
        left_display_layout = QVBoxLayout(left_display_widget) # QVBoxLayout for left display
        story_label = QLabel("Content Display:") # QLabel for story label
        left_display_layout.addWidget(story_label)
        self.story_display = QTextEdit() # QTextEdit for story display
        self.story_display.setReadOnly(True)
        self.story_display.setPlaceholderText("Content will be displayed here")
        left_display_layout.addWidget(self.story_display)
        display_splitter_v.addWidget(left_display_widget)

        # --- Right Display (Monitor Tabs) ---
        right_display_widget = QWidget() # QWidget for right display
        right_display_layout = QVBoxLayout(right_display_widget) # QVBoxLayout for right display
        self.monitor_tabs = QTabWidget() # QTabWidget for monitor tabs
        right_display_layout.addWidget(self.monitor_tabs)
        display_splitter_v.addWidget(right_display_widget)

        # Info Tab
        info_tab = QWidget() # QWidget for info tab
        info_layout = QVBoxLayout(info_tab) # QVBoxLayout for info tab
        self.info_display = QTextEdit() # QTextEdit for info display
        self.info_display.setReadOnly(True)
        self.info_display.setPlaceholderText("Information will be displayed here")
        info_layout.addWidget(self.info_display)
        self.monitor_tabs.addTab(info_tab, "Info")

        # Settings Tab
        settings_tab = QWidget() # QWidget for settings tab
        settings_layout = QVBoxLayout(settings_tab) # QVBoxLayout for settings tab
        self.settings_display = QTextEdit() # QTextEdit for settings display
        self.settings_display.setReadOnly(True)
        self.settings_display.setPlaceholderText("Settings information will be displayed here")
        settings_layout.addWidget(self.settings_display)
        self.monitor_tabs.addTab(settings_tab, "Settings")

        # --- Bottom Pane (Input Area Tabs) ---
        bottom_pane_widget = QWidget() # QWidget for bottom pane
        bottom_pane_layout = QVBoxLayout(bottom_pane_widget) # QVBoxLayout for bottom pane
        bottom_pane_layout.setContentsMargins(0, 5, 0, 0) # Add some top margin
        self.input_tabs = QTabWidget() # QTabWidget for input tabs
        bottom_pane_layout.addWidget(self.input_tabs)
        main_splitter_h.addWidget(bottom_pane_widget)

        # Main Input Tab
        main_input_tab = QWidget() # QWidget for main input tab
        main_input_layout = QVBoxLayout(main_input_tab) # QVBoxLayout for main input tab
        self.main_input = QTextEdit() # QTextEdit for main input
        self.main_input.setPlaceholderText("Type your input here...")
        main_input_layout.addWidget(self.main_input)
        main_input_buttons_layout = QHBoxLayout() # QHBoxLayout for main input buttons
        send_button_main = QPushButton("Send") # QPushButton for send
        send_button_main.clicked.connect(self._handle_send)
        main_input_buttons_layout.addWidget(send_button_main)
        main_input_layout.addLayout(main_input_buttons_layout)
        self.input_tabs.addTab(main_input_tab, "Main Input")

        # Secondary Input Tab
        secondary_input_tab = QWidget() # QWidget for secondary input tab
        secondary_input_layout = QVBoxLayout(secondary_input_tab) # QVBoxLayout for secondary input tab
        self.secondary_input = QTextEdit() # QTextEdit for secondary input
        self.secondary_input.setPlaceholderText("Type your secondary input here...")
        secondary_input_layout.addWidget(self.secondary_input)
        secondary_input_buttons_layout = QHBoxLayout() # QHBoxLayout for secondary input buttons
        send_button_secondary = QPushButton("Send") # QPushButton for send
        send_button_secondary.clicked.connect(self._handle_send)
        secondary_input_buttons_layout.addWidget(send_button_secondary)
        secondary_input_layout.addLayout(secondary_input_buttons_layout)
        self.input_tabs.addTab(secondary_input_tab, "Secondary Input")

        # --- Initial Splitter Sizes ---
        main_splitter_h.setSizes([int(self.height() * 0.65), int(self.height() * 0.35)])
        display_splitter_v.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])

        # --- Bottom Toolbar ---
        toolbar = QToolBar("Main Toolbar") # QToolBar for toolbar
        toolbar.setIconSize(QSize(16, 16)) # Smaller icons if used
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, toolbar)

        # Style Selector (ComboBox)
        toolbar.addWidget(QLabel(" Style: ")) # QLabel for style
        self.style_selector = QComboBox() # QComboBox for style selection
        self.style_selector.addItems(STYLE_THEMES)
        self.style_selector.setCurrentText(STYLE_SELECTED_THEME)  # Select Fusion by default
        self.style_selector.setMinimumWidth(150)
        self.style_selector.currentTextChanged.connect(self._on_style_changed)
        toolbar.addWidget(self.style_selector)

        # Temperature (DoubleSpinBox)
        toolbar.addWidget(QLabel(" Temp: ")) # QLabel for temperature
        self.temp_spinbox = QDoubleSpinBox() # QDoubleSpinBox for temperature
        self.temp_spinbox.setRange(0.0, 2.0)
        self.temp_spinbox.setSingleStep(0.1)
        self.temp_spinbox.setValue(0.7) # Default temp
        toolbar.addWidget(self.temp_spinbox)

        # Max Tokens (SpinBox)
        toolbar.addWidget(QLabel(" Max Tokens: ")) # QLabel for max tokens
        self.max_tokens_spinbox = QSpinBox() # QSpinBox for max tokens
        self.max_tokens_spinbox.setRange(50, 8192)
        self.max_tokens_spinbox.setSingleStep(10)
        self.max_tokens_spinbox.setValue(1024) # Default max tokens
        toolbar.addWidget(self.max_tokens_spinbox)

        toolbar.addSeparator()

        # XML Tag Input (LineEdit)
        toolbar.addWidget(QLabel(" Tag: ")) # QLabel for XML tag
        self.xml_tag_input = QLineEdit() # QLineEdit for XML tag input
        self.xml_tag_input.setPlaceholderText("e.g., <instruction>")
        self.xml_tag_input.setFixedWidth(120)
        toolbar.addWidget(self.xml_tag_input)

        toolbar.addSeparator()

        # Font Size (SpinBox)
        toolbar.addWidget(QLabel(" Font Size: ")) # QLabel for font size
        self.font_size_spinbox = QSpinBox() # QSpinBox for font size
        self.font_size_spinbox.setRange(8, 24)
        self.font_size_spinbox.setValue(DEFAULT_FONT_SIZE)
        self.font_size_spinbox.valueChanged.connect(self._update_font_size)
        toolbar.addWidget(self.font_size_spinbox)

        # Theme Toggle Button (QPushButton with checkable property)
        self.theme_button = QPushButton("Dark Mode") # QPushButton for theme toggle
        self.theme_button.setCheckable(True)
        self.theme_button.toggled.connect(self._toggle_color_scheme)
        toolbar.addWidget(self.theme_button)

        toolbar.addSeparator()

        # System Prompt Selector (ComboBox)
        toolbar.addWidget(QLabel(" Sys Prompt: ")) # QLabel for system prompt
        self.system_prompt_selector = QComboBox() # QComboBox for system prompt selection
        self.system_prompt_selector.addItems(["Default", "Creative", "Technical"])
        self.system_prompt_selector.setMinimumWidth(150)
        toolbar.addWidget(self.system_prompt_selector)

        # Send Button (Main Action) (QPushButton)
        self.send_button = QPushButton("Send") # QPushButton for send
        self.send_button.setToolTip("Send input based on active tab")
        self.send_button.clicked.connect(self._handle_send)
        toolbar.addWidget(self.send_button)

        # --- Status Bar ---
        self.status_bar = QStatusBar() # QStatusBar for status bar
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Add sample content to demonstrate the UI
        self._add_sample_content()

        # Print available styles
        print(f"Available styles: {QStyleFactory.keys()}")

    def _add_sample_content(self):
        """Adds sample content to the display area."""
        sample_text = """# Cool GUI Example

This is a demonstration of a cool GUI implementation using PySide6.

## Features:
- Color Scheme selection (Auto, Light, Dark) via View > Color Scheme menu
- Toggle between light and dark modes with the Dark Mode button
- Load custom QSS themes (experimental feature)
- Style selection via the Style dropdown
- Default Fusion style option in View > Theme menu
- Adjustable font size
- Tab-based input area
- Splitter for resizable panels
- Various example widgets (buttons, input fields, progress bar)

## How to Use:
1. Try the Auto/Light/Dark options in the View > Color Scheme menu
2. Toggle between Light/Dark modes using the button in the toolbar
3. Try different Qt styles from the Style dropdown in the toolbar
4. Experiment with custom themes via View > Theme > Load Custom QSS (experimental)
5. Select "Default Fusion Style" from the View > Theme menu to reset
6. Experiment with the example widgets below

Note: The Auto/Light/Dark color schemes are the recommended way to handle theming. Custom QSS themes are experimental and may not work perfectly with all styles.
"""
        self.story_display.setMarkdown(sample_text)

        info_text = """# Information Panel

This panel displays information about the application.

## Widget Classes Used:
- QMainWindow: Main application window
- QWidget: Container widgets
- QVBoxLayout/QHBoxLayout: Layout managers
- QSplitter: Resizable panel dividers
- QTabWidget: Tab containers
- QTextEdit: Text editing/display areas
- QPushButton: Action buttons
- QLabel: Text labels
- QSpinBox: Numeric input for font size
- QToolBar: Toolbar container
- QStatusBar: Status information
- QAction: Menu actions
- QGroupBox: Grouped widget container
- QRadioButton: Exclusive selection button
- QCheckBox: Checkable option button
- QToolButton: Compact button with menu support
- QCommandLinkButton: Vista-style link button
- QDateTimeEdit: Date and time editor
- QSlider: Sliding value selector
- QScrollBar: Scrolling control
- QDial: Rotary value control
- QProgressBar: Progress indicator
"""
        self.info_display.setMarkdown(info_text)

        settings_text = """# Theme and Style Settings

## Color Schemes (Recommended)
The application supports system color schemes via the View > Color Scheme menu:
- Auto: Uses the system default (light or dark based on OS settings)
- Light: Forces light mode
- Dark: Forces dark mode

The Dark Mode toggle button in the toolbar provides a quick way to switch between Light and Dark modes.

## Custom Themes (Experimental)
The application supports custom themes via QSS (Qt Style Sheets) as an experimental feature.
You can load custom QSS files via View > Theme > Load Custom QSS.
The theme files are stored in the 'resources' directory with names based on what you provide.

Note: Custom QSS themes may conflict with the system color schemes and might not work perfectly with all styles.

## Styles
You can select different Qt styles from the Style dropdown in the toolbar.
The application uses the Fusion style by default, which provides a consistent look across platforms.

## Default Fusion Style
Select "Default Fusion Style" from the View > Theme menu to reset to the default Fusion style with Auto color scheme.
This is useful if you want to clear any custom themes and return to the default appearance.
"""
        self.settings_display.setMarkdown(settings_text)

    @Slot()
    def _handle_send(self):
        """Handles the send button click."""
        active_tab = self.input_tabs.currentWidget()
        if active_tab == self.input_tabs.widget(0):  # Main Input tab
            input_text = self.main_input.toPlainText()
            if input_text:
                self.story_display.append(f"\n\n**User Input:**\n{input_text}")
                self.main_input.clear()
                self.status_bar.showMessage("Message sent", 3000)
        elif active_tab == self.input_tabs.widget(1):  # Secondary Input tab
            input_text = self.secondary_input.toPlainText()
            if input_text:
                self.story_display.append(f"\n\n**Secondary Input:**\n{input_text}")
                self.secondary_input.clear()
                self.status_bar.showMessage("Secondary message sent", 3000)

    @Slot(int)
    def _update_font_size(self, size: int):
        """Applies the selected font size to relevant text areas."""
        font = self.font() # Get default app font
        font.setPointSize(size)

        widgets_to_update = [
            self.story_display,      # QTextEdit for main content display
            self.info_display,       # QTextEdit for info tab
            self.settings_display,   # QTextEdit for settings tab
            self.main_input,         # QTextEdit for main input
            self.secondary_input     # QTextEdit for secondary input
        ]

        for widget in widgets_to_update:
            widget.setFont(font)

        self.settings.setValue("fontSize", size) # Save setting

    @Slot(bool)
    def _toggle_color_scheme(self, checked: bool):
        """Toggles between light and dark color schemes."""
        # app = QApplication.instance()

        # First set style for consistent look
        app.setStyle(QStyleFactory.create(STYLE_SELECTED_THEME))

        # Make sure the style selector shows the current style
        self.style_selector.setCurrentText(STYLE_SELECTED_THEME)

        # Clear any custom theme by emptying default_theme.qss
        with open(DEFAULT_THEME_PATH, 'w', encoding='utf-8') as file:
            file.write('')  # Write empty content

        # Reset stylesheet
        app.setStyleSheet('')

        if checked: # Dark mode
            # Apply dark color scheme
            app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
            scheme_index = 2  # Dark

            # Update settings and UI
            self.settings.setValue("colorScheme", scheme_index)
            self.theme_button.setText("Light Mode")
        else: # Light mode
            # Apply light color scheme
            app.styleHints().setColorScheme(Qt.ColorScheme.Light)
            scheme_index = 1  # Light

            # Update settings and UI
            self.settings.setValue("colorScheme", scheme_index)
            self.theme_button.setText("Dark Mode")

        # Update color scheme action checkboxes
        for action in self.color_scheme_actions:
            action.setChecked(action.data() == scheme_index)

        # Uncheck theme actions since we're using color scheme
        for action in self.theme_actions:
            action.setChecked(False)

        # Update status bar
        scheme_name = COLOR_SCHEMES[scheme_index]
        self.status_bar.showMessage(f"{scheme_name} color scheme applied", 3000)


    def _apply_theme_from_file(self, theme_path: Path):
        """Applies a theme from a QSS file."""
        if not theme_path.exists():
            QMessageBox.warning(self, "Theme Error", f"Theme file not found: {theme_path}")
            return False

        try:
            # Read the QSS file content
            with open(theme_path, 'r', encoding='utf-8') as file:
                qss = file.read()

            # Reset to style first
            # app = QApplication.instance()
            app.setStyle(QStyleFactory.create(STYLE_SELECTED_THEME))

            # Apply the stylesheet to the application instance
            app.setStyleSheet(qss)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Theme Error", f"Error applying theme: {str(e)}")
            return False

    @Slot(bool)
    def _on_theme_selected(self, checked: bool):
        """Handles theme selection from the menu."""
        action = self.sender()
        if not isinstance(action, QAction) or not checked: return

        theme_type = action.data()
        if theme_type:
            # Uncheck all other theme actions
            for other_action in self.theme_actions:
                if other_action != action:
                    other_action.setChecked(False)

            # Uncheck color scheme actions since we're using a custom theme
            for action in self.color_scheme_actions:
                action.setChecked(False)

            # Apply the selected theme directly
            # app = QApplication.instance()

            # First set style for consistent look
            app.setStyle(QStyleFactory.create(STYLE_SELECTED_THEME))

            # Apply the theme based on type
            if theme_type == "dark":
                # Apply dark theme via color scheme
                app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
                self.theme_button.setText("Light Mode")
                self.theme_button.setChecked(True)
                self.settings.setValue("colorScheme", 2)  # Dark
            else:  # light theme
                # Apply light theme via color scheme
                app.styleHints().setColorScheme(Qt.ColorScheme.Light)
                self.theme_button.setText("Dark Mode")
                self.theme_button.setChecked(False)
                self.settings.setValue("colorScheme", 1)  # Light

    @Slot(str)
    def _on_style_changed(self, style_name: str):
        """Handles style selection from the dropdown."""
        try:
            # Apply the selected style
            # app = QApplication.instance()
            app.setStyle(QStyleFactory.create(style_name))

            # Update the global style theme
            global STYLE_SELECTED_THEME
            STYLE_SELECTED_THEME = style_name

            # Get current color scheme
            color_scheme = self.settings.value("colorScheme", 0, type=int)  # 0 = Auto by default

            # Reapply the color scheme to ensure it works with the new style
            app.styleHints().setColorScheme(Qt.ColorScheme(color_scheme))

            self.status_bar.showMessage(f"{style_name} style applied", 3000)

        except Exception as e:
            QMessageBox.warning(self, "Style Error", f"Error applying {style_name} style: {str(e)}")

    @Slot()
    def _apply_default_fusion_style(self):
        """Applies the default Fusion style without any QSS customization."""
        try:
            # Clear any custom theme setting
            self.settings.setValue("customTheme", "")

            # Reset to Fusion style without any stylesheet
            # app = QApplication.instance()
            app.setStyle(QStyleFactory.create(STYLE_SELECTED_THEME))
            app.setStyleSheet('')  # Clear any stylesheet

            # Update UI to reflect we're using default style
            self.status_bar.showMessage("Default Fusion style applied", 3000)

            # Uncheck theme actions since we're not using any custom theme
            for action in self.theme_actions:
                action.setChecked(False)

            # Make sure the style selector shows the current style
            self.style_selector.setCurrentText(STYLE_SELECTED_THEME)

            # Set Auto color scheme
            self._on_color_scheme_selected(True, force_index=0)

        except Exception as e:
            QMessageBox.warning(self, "Style Error", f"Error applying default style: {str(e)}")

    @Slot(bool)
    def _on_color_scheme_selected(self, checked: bool, force_index=None):
        """Handles color scheme selection from the menu."""
        if not checked and force_index is None:
            return

        # Get the selected scheme index
        if force_index is not None:
            scheme_index = force_index
        else:
            action = self.sender()
            if not isinstance(action, QAction): return
            scheme_index = action.data()

        # Uncheck all other color scheme actions
        for action in self.color_scheme_actions:
            action.setChecked(action.data() == scheme_index)

        # Apply the selected color scheme
        # app = QApplication.instance()
        app.styleHints().setColorScheme(Qt.ColorScheme(scheme_index))

        # Reset stylesheet but keep the style
        app.setStyleSheet('')

        # Clear any custom theme setting
        self.settings.setValue("customTheme", "")

        # Update settings
        self.settings.setValue("colorScheme", scheme_index)

        # Update UI
        scheme_name = COLOR_SCHEMES[scheme_index]
        self.status_bar.showMessage(f"{scheme_name} color scheme applied", 3000)

        # Uncheck theme actions since we're using color scheme
        for action in self.theme_actions:
            action.setChecked(False)

        # Update theme button state based on color scheme
        if scheme_index == 2:  # Dark
            self.theme_button.setChecked(True)
            self.theme_button.setText("Light Mode")
        else:  # Light or Auto
            self.theme_button.setChecked(False)
            self.theme_button.setText("Dark Mode")

    @Slot()
    def _load_custom_qss(self):
        """Opens a file dialog to load a custom QSS file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Custom QSS Theme",
            str(RESOURCES_DIR),
            "QSS Files (*.qss);;All Files (*)"
        )

        if not file_path:
            return

        # Ask for a theme name
        theme_name, ok = QInputDialog.getText(
            self,
            "Theme Name",
            "Enter a name for this theme (e.g., 'Blue Accent'):"
        )

        if not ok or not theme_name:
            theme_name = "custom"

        # Create a sanitized filename
        safe_name = "".join(c if c.isalnum() or c in "_- " else "_" for c in theme_name).lower()
        safe_name = safe_name.replace(" ", "_")

        # Create the new theme file path
        new_theme_path = RESOURCES_DIR / f"{safe_name}_theme.qss"

        try:
            # Copy the selected QSS file to the new theme file
            shutil.copy(file_path, new_theme_path)

            # Also copy to default_theme.qss
            shutil.copy(file_path, DEFAULT_THEME_PATH)

            # Apply the theme
            success = self._apply_theme_from_file(new_theme_path)

            if success:
                # Store the custom theme name in settings
                self.settings.setValue("customTheme", safe_name)

                # Uncheck color scheme actions
                for action in self.color_scheme_actions:
                    action.setChecked(False)

                # Update UI
                self.status_bar.showMessage(f"Custom theme '{theme_name}' applied", 3000)

                # Add to theme menu if it doesn't exist
                theme_exists = False
                for action in self.theme_actions:
                    if action.text() == theme_name:
                        action.setChecked(True)
                        theme_exists = True
                        break

                if not theme_exists:
                    # Create a new action for this theme
                    new_theme_action = QAction(theme_name, self)
                    new_theme_action.setCheckable(True)
                    new_theme_action.setData(safe_name)
                    new_theme_action.setChecked(True)
                    new_theme_action.triggered.connect(self._on_custom_theme_selected)

                    # Add it to the theme menu before the separators
                    menu = self.theme_actions[0].parentWidget()
                    if menu:
                        menu.insertAction(self.theme_actions[-1], new_theme_action)
                        self.theme_actions.append(new_theme_action)
        except Exception as e:
            QMessageBox.warning(self, "Theme Error", f"Error loading custom theme: {str(e)}")

    @Slot(bool)
    def _on_custom_theme_selected(self, checked: bool):
        """Handles custom theme selection from the menu."""
        if not checked:
            return

        action = self.sender()
        if not isinstance(action, QAction): return

        theme_id = action.data()
        theme_path = RESOURCES_DIR / f"{theme_id}_theme.qss"

        if theme_path.exists():
            # Store the custom theme name in settings
            self.settings.setValue("customTheme", theme_id)

            # Apply the theme directly from the theme file
            self._apply_theme_from_file(theme_path)

            # Uncheck other theme actions
            for other_action in self.theme_actions:
                if other_action != action:
                    other_action.setChecked(False)

            # Uncheck color scheme actions
            for scheme_action in self.color_scheme_actions:
                scheme_action.setChecked(False)

            # Update UI
            self.status_bar.showMessage(f"Theme '{action.text()}' applied", 3000)
        else:
            QMessageBox.warning(self, "Theme Error", f"Theme file not found: {theme_path}")
            action.setChecked(False)
            # Clear the custom theme setting
            self.settings.setValue("customTheme", "")

    def _create_buttons_group_box(self):
        """Creates a group box with various button types."""
        group_box = QGroupBox("Buttons") # QGroupBox for buttons
        group_box.setObjectName("buttonsGroupBox")

        # Create buttons
        default_push_button = QPushButton("Default Push Button") # QPushButton for default
        default_push_button.setDefault(True)

        toggle_push_button = QPushButton("Toggle Push Button") # QPushButton for toggle
        toggle_push_button.setCheckable(True)
        toggle_push_button.setChecked(True)

        flat_push_button = QPushButton("Flat Push Button") # QPushButton for flat
        flat_push_button.setFlat(True)

        tool_button = QToolButton() # QToolButton
        tool_button.setText("Tool Button")

        menu_tool_button = QToolButton() # QToolButton for menu
        menu_tool_button.setText("Menu Button")
        tool_menu = QMenu(menu_tool_button) # QMenu for tool button
        menu_tool_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        tool_menu.addAction("Option")
        tool_menu.addSeparator()
        action = tool_menu.addAction("Checkable Option")
        action.setCheckable(True)
        menu_tool_button.setMenu(tool_menu)

        tool_layout = QHBoxLayout() # QHBoxLayout for tool buttons
        tool_layout.addWidget(tool_button)
        tool_layout.addWidget(menu_tool_button)

        command_link_button = QCommandLinkButton("Command Link Button") # QCommandLinkButton
        command_link_button.setDescription("Description")

        # Create radio buttons and checkbox
        radio_button1 = QRadioButton("Radio button 1") # QRadioButton
        radio_button2 = QRadioButton("Radio button 2") # QRadioButton
        radio_button3 = QRadioButton("Radio button 3") # QRadioButton
        radio_button1.setChecked(True)

        check_box = QCheckBox("Tri-state check box") # QCheckBox
        check_box.setTristate(True)
        check_box.setCheckState(Qt.CheckState.PartiallyChecked)

        # Layout for buttons
        button_layout = QVBoxLayout() # QVBoxLayout for buttons
        button_layout.addWidget(default_push_button)
        button_layout.addWidget(toggle_push_button)
        button_layout.addWidget(flat_push_button)
        button_layout.addLayout(tool_layout)
        button_layout.addWidget(command_link_button)
        button_layout.addStretch(1)

        # Layout for checkable widgets
        checkable_layout = QVBoxLayout() # QVBoxLayout for checkable widgets
        checkable_layout.addWidget(radio_button1)
        checkable_layout.addWidget(radio_button2)
        checkable_layout.addWidget(radio_button3)
        checkable_layout.addWidget(check_box)
        checkable_layout.addStretch(1)

        # Main layout
        main_layout = QHBoxLayout(group_box) # QHBoxLayout for main layout
        main_layout.addLayout(button_layout)
        main_layout.addLayout(checkable_layout)
        main_layout.addStretch()

        return group_box

    def _create_input_widgets_group_box(self):
        """Creates a group box with various input widgets."""
        group_box = QGroupBox("Simple Input Widgets") # QGroupBox for input widgets
        group_box.setObjectName("inputWidgetsGroupBox")
        group_box.setCheckable(True)
        group_box.setChecked(True)

        # Create input widgets
        line_edit = QLineEdit("s3cRe7") # QLineEdit
        line_edit.setClearButtonEnabled(True)
        line_edit.setEchoMode(QLineEdit.EchoMode.Password)

        spin_box = QSpinBox() # QSpinBox
        spin_box.setValue(50)

        date_time_edit = QDateTimeEdit() # QDateTimeEdit
        date_time_edit.setDateTime(QDateTime.currentDateTime())

        slider = QSlider() # QSlider
        slider.setOrientation(Qt.Orientation.Horizontal)
        slider.setValue(40)

        scroll_bar = QScrollBar() # QScrollBar
        scroll_bar.setOrientation(Qt.Orientation.Horizontal)
        scroll_bar.setValue(60)

        dial = QDial() # QDial
        dial.setValue(30)
        dial.setNotchesVisible(True)

        # Layout
        layout = QGridLayout(group_box) # QGridLayout for layout
        layout.addWidget(line_edit, 0, 0, 1, 2)
        layout.addWidget(spin_box, 1, 0, 1, 2)
        layout.addWidget(date_time_edit, 2, 0, 1, 2)
        layout.addWidget(slider, 3, 0)
        layout.addWidget(scroll_bar, 4, 0)
        layout.addWidget(dial, 3, 1, 2, 1)
        layout.setRowStretch(5, 1)

        return group_box

    def _create_progress_bar(self):
        """Creates a progress bar with a timer."""
        progress_bar = QProgressBar() # QProgressBar
        progress_bar.setObjectName("progressBar")
        progress_bar.setRange(0, 10000)
        progress_bar.setValue(0)

        # Create timer to advance the progress bar
        timer = QTimer(self) # QTimer
        timer.timeout.connect(self._advance_progress_bar)
        timer.start(100)

        return progress_bar

    @Slot()
    def _advance_progress_bar(self):
        """Advances the progress bar value."""
        current_value = self.progress_bar.value()
        max_value = self.progress_bar.maximum()
        self.progress_bar.setValue(current_value + (max_value - current_value) // 100)

    def _apply_current_theme(self):
        """Applies the current theme based on settings."""
        color_scheme = self.settings.value("colorScheme", 0, type=int)  # 0 = Auto by default

        # Make sure the style selector shows the current style
        self.style_selector.setCurrentText(STYLE_SELECTED_THEME)

        # Apply color scheme
        # app = QApplication.instance()
        app.styleHints().setColorScheme(Qt.ColorScheme(color_scheme))

        # Clear any stylesheet by default
        app.setStyleSheet('')

        # Ensure default_theme.qss exists but is empty
        if not RESOURCES_DIR.exists():
            RESOURCES_DIR.mkdir(parents=True)

        with open(DEFAULT_THEME_PATH, 'w', encoding='utf-8') as file:
            file.write('')  # Write empty content

        # Update color scheme actions
        for action in self.color_scheme_actions:
            action.setChecked(action.data() == color_scheme)

        # Update theme button state based on color scheme
        if color_scheme == 2:  # Dark
            self.theme_button.setChecked(True)
            self.theme_button.setText("Light Mode")
        else:  # Light or Auto
            self.theme_button.setChecked(False)
            self.theme_button.setText("Dark Mode")

        # Check if we have a custom theme file to apply
        custom_theme = self.settings.value("customTheme", "", type=str)
        if custom_theme:
            theme_path = RESOURCES_DIR / f"{custom_theme}_theme.qss"
            if theme_path.exists():
                # Apply the custom theme
                self._apply_theme_from_file(theme_path)

                # Update theme actions
                for action in self.theme_actions:
                    action.setChecked(action.data() == custom_theme)

    def _load_settings(self):
        """Loads UI settings like theme and font size."""
        font_size = self.settings.value("fontSize", DEFAULT_FONT_SIZE, type=int)
        if not isinstance(font_size, int): return
        self.font_size_spinbox.setValue(font_size)
        self._update_font_size(font_size)

    def closeEvent(self, event):
        """Handle window close event."""
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()


# --- Main Execution ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName(SETTINGS_APP)
    app.setOrganizationName(SETTINGS_ORG)

    # Force style for more consistent look across platforms initially
    app.setStyle(QStyleFactory.create(STYLE_SELECTED_THEME))

    # Set color scheme to Auto by default
    app.styleHints().setColorScheme(Qt.ColorScheme.Unknown)  # Auto/Unknown = system default

    # Create and show the main window
    window = MainWindow()

    # Restore window geometry
    geometry = window.settings.value("geometry")
    if geometry:
        window.restoreGeometry(geometry)
    else:
        window.resize(DEFAULT_WINDOW_SIZE)

    window.show()

    sys.exit(app.exec())
