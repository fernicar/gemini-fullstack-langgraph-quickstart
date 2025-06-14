# PySide6 Examples Documentation Initiative

This repository contains a collection of PySide6 examples, each with a `README.md` file summarizing its functionality, key PySide6/Qt concepts demonstrated, and instructions on how to run it.

The goal of this initiative is to provide clear, concise, and informative documentation for each example, making it easier for developers to learn and utilize PySide6.

## PySide6 Modern Usage Guide (v6.9.1+)

This guide highlights modern PySide6 usage patterns and best practices, derived from analyzing the official examples. It aims to help developers use current APIs and avoid outdated idioms.

### QtCore

#### Enums
- Use `Qt.AlignmentFlag.AlignBottom` (scoped enum). Context from: `examples/bluetooth/btscanner/README.md`
- Use `Qt.AlignmentFlag.AlignHCenter` (scoped enum). Context from: `examples/async/minimal/README.md`
- Use `Qt.AlignmentFlag.AlignLeft` (scoped enum). Context from: `examples/bluetooth/btscanner/README.md`
- Use `Qt.AlignmentFlag.AlignRight` (scoped enum). Context from: `examples/charts/donutbreakdown/README.md`
- Use `Qt.AlignmentFlag.AlignTop` (scoped enum). Context from: `examples/charts/legend/README.md`
- Use `Qt.AlignmentFlag.AlignVCenter` (scoped enum). Context from: `examples/async/minimal/README.md`
- Use `Qt.ApplicationAttribute.AA_EnableHighDpiScaling` (scoped enum). Context from: `examples/opengl/hellogl2/README.md`
- Use `Qt.ApplicationAttribute.AA_UseDesktopOpenGL` (scoped enum). Context from: `examples/opengl/contextinfo/README.md`
- Use `Qt.ApplicationAttribute.AA_UseOpenGLES` (scoped enum). Context from: `examples/opengl/contextinfo/README.md`
- Use `Qt.ApplicationAttribute.AA_UseSoftwareOpenGL` (scoped enum). Context from: `examples/opengl/contextinfo/README.md`
- Use `Qt.AspectRatioMode.KeepAspectRatio` (scoped enum). Context from: `examples/widgets/desktop/screenshot/README.md`
- Use `Qt.CheckState.Checked` (scoped enum). Context from: `examples/charts/pointselectionandmarkers/README.md`
- Use `Qt.CheckState.Unchecked` (scoped enum). Context from: `examples/charts/pointselectionandmarkers/README.md`
- Use `Qt.ContextMenuPolicy.CustomContextMenu` (scoped enum). Context from: `examples/widgets/desktop/systray/README.md`
- Use `Qt.CursorShape.WaitCursor` (scoped enum). Context from: `examples/network/loopback/README.md`
- Use `Qt.DropAction.CopyAction` (scoped enum). Context from: `examples/widgets/draganddrop/draggabletext/README.md`
- Use `Qt.DropAction.MoveAction` (scoped enum). Context from: `examples/widgets/draganddrop/draggabletext/README.md`
- Use `Qt.GestureType.PanGesture` (scoped enum). Context from: `examples/charts/zoomlinechart/README.md`
- Use `Qt.GestureType.PinchGesture` (scoped enum). Context from: `examples/charts/zoomlinechart/README.md`
- Use `Qt.GlobalColor.black` (scoped enum). Context from: `examples/statemachine/trafficlight/README.md`
- Use `Qt.GlobalColor.blue` (scoped enum). Context from: `examples/statemachine/moveblocks/README.md`
- Use `Qt.GlobalColor.green` (scoped enum). Context from: `examples/charts/piechart/README.md`
- Use `Qt.GlobalColor.red` (scoped enum). Context from: `examples/statemachine/trafficlight/README.md`
- Use `Qt.GlobalColor.white` (scoped enum). Context from: `examples/charts/nesteddonuts/README.md`
- Use `Qt.ItemDataRole.BackgroundRole` (scoped enum). Context from: `examples/charts/modeldata/README.md`
- Use `Qt.ItemDataRole.DisplayRole` (scoped enum). Context from: `examples/corelib/mimetypesbrowser/README.md`
- Use `Qt.ItemDataRole.EditRole` (scoped enum). Context from: `examples/charts/modeldata/README.md`
- Use `Qt.ItemDataRole.UserRole` (scoped enum). Context from: `examples/corelib/mimetypesbrowser/README.md`
- Use `Qt.ItemFlag.ItemIsUserCheckable` (scoped enum). Context from: `best_gui.py` (Checklist feature)
- Use `Qt.Key.Key_Down` (scoped enum). Context from: `examples/charts/zoomlinechart/README.md`
- Use `Qt.Key.Key_Left` (scoped enum). Context from: `examples/charts/zoomlinechart/README.md`
- Use `Qt.Key.Key_Minus` (scoped enum). Context from: `examples/charts/zoomlinechart/README.md`
- Use `Qt.Key.Key_Plus` (scoped enum). Context from: `examples/charts/zoomlinechart/README.md`
- Use `Qt.Key.Key_Q` (scoped enum). Context from: `examples/statemachine/rogue/README.md`
- Use `Qt.Key.Key_Right` (scoped enum). Context from: `examples/charts/zoomlinechart/README.md`
- Use `Qt.Key.Key_Up` (scoped enum). Context from: `examples/charts/zoomlinechart/README.md`
- Use `Qt.MouseButton.LeftButton` (scoped enum). Context from: `examples/opengl/hellogl2/README.md`
- Use `Qt.MouseButton.MiddleButton` (scoped enum). Context from: `examples/qml/editingmodel/README.md`
- Use `Qt.MouseButton.RightButton` (scoped enum). Context from: `examples/opengl/hellogl2/README.md`
- Use `Qt.Orientation.Horizontal` (scoped enum). Context from: `examples/charts/areachart/README.md`
- Use `Qt.Orientation.Vertical` (scoped enum). Context from: `examples/charts/areachart/README.md`
- Use `Qt.PenStyle.NoPen` (scoped enum). Context from: `examples/gui/analogclock/README.md`
- Use `QTextDocument.FindFlag.FindCaseSensitively` (scoped enum). Context from: `best_gui.py` (Find/Replace feature)
- Use `QTextDocument.FindFlag.FindWholeWords` (scoped enum). Context from: `best_gui.py` (Find/Replace feature)
- Use `Qt.WindowFlags.FramelessWindowHint` (scoped enum). Context from: `examples/webenginewidgets/notifications/README.md`
- Use `Qt.WindowFlags.SplashScreen` (scoped enum). Context from: `examples/quick/window/README.md`
- Use `Qt.WindowFlags.ToolTip` (scoped enum). Context from: `examples/webenginewidgets/notifications/README.md`
- Use `Qt.WindowFlags.WindowStaysOnTopHint` (scoped enum). Context from: `examples/webenginewidgets/notifications/README.md`
- Use `Qt.WindowState.WindowFullScreen` (scoped enum). Context from: `examples/quick/window/README.md`
- Use `Qt.WindowState.WindowMaximized` (scoped enum). Context from: `examples/quick/window/README.md`
- Use `Qt.WindowState.WindowMinimized` (scoped enum). Context from: `examples/quick/window/README.md`

#### Properties
- Define properties like: `@Property(QColor, notify=color_changed)`. Context: `examples/qml/tutorials/extending-qml/chapter4-customPropertyTypes/RE...`
- Define properties like: `@Property(QUrl, notify=sourceChanged)`. Context: `examples/multimedia/player/README.md`
- Define properties like: `@Property(bool, notify=rightAlignedChanged)`. Context: `examples/quick/painteditem/README.md`
- Define properties like: `@Property(float, notify=tChanged)`. Context: `examples/quick/scenegraph/openglunderqml/README.md`
- Define properties like: `@Property(int, notify=angle_changed)`. Context: `examples/widgets/tutorials/cannon/README.md`
- Define properties like: `@Property(str, notify=statusChanged)`. Context: `examples/statemachine/rogue/README.md`
- Define properties like: `@Property(str, notify=textChanged)`. Context: `examples/webenginewidgets/markdowneditor/README.md`

#### Signals
- Define signals like: `Signal()`. Context: `examples/widgets/animation/appchooser/README.md`
- Define signals like: `Signal(QImage, float)`. Context: `examples/corelib/threads/README.md`
- Define signals like: `Signal(QPointF)`. Context: `examples/widgets/animation/easing/README.md`
- Define signals like: `Signal(bool)`. Context: `examples/widgets/tutorials/cannon/README.md`
- Define signals like: `Signal(int)`. Context: `examples/widgets/animation/easing/README.md`
- Define signals like: `Signal(int, str)`. Context: `examples/network/blockingfortuneclient/README.md`
- Define signals like: `Signal(list)`. Context: `examples/graphs/2d/graphsaudio/README.md`
- Define signals like: `Signal(object)`. Context: `examples/webchannel/standalone/README.md`
- Define signals like: `Signal(str)`. Context: `examples/network/blockingfortuneclient/README.md`

#### Slots
- Define slots like: `@Slot()`. Context: `examples/bluetooth/btscanner/README.md`
- Define slots like: `@Slot(QAbstractSocket.SocketError)`. Context: `examples/network/fortuneclient/README.md`
- Define slots like: `@Slot(QAudio.State)`. Context: `examples/multimedia/audiooutput/README.md`
- Define slots like: `@Slot(QBluetoothDeviceDiscoveryAgent.Error)`. Context: `examples/bluetooth/lowenergyscanner/README.md`
- Define slots like: `@Slot(QBluetoothDeviceInfo)`. Context: `examples/bluetooth/btscanner/README.md`
- Define slots like: `@Slot(QBluetoothServiceInfo)`. Context: `examples/bluetooth/btscanner/README.md`
- Define slots like: `@Slot(QCloseEvent)`. Context: `examples/widgets/desktop/systray/README.md`
- Define slots like: `@Slot(QListWidgetItem)`. Context: `examples/widgets/dialogs/standarddialogs/README.md`
- Define slots like: `@Slot(QMediaCaptureSession.State)`. Context: `examples/multimedia/camera/README.md`
- Define slots like: `@Slot(QMediaPlayer.PlaybackState)`. Context: `examples/multimedia/player/README.md`
- Define slots like: `@Slot(QModelIndex)`. Context: `examples/corelib/mimetypesbrowser/README.md`
- Define slots like: `@Slot(QNetworkReply)`. Context: `examples/network/googlesuggest/README.md`
- Define slots like: `@Slot(QPoint)`. Context: `examples/widgets/animation/animatedtiles/README.md`
- Define slots like: `@Slot(QPointF)`. Context: `examples/charts/callout/README.md`
- Define slots like: `@Slot(QProcess.ExitStatus)`. Context: `examples/corelib/mimetypesbrowser/README.md`
- Define slots like: `@Slot(QSystemTrayIcon.ActivationReason)`. Context: `examples/widgets/desktop/systray/README.md`
- Define slots like: `@Slot(QUrl)`. Context: `examples/webenginewidgets/widgetsnanobrowser/README.md`
- Define slots like: `@Slot(bool)`. Context: `examples/charts/callout/README.md`
- Define slots like: `@Slot(bytes)`. Context: `examples/serialport/terminal/README.md`
- Define slots like: `@Slot(float)`. Context: `examples/spatialaudio/audiopanning/README.md`
- Define slots like: `@Slot(int)`. Context: `examples/charts/callout/README.md`
- Define slots like: `@Slot(int, QModelIndex, QModelIndex)`. Context: `examples/corelib/settingseditor/README.md`
- Define slots like: `@Slot(int, str)`. Context: `examples/network/blockingfortuneclient/README.md`
- Define slots like: `@Slot(object)`. Context: `examples/webchannel/standalone/README.md`
- Define slots like: `@Slot(str)`. Context: `examples/corelib/mimetypesbrowser/README.md`
- Define slots like: `@Slot(str, result=QUrl)`. Context: `examples/webenginequick/nanobrowser/README.md`
- Define slots like: `@Slot(str, result=str)`. Context: `examples/qml/textproperties/README.md`

#### Timers
- Use `QTimer.singleShot(delay_ms, callback_slot)` for a non-repeating timer. Context from: `best_gui.py` (Chat Preview bot simulation)

### QtWidgets

#### ItemViews
- Employ Model/View architecture with QAbstractItemModel, delegates, and proxy models. Context: `examples/sql/books/README.md`
- Employ Model/View architecture with QAbstractItemModel, delegates, and proxy models. Context: `examples/widgets/itemviews/address_book/README.md`
- Employ Model/View architecture with QAbstractItemModel, delegates, and proxy models. Context: `examples/widgets/itemviews/basicfiltermodel/README.md`
- Employ Model/View architecture with QAbstractItemModel, delegates, and proxy models. Context: `examples/widgets/itemviews/dirview/README.md`
- Employ Model/View architecture with QAbstractItemModel, delegates, and proxy models. Context: `examples/widgets/itemviews/editabletreemodel/README.md`
- Employ Model/View architecture with QAbstractItemModel, delegates, and proxy models. Context: `examples/widgets/itemviews/fetchmore/README.md`
- Employ Model/View architecture with QAbstractItemModel, delegates, and proxy models. Context: `examples/widgets/itemviews/jsonmodel/README.md`
- Employ Model/View architecture with QAbstractItemModel, delegates, and proxy models. Context: `examples/widgets/itemviews/spinboxdelegate/README.md`
- Employ Model/View architecture with QAbstractItemModel, delegates, and proxy models. Context: `examples/widgets/itemviews/spreadsheet/README.md`
- Employ Model/View architecture with QAbstractItemModel, delegates, and proxy models. Context: `examples/widgets/itemviews/stardelegate/README.md`
- Employ Model/View architecture with QAbstractItemModel, delegates, and proxy models. Context: `examples/widgets/tutorials/modelview/README.md`
- Utilize `QListWidget` for simple list management with `QListWidgetItem`. Context from: `best_gui.py` (Checklist feature)

#### Layouts
- Utilize standard layouts like QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout. Context: `examples/widgets/dialogs/classwizard/README.md`
- Utilize standard layouts like QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout. Context: `examples/widgets/dialogs/extension/README.md`
- Utilize standard layouts like QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout. Context: `examples/widgets/dialogs/licensewizard/README.md`
- Utilize standard layouts like QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout. Context: `examples/widgets/dialogs/standarddialogs/README.md`
- Utilize standard layouts like QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout. Context: `examples/widgets/dialogs/tabdialog/README.md`
- Utilize standard layouts like QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout. Context: `examples/widgets/dialogs/trivialwizard/README.md`
- Utilize standard layouts like QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout. Context: `examples/widgets/layouts/basiclayouts/README.md`
- Utilize standard layouts like QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout. Context: `examples/widgets/layouts/borderlayout/README.md`
- Utilize standard layouts like QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout. Context: `examples/widgets/layouts/dynamiclayouts/README.md`
- Utilize standard layouts like QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout. Context: `examples/widgets/layouts/flowlayout/README.md`

#### Painting
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/gui/analogclock/README.md`
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/quick/painteditem/README.md`
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/statemachine/rogue/README.md`
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/statemachine/trafficlight/README.md`
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/widgets/animation/appchooser/README.md`
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/widgets/painting/basicdrawing/README.md`
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/widgets/painting/concentriccircles/README.md`
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/widgets/painting/painter/README.md`
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/widgets/painting/plot/README.md`
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/widgets/tutorials/cannon/README.md`
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/widgets/widgets/charactermap/README.md`
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/widgets/widgets/digitalclock/README.md`
- Perform custom drawing in `paintEvent` using QPainter. Context: `examples/widgets/widgets/tetrix/README.md`

#### Standard Dialogs
- Use `QInputDialog.getText(parent, title, label)` for simple text input. Context from: `best_gui.py` (Find feature)
- Use `QMessageBox.information(parent, title, message)` for informational popups. Context from: `best_gui.py` (Find feature)
- Use `QDialog` as a base for custom dialogs. Context from: `best_gui.py` (Replace feature)

### QtQml

#### Integration
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/editingmodel/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/textproperties/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml-advanced/adding/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml-advanced/advanced1-Base-project/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml-advanced/advanced2-Inheritance-and-coerc...`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml-advanced/advanced3-Default-properties/READ...`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml-advanced/advanced4-Grouped-properties/READ...`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml-advanced/advanced5-Attached-properties/REA...`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml-advanced/advanced6-Property-value-source/...`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml-advanced/binding/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml-advanced/extended/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml-advanced/methods/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml-advanced/properties/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml/chapter1-basics/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml/chapter2-methods/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml/chapter3-bindings/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml/chapter4-customPropertyTypes/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml/chapter5-listproperties/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/tutorials/extending-qml/chapter6-plugins/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/qml/usingmodel/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/quick/models/objectlistmodel/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/quick/models/stringlistmodel/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/quick/painteditem/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/quick/scenegraph/openglunderqml/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/quick/scenegraph/scenegraph_customgeometry/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/quick3d/customgeometry/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/quick3d/proceduraltexture/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/tutorials/finance_manager/part1/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/tutorials/finance_manager/part2/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/tutorials/finance_manager/part3/README.md`
- Use `@QmlElement` for exposing Python classes to QML. Context: `examples/webenginequick/nanobrowser/README.md`


---
*(This guide is auto-generated based on heuristics. Always refer to official PySide6 documentation for definitive information.)*