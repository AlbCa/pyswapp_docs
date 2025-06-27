# # import matplotlib
# # # prevent NoneType error for versions of matplotlib 3.1.0rc1+ by calling matplotlib.use()
# # # For more on why it's nececessary, see
# # # https://stackoverflow.com/questions/59656632/using-qt5agg-backend-with-matplotlib-3-1-2-get-backend-changes-behavior
# # matplotlib.use('qt5agg')
# #
# # from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# # from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
# # import matplotlib.pyplot as plt
# # import numpy as np
# # from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QAction, QTabWidget,QVBoxLayout, QHBoxLayout, QStackedWidget
# # from PyQt5.QtGui import QIcon
# # from PyQt5.QtCore import pyqtSlot, QSize
# # import sys
# #
# # #
# # # class plotWindow():
# # #     def __init__(self, parent=None):
# # #         self.app = QApplication.instance()
# # #         if not self.app:
# # #             self.app = QApplication(sys.argv)
# # #         self.MainWindow = QMainWindow()
# # #         self.MainWindow.setWindowTitle("plot window")
# # #         self.canvases = []
# # #         self.figure_handles = []
# # #         self.toolbar_handles = []
# # #         self.tab_handles = []
# # #         self.current_window = -1
# # #         #self.tabs = QStackedWidget()# QTabWidget()
# # #         self.tabs = QTabWidget()
# # #         self.MainWindow.setCentralWidget(self.tabs)
# # #         self.MainWindow.resize(1280, 900)
# # #         self.MainWindow.show()
# # #
# # #     def addPlot(self, title, figure):
# # #         new_tab = QWidget()
# # #         layout = QVBoxLayout()
# # #         new_tab.setLayout(layout)
# # #
# # #         figure.subplots_adjust(left=0.05, right=0.99, bottom=0.05, top=0.91, wspace=0.2, hspace=0.2)
# # #         new_canvas = FigureCanvas(figure)
# # #         new_toolbar = NavigationToolbar(new_canvas, new_tab)
# # #
# # #         layout.addWidget(new_canvas)
# # #         layout.addWidget(new_toolbar)
# # #         self.tabs.addTab(new_tab, title)
# # #         #self.tabs.addWidget(new_tab)
# # #
# # #         self.toolbar_handles.append(new_toolbar)
# # #         self.canvases.append(new_canvas)
# # #         self.figure_handles.append(figure)
# # #         self.tab_handles.append(new_tab)
# # #
# # #     def show(self):
# # #         self.app.exec_()
# # #
# # # if __name__ == '__main__':
# # #     import numpy as np
# # #
# # #
# # #     pw = plotWindow()
# # #
# # #     x = np.arange(0, 10, 0.001)
# # #
# # #     f = plt.figure()
# # #     ysin = np.sin(x)
# # #     plt.plot(x, ysin, '--')
# # #     pw.addPlot("sin", f)
# # #
# # #     f = plt.figure()
# # #     ycos = np.cos(x)
# # #     plt.plot(x, ycos, '--')
# # #     pw.addPlot("cos", f)
# # #     pw.show()
# # #
# # #     # sys.exit(app.exec_())
# #
# #
# # # import sys
# # # from PyQt5.QtWidgets import (
# # #     QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
# # # )
# # # from PyQt5.QtCore import Qt
# # # from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# # # from matplotlib.figure import Figure
# # #
# # #
# # # class FigureSwitcher(QMainWindow):
# # #     def __init__(self, figures):
# # #         super().__init__()
# # #         self.setWindowTitle("Figure Switcher")
# # #
# # #         self.figures = figures
# # #         self.current_index = 0
# # #
# # #         self.init_ui()
# # #
# # #     def init_ui(self):
# # #         # Main widget
# # #         central_widget = QWidget()
# # #         self.setCentralWidget(central_widget)
# # #
# # #         # Layouts
# # #         main_layout = QVBoxLayout()
# # #         nav_layout = QHBoxLayout()
# # #         main_layout.addLayout(nav_layout)
# # #         central_widget.setLayout(main_layout)
# # #
# # #         # Navigation buttons
# # #         self.left_btn = QPushButton()
# # #         self.left_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
# # #         self.left_btn.setFixedSize(40, 40)
# # #
# # #         self.right_btn = QPushButton()
# # #         self.right_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
# # #         self.right_btn.setFixedSize(40, 40)
# # #
# # #         nav_layout.addWidget(self.left_btn)
# # #         nav_layout.addWidget(self.right_btn)
# # #         nav_layout.addStretch()
# # #
# # #         self.left_btn.clicked.connect(self.show_previous_figure)
# # #         self.right_btn.clicked.connect(self.show_next_figure)
# # #
# # #         # Canvas for figure
# # #         self.canvas = FigureCanvas(self.figures[self.current_index])
# # #         main_layout.addWidget(self.canvas)
# # #
# # #     def show_previous_figure(self):
# # #         if self.current_index > 0:
# # #             self.current_index -= 1
# # #             self.update_figure()
# # #         else:
# # #             self.current_index = len(self.figures) - 1
# # #             self.update_figure()
# # #
# # #     def show_next_figure(self):
# # #         if self.current_index < len(self.figures) - 1:
# # #             self.current_index += 1
# # #             self.update_figure()
# # #         else:
# # #             self.current_index = 0
# # #             self.update_figure()
# # #
# # #     def update_figure(self):
# # #         self.canvas.setParent(None)
# # #         self.canvas = FigureCanvas(self.figures[self.current_index])
# # #         self.centralWidget().layout().addWidget(self.canvas)
# # #
# # #
# # # def create_sample_figures():
# # #     figures = []
# # #
# # #     for i in range(5):
# # #         fig = Figure()
# # #         ax = fig.add_subplot(111)
# # #         ax.plot([j for j in range(10)], [j * (i + 1) for j in range(10)])
# # #         ax.set_title(f"Figure {i + 1}")
# # #         figures.append(fig)
# # #
# # #     return figures
# # #
# # #
# # # if __name__ == "__main__":
# # #     app = QApplication(sys.argv)
# # #     figures = create_sample_figures()
# # #     window = FigureSwitcher(figures)
# # #     window.resize(800, 600)
# # #     window.show()
# # #     sys.exit(app.exec_())
# #
# #
# # # import sys
# # # import pandas as pd
# # # from PyQt5.QtWidgets import (
# # #     QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
# # #     QPushButton
# # # )
# # # from PyQt5.QtCore import Qt, QSize
# # # from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# # # from matplotlib.figure import Figure
# # #
# # #
# # # class PlotSwitcher(QMainWindow):
# # #     def __init__(self, datasets):
# # #         super().__init__()
# # #         self.setWindowTitle("Dataset Plot Viewer")
# # #         self.datasets = datasets
# # #         self.current_index = 0
# # #
# # #         self.init_ui()
# # #
# # #     def init_ui(self):
# # #         # Main widget
# # #         central_widget = QWidget()
# # #         self.setCentralWidget(central_widget)
# # #
# # #         # Layouts
# # #         main_layout = QVBoxLayout()
# # #         nav_layout = QHBoxLayout()
# # #         central_widget.setLayout(main_layout)
# # #
# # #         # Navigation buttons
# # #         self.left_btn = QPushButton()
# # #         self.left_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
# # #         self.left_btn.setFixedSize(40, 40)
# # #         self.left_btn.setIconSize(QSize(24, 24))
# # #
# # #         self.right_btn = QPushButton()
# # #         self.right_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
# # #         self.right_btn.setFixedSize(40, 40)
# # #         self.right_btn.setIconSize(QSize(24, 24))
# # #
# # #         nav_layout.addWidget(self.left_btn)
# # #         nav_layout.addWidget(self.right_btn)
# # #         nav_layout.addStretch()
# # #
# # #         self.left_btn.clicked.connect(self.show_previous)
# # #         self.right_btn.clicked.connect(self.show_next)
# # #
# # #         # Matplotlib Figure and Canvas
# # #         self.figure = Figure()
# # #         self.canvas = FigureCanvas(self.figure)
# # #         self.canvas.mpl_connect("button_press_event", self.on_plot_click)
# # #
# # #         main_layout.addLayout(nav_layout)
# # #         main_layout.addWidget(self.canvas)
# # #
# # #         self.plot_dataset()
# # #
# # #     def plot_dataset(self):
# # #         self.figure.clear()
# # #         ax = self.figure.add_subplot(111)
# # #
# # #         df = self.datasets[self.current_index]
# # #         df.plot(x="X", y=df.columns[1], ax=ax, marker='o')
# # #         ax.set_title(f"Dataset {self.current_index + 1}")
# # #         self.canvas.draw()
# # #
# # #     def show_previous(self):
# # #         if self.current_index > 0:
# # #             self.current_index -= 1
# # #             self.plot_dataset()
# # #
# # #     def show_next(self):
# # #         if self.current_index < len(self.datasets) - 1:
# # #             self.current_index += 1
# # #             self.plot_dataset()
# # #
# # #     def on_plot_click(self, event):
# # #         """Handle mouse clicks on the plot to add a new point."""
# # #         if event.inaxes:
# # #             df = self.datasets[self.current_index]
# # #             new_x = event.xdata
# # #             new_y = event.ydata
# # #
# # #             # Append new point
# # #             new_row = pd.DataFrame({"X": [new_x], df.columns[1]: [new_y]})
# # #             self.datasets[self.current_index] = pd.concat([df, new_row], ignore_index=True).sort_values(by="X").reset_index(drop=True)
# # #
# # #             self.plot_dataset()
# # #
# # #
# # # def create_sample_datasets():
# # #     datasets = []
# # #     for i in range(5):
# # #         df = pd.DataFrame({
# # #             "X": list(range(10)),
# # #             f"Y{i+1}": [x * (i + 1) for x in range(10)]
# # #         })
# # #         datasets.append(df)
# # #     return datasets
# # #
# # #
# # # if __name__ == "__main__":
# # #     app = QApplication(sys.argv)
# # #     datasets = create_sample_datasets()
# # #     window = PlotSwitcher(datasets)
# # #     window.resize(800, 600)
# # #     window.show()
# # #     sys.exit(app.exec_())
# #
# # # import sys
# # # import numpy as np
# # # import pandas as pd
# # # from collections.abc import Iterable
# # # from PyQt5.QtWidgets import (
# # #     QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
# # #     QPushButton
# # # )
# # # from PyQt5.QtCore import Qt, QSize
# # # from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# # # from matplotlib.figure import Figure
# # #
# # #
# # # class DraggablePoints:
# # #     def __init__(self, ax, points=None, kwargs=None):
# # #         self.ax = ax
# # #         self.canvas = self.ax.figure.canvas
# # #
# # #         self.distance_threshold = 0.1  # Threshold in data coords (adjust if needed)
# # #         self._dragging_point = None
# # #         self._points = {}  # Dict: x -> y
# # #
# # #         if kwargs is None:
# # #             kwargs = dict(color='r', linestyle='--', linewidth=1, markersize=7, marker='x')
# # #         self._kwargs = kwargs
# # #
# # #         if points is not None:
# # #             for x, y in points.items():
# # #                 self._points[x] = y
# # #
# # #         self._line = None
# # #         self._init_plot()
# # #
# # #     def _init_plot(self):
# # #         """Connect matplotlib events."""
# # #         self.canvas.mpl_connect('button_press_event', self._on_click)
# # #         self.canvas.mpl_connect('button_release_event', self._on_release)
# # #         self.canvas.mpl_connect('motion_notify_event', self._on_motion)
# # #
# # #     def _update_plot(self):
# # #         """Update line data and redraw."""
# # #         if not self._points:
# # #             if self._line:
# # #                 self._line.set_data([], [])
# # #         else:
# # #             x, y = zip(*sorted(self._points.items()))
# # #             if not self._line:
# # #                 self._line, = self.ax.plot(x, y, **self._kwargs)
# # #             else:
# # #                 self._line.set_data(x, y)
# # #         self.canvas.draw_idle()
# # #
# # #     def _add_point(self, x, y):
# # #         """Add or update a point."""
# # #         self._points[x] = y
# # #         return x, y
# # #
# # #     def _remove_point(self, x, _):
# # #         """Remove a point by its x coordinate."""
# # #         if x in self._points:
# # #             self._points.pop(x)
# # #
# # #     def _find_neighbor_point(self, event):
# # #         """Find nearest point to the mouse event within threshold."""
# # #         if not self._points or event.xdata is None or event.ydata is None:
# # #             return None
# # #
# # #         points = np.array(list(self._points.items()))
# # #         mouse_pos = np.array([event.xdata, event.ydata])
# # #
# # #         distances = np.sqrt(np.sum((points - mouse_pos) ** 2, axis=1))
# # #         nearest_idx = np.argmin(distances)
# # #         if distances[nearest_idx] < self.distance_threshold:
# # #             nearest_point = (points[nearest_idx][0], points[nearest_idx][1])
# # #             return nearest_point
# # #         return None
# # #
# # #     def _on_click(self, event):
# # #         if event.inaxes != self.ax:
# # #             return
# # #
# # #         # Left click: start drag or add point
# # #         if event.button == 1:
# # #             point = self._find_neighbor_point(event)
# # #             if point:
# # #                 self._dragging_point = point
# # #             else:
# # #                 self._add_point(event.xdata, event.ydata)
# # #                 self._update_plot()
# # #
# # #         # Right click: remove point
# # #         elif event.button == 3:
# # #             point = self._find_neighbor_point(event)
# # #             if point:
# # #                 self._remove_point(*point)
# # #                 self._update_plot()
# # #
# # #     def _on_release(self, event):
# # #         if event.button == 1 and self._dragging_point:
# # #             self._dragging_point = None
# # #             self._update_plot()
# # #
# # #     def _on_motion(self, event):
# # #         if not self._dragging_point or event.inaxes != self.ax:
# # #             return
# # #         if event.xdata is None or event.ydata is None:
# # #             return
# # #
# # #         self._remove_point(*self._dragging_point)
# # #         self._dragging_point = self._add_point(event.xdata, event.ydata)
# # #         self._update_plot()
# # #
# # #     @property
# # #     def points(self):
# # #         return self._points
# # #
# # #
# # # class PlotSwitcher(QMainWindow):
# # #     def __init__(self, datasets):
# # #         super().__init__()
# # #         self.setWindowTitle("Interactive Dataset Plot Viewer")
# # #         self.datasets = datasets  # List of pandas DataFrames
# # #         self.points_list = {}
# # #         self.current_index = 0
# # #
# # #         self.init_ui()
# # #
# # #     def init_ui(self):
# # #         central_widget = QWidget()
# # #         self.setCentralWidget(central_widget)
# # #
# # #         main_layout = QVBoxLayout()
# # #         nav_layout = QHBoxLayout()
# # #         central_widget.setLayout(main_layout)
# # #
# # #         # Navigation buttons (left/right arrows)
# # #         self.left_btn = QPushButton()
# # #         self.left_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
# # #         self.left_btn.setFixedSize(40, 40)
# # #         self.left_btn.setIconSize(QSize(24, 24))
# # #         self.left_btn.clicked.connect(self.show_previous)
# # #
# # #         self.right_btn = QPushButton()
# # #         self.right_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
# # #         self.right_btn.setFixedSize(40, 40)
# # #         self.right_btn.setIconSize(QSize(24, 24))
# # #         self.right_btn.clicked.connect(self.show_next)
# # #
# # #         nav_layout.addWidget(self.left_btn)
# # #         nav_layout.addWidget(self.right_btn)
# # #         nav_layout.addStretch()
# # #
# # #         # Matplotlib Figure and Canvas
# # #         self.figure = Figure()
# # #         self.canvas = FigureCanvas(self.figure)
# # #         main_layout.addLayout(nav_layout)
# # #         main_layout.addWidget(self.canvas)
# # #         #self.setCentralWidget(main_widget)
# # #
# # #         self.ax = self.figure.add_subplot(111)
# # #         self.draggable = None  # Will hold DraggablePoints instance
# # #
# # #         self.plot_dataset()
# # #
# # #     def plot_dataset(self):
# # #         self.ax.clear()
# # #         df = self.datasets[self.current_index]
# # #
# # #         # Assume first column is X, second column is Y
# # #         x = df.iloc[:, 0]
# # #         y = df.iloc[:, 1]
# # #         self.ax.plot(x, y, 'b-', label='Data')
# # #         self.ax.set_title(f"Dataset {self.current_index + 1}")
# # #         self.ax.set_xlabel(df.columns[0])
# # #         self.ax.set_ylabel(df.columns[1])
# # #         self.ax.legend()
# # #
# # #         # Create dict for draggable points from current data
# # #         points_dict = dict(zip(x, y))
# # #
# # #         # Create DraggablePoints for this plot
# # #         if self.draggable:
# # #             pass
# # #
# # #         if self.current_index in self.points_list.keys():
# # #
# # #             if self.points_list[self.current_index]:
# # #                 x, y = zip(*sorted(self.points_list[self.current_index].items()))
# # #                 self.ax.plot(x, y, 'r-', label='Data')
# # #
# # #             self.draggable = DraggablePoints(self.ax, points=self.points_list[self.current_index])
# # #         else:
# # #             self.draggable = DraggablePoints(self.ax)
# # #
# # #         self.canvas.draw_idle()
# # #
# # #         self.points_list[self.current_index] = self.draggable.points
# # #
# # #     def show_previous(self):
# # #         if self.current_index > 0:
# # #             self.current_index -= 1
# # #             self.plot_dataset()
# # #
# # #     def show_next(self):
# # #         if self.current_index < len(self.datasets) - 1:
# # #             self.current_index += 1
# # #             self.plot_dataset()
# # #
# # #
# # # def create_sample_datasets():
# # #     datasets = []
# # #     for i in range(3):
# # #         df = pd.DataFrame({
# # #             "X": np.linspace(0, 10, 10),
# # #             f"Y{i+1}": np.sin(np.linspace(0, 10, 10) * (i+1))  # example function
# # #         })
# # #         datasets.append(df)
# # #     return datasets
# # #
# # #
# # # if __name__ == "__main__":
# # #     app = QApplication(sys.argv)
# # #     datasets = create_sample_datasets()
# # #     window = PlotSwitcher(datasets)
# # #     window.resize(800, 600)
# # #     window.show()
# # #     sys.exit(app.exec_())
# #
# #
# # # import sys
# # # from PyQt5.QtWidgets import (
# # #     QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
# # # )
# # # from matplotlib.backends.backend_qt5agg import (
# # #     FigureCanvasQTAgg as FigureCanvas,
# # #     NavigationToolbar2QT as NavigationToolbar
# # # )
# # # from matplotlib.figure import Figure
# # # import numpy as np
# # #
# # #
# # # class MplWidget(QWidget):
# # #     def __init__(self, parent=None):
# # #         super().__init__(parent)
# # #         self.canvas = FigureCanvas(Figure())
# # #         self.toolbar = NavigationToolbar(self.canvas, self)
# # #
# # #         layout = QVBoxLayout()
# # #         layout.addWidget(self.toolbar)
# # #         layout.addWidget(self.canvas)
# # #         self.setLayout(layout)
# # #
# # #
# # # class MainWindow(QMainWindow):
# # #     def __init__(self):
# # #         super().__init__()
# # #         self.setWindowTitle("Two Subplots with Independent Navigation Toolbars")
# # #
# # #         # Create main widget and layout
# # #         main_widget = QWidget()
# # #         main_layout = QHBoxLayout()
# # #
# # #         # First subplot
# # #         self.plot1 = MplWidget()
# # #         ax1 = self.plot1.canvas.figure.add_subplot(111)
# # #         t = np.linspace(0, 10, 100)
# # #         ax1.plot(t, np.sin(t))
# # #         ax1.set_title("Sine Wave")
# # #
# # #         # Second subplot
# # #         self.plot2 = MplWidget()
# # #         ax2 = self.plot2.canvas.figure.add_subplot(111)
# # #         ax2.plot(t, np.cos(t))
# # #         ax2.set_title("Cosine Wave")
# # #
# # #         # Add both plots to the layout
# # #         main_layout.addWidget(self.plot1)
# # #         main_layout.addWidget(self.plot2)
# # #
# # #         main_widget.setLayout(main_layout)
# # #         self.setCentralWidget(main_widget)
# # #
# # #
# # # if __name__ == "__main__":
# # #     app = QApplication(sys.argv)
# # #     window = MainWindow()
# # #     window.show()
# # #     sys.exit(app.exec_())
# #
# #
# # # from PyQt5.QtCore import pyqtSignal
# # # from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
# # # from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# # #
# # # class ViewerWidget(QWidget):
# # #     index_changed = pyqtSignal(int)
# # #
# # #     def __init__(self, figures, label_prefix="Figure", is_right=False):
# # #         super().__init__()
# # #         self.label_prefix = label_prefix
# # #         self.is_right = is_right
# # #         self.all_figures = figures  # If is_right: this is a list of lists
# # #         self.figures = figures if not is_right else figures[0]
# # #         self.current_index = 0
# # #         self.group_index = 0  # Only used on right side
# # #         self.init_ui()
# # #
# # #     def init_ui(self):
# # #         self.layout = QVBoxLayout(self)
# # #
# # #         # Navigation bar
# # #         nav_layout = QHBoxLayout()
# # #         self.left_btn = QPushButton()
# # #         self.left_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
# # #         self.left_btn.setFixedSize(40, 40)
# # #         self.right_btn = QPushButton()
# # #         self.right_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
# # #         self.right_btn.setFixedSize(40, 40)
# # #         self.label = QLabel()
# # #         nav_layout.addWidget(self.left_btn)
# # #         nav_layout.addWidget(self.right_btn)
# # #         nav_layout.addStretch()
# # #         nav_layout.addWidget(self.label)
# # #         self.layout.addLayout(nav_layout)
# # #
# # #         # Canvas
# # #         self.canvas = FigureCanvas(self.figures[self.current_index])
# # #         self.layout.addWidget(self.canvas)
# # #
# # #         # Connect buttons
# # #         self.left_btn.clicked.connect(self.show_previous_figure)
# # #         self.right_btn.clicked.connect(self.show_next_figure)
# # #
# # #         self.update_display()
# # #
# # #     def show_previous_figure(self):
# # #         self.current_index = (self.current_index - 1) % len(self.figures)
# # #         self.update_display()
# # #         if not self.is_right:
# # #             self.index_changed.emit(self.current_index)
# # #
# # #     def show_next_figure(self):
# # #         self.current_index = (self.current_index + 1) % len(self.figures)
# # #         self.update_display()
# # #         if not self.is_right:
# # #             self.index_changed.emit(self.current_index)
# # #
# # #     def update_display(self):
# # #         self.canvas.setParent(None)
# # #         self.canvas = FigureCanvas(self.figures[self.current_index])
# # #         self.layout.addWidget(self.canvas)
# # #         self.label.setText(f"{self.label_prefix} {self.current_index + 1} of {len(self.figures)}")
# # #
# # #     def set_group(self, group_index):
# # #         """Used by the right viewer to update its figure group."""
# # #         self.group_index = group_index
# # #         self.figures = self.all_figures[group_index]
# # #         self.current_index = 0
# # #         self.update_display()
# # #
# # #
# # # from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QApplication
# # # from matplotlib.figure import Figure
# # # import sys
# # #
# # # class FigureSwitcher(QMainWindow):
# # #     def __init__(self, figures1, grouped_figures2):
# # #         super().__init__()
# # #         self.setWindowTitle("Linked Multi-Viewer")
# # #
# # #         central_widget = QWidget()
# # #         self.setCentralWidget(central_widget)
# # #         layout = QHBoxLayout()
# # #         central_widget.setLayout(layout)
# # #
# # #         # Viewer 1: controls the index
# # #         self.viewer1 = ViewerWidget(figures1, label_prefix="Left")
# # #
# # #         # Viewer 2: shows groups of figures based on viewer1's index
# # #         self.viewer2 = ViewerWidget(grouped_figures2, label_prefix="Right", is_right=True)
# # #
# # #         layout.addWidget(self.viewer1)
# # #         layout.addWidget(self.viewer2)
# # #
# # #         # Link left to right
# # #         self.viewer1.index_changed.connect(self.viewer2.set_group)
# # #
# # #
# # # listx = range(1,12)
# # #
# # # # print([f"WIN {x}" for x in listx])
# # # from swa import *
# # #
# # # if __name__ == "__main__":
# # #     from matplotlib.figure import Figure
# # #     from PyQt5.QtWidgets import QApplication
# # #     import sys
# # #
# # #     app = QApplication(sys.argv)
# # #
# # #     def make_fig(title):
# # #         fig = Figure()
# # #         ax = fig.add_subplot(111)
# # #         ax.plot([1, 2, 3])
# # #         ax.set_title(title)
# # #         return fig
# # #
# # #     # Left figures
# # #     figures1 = [make_fig(f"Left {i}") for i in range(3)]
# # #
# # #     # Right: list of groups of figures
# # #     figures2 = [
# # #         [make_fig(f"R0-A"), make_fig(f"R0-B")],
# # #         [make_fig(f"R1-A")],
# # #         [make_fig(f"R2-A"), make_fig(f"R2-B"), make_fig(f"R2-C")]
# # #     ]
# # #
# # #     window = FigureSwitcher(figures1, figures2)
# # #     window.resize(1000, 600)
# # #     window.show()
# # #     sys.exit(app.exec_())
# # from swa import *
# # app = QApplication(sys.argv)
# # #
# # # Create example figures
# # figs = []
# # for i in range(3):
# #     fig = plt.figure()
# #     ax = fig.add_subplot(111)
# #     ax.plot(np.random.rand(10))
# #     figs.append(fig)
# #
# # labels = [f"Figure {i}" for i in range(3)]
# #
# # # Launch the viewer with interactive filtering
# # viewer = FigureSwitcher(figs, labels, interaction_class=FKFilterInteractive)
# # viewer.show()
# #
# # def handle_about_to_quit():
# #     points = viewer.get_points()
# #     print("Saved points:", points)  # or write to file
# #
# # app.aboutToQuit.connect(handle_about_to_quit)
# #
# # app.exec_()
# # # sys.exit(app.exec_())
# # #
# # # print(points)
# #
# # # Create example figures
# # figs = []
# # for i in range(3):
# #
# #     x = y = np.arange(10,100,20)
# #     X, Y = np.meshgrid(x, y)
# #     Z = X*Y
# #
# #     fig = plt.figure()
# #     ax = fig.add_subplot(111)
# #     ax.contourf(X, Y, Z, 10, cmap=plt.cm.viridis)
# #     figs.append(fig)
# #
# # labels = [f"Figure {i}" for i in range(3)]
# #
# # # Launch the viewer with interactive filtering
# # viewer = FigureSwitcher(figs, labels, interaction_class=DCPickingInteractive, freq=x.real, vel=y.real, power=np.real(Z))
# # viewer.show()
# #
# # def handle_about_to_quit():
# #     points = viewer.get_points()
# #     print("Saved points:", points)  # or write to file
# #
# # app.aboutToQuit.connect(handle_about_to_quit)
# #
# # #sys.exit(app.exec_())
# # app.exec_()
# #
# # # import sys
# # # from PyQt5.QtWidgets import (
# # #     QApplication, QMainWindow, QVBoxLayout, QWidget,
# # #     QComboBox, QPushButton, QHBoxLayout
# # # )
# # # from matplotlib.backends.backend_qt5agg import (
# # #     FigureCanvasQTAgg as FigureCanvas,
# # #     NavigationToolbar2QT as NavigationToolbar
# # # )
# # # from matplotlib.figure import Figure
# # #
# # #
# # # class FigureSwitcherApp(QMainWindow):
# # #     def __init__(self):
# # #         super().__init__()
# # #         self.setWindowTitle("Figure Switcher with Drop-down")
# # #
# # #         # Main widget and layout
# # #         self.main_widget = QWidget(self)
# # #         self.setCentralWidget(self.main_widget)
# # #         self.layout = QVBoxLayout(self.main_widget)
# # #
# # #         # Dropdown (ComboBox) to select figure set
# # #         self.combo = QComboBox()
# # #         self.combo.addItems(["Set 1", "Set 2"])
# # #         self.combo.currentTextChanged.connect(self.change_figure_set)
# # #
# # #         # Navigation button
# # #         self.next_button = QPushButton("Next Figure")
# # #         self.next_button.clicked.connect(self.next_figure)
# # #
# # #         # Toolbar layout
# # #         top_layout = QHBoxLayout()
# # #         top_layout.addWidget(self.combo)
# # #         top_layout.addWidget(self.next_button)
# # #         self.layout.addLayout(top_layout)
# # #
# # #         # Define figure sets
# # #         self.figure_sets = {
# # #             "Set 1": [self.create_figure(1), self.create_figure(2)],
# # #             "Set 2": [self.create_figure(3), self.create_figure(4)],
# # #         }
# # #         self.current_set = "Set 1"
# # #         self.current_index = 0
# # #
# # #         # Matplotlib canvas and toolbar
# # #         self.canvas = FigureCanvas(self.figure_sets[self.current_set][self.current_index])
# # #         self.toolbar = NavigationToolbar(self.canvas, self)
# # #
# # #         self.layout.addWidget(self.toolbar)
# # #         self.layout.addWidget(self.canvas)
# # #
# # #     def create_figure(self, seed):
# # #         fig = Figure()
# # #         ax = fig.add_subplot(111)
# # #         ax.plot([seed * i for i in range(10)])
# # #         ax.set_title(f"Figure {seed}")
# # #         return fig
# # #
# # #     def change_figure_set(self, set_name):
# # #         self.current_set = set_name
# # #         self.current_index = 0
# # #         self.update_canvas()
# # #
# # #     def next_figure(self):
# # #         self.current_index = (self.current_index + 1) % len(self.figure_sets[self.current_set])
# # #         self.update_canvas()
# # #
# # #     def update_canvas(self):
# # #         self.layout.removeWidget(self.canvas)
# # #         self.canvas.setParent(None)  # Remove old canvas
# # #
# # #         self.canvas = FigureCanvas(self.figure_sets[self.current_set][self.current_index])
# # #         self.layout.addWidget(self.canvas)
# # #         self.toolbar.setParent(None)  # Remove old toolbar
# # #         self.toolbar = NavigationToolbar(self.canvas, self)
# # #         self.layout.insertWidget(1, self.toolbar)  # Put toolbar above canvas
# # #         self.canvas.draw()
# # #
# # #
# # # if __name__ == "__main__":
# # #     app = QApplication(sys.argv)
# # #     window = FigureSwitcherApp()
# # #     window.show()
# # #     sys.exit(app.exec_())
#
# # from PyQt5.QtWidgets import (
# #     QApplication, QWidget, QLabel, QComboBox, QPushButton,
# #     QVBoxLayout, QHBoxLayout
# # )
# #
# # class ComboBoxRowWithLabel(QWidget):
# #     def __init__(self):
# #         super().__init__()
# #
# #         # Left button
# #         left_button = QPushButton("Left")
# #
# #         # Label above ComboBoxes
# #         combo_label = QLabel("Choose options:")
# #
# #         # Two ComboBoxes side by side
# #         combo1 = QComboBox()
# #         combo1.addItems(["One", "Two", "Three"])
# #
# #         combo2 = QComboBox()
# #         combo2.addItems(["A", "B", "C"])
# #
# #         # Horizontal layout for the two ComboBoxes
# #         combo_row_layout = QHBoxLayout()
# #         combo_row_layout.addWidget(combo1)
# #         combo_row_layout.addWidget(combo2)
# #
# #         # Vertical layout for the label and ComboBoxes
# #         combo_with_label_layout = QVBoxLayout()
# #         combo_with_label_layout.addWidget(combo_label, alignment=Qt.AlignCenter)
# #         combo_with_label_layout.addLayout(combo_row_layout)
# #
# #         # Right buttons
# #         right_button1 = QPushButton("OK")
# #         right_button2 = QPushButton("Cancel")
# #
# #         right_buttons_layout = QVBoxLayout()
# #         right_buttons_layout.addWidget(right_button1)
# #         right_buttons_layout.addWidget(right_button2)
# #
# #         # Main horizontal layout
# #         main_layout = QHBoxLayout()
# #         main_layout.addWidget(left_button)
# #         main_layout.addLayout(combo_with_label_layout)
# #         main_layout.addLayout(right_buttons_layout)
# #
# #         self.setLayout(main_layout)
# #         self.setWindowTitle("Row with ComboBoxes and Label")
# #
# # # Required for alignment
# # from PyQt5.QtCore import Qt
# #
# # if __name__ == "__main__":
# #     import sys
# #     app = QApplication(sys.argv)
# #     window = ComboBoxRowWithLabel()
# #     window.show()
# #     sys.exit(app.exec_())
# #
# #
# #     # TODO: compute images for all procsets??
# #     # TODO: if FK or Dispersion image or seismogram is plotted --> add the interactor
# #     # TODO: apply the process directly to the data by passing data to to the plot switcher!
# #     # TODO: deal with windows
#
#     # def test_plot(self, attr='seismogram', procset = None, **kwargs):
#     #     """Plot the stream data"""
#     #
#     #     if attr == 'curve':
#     #         self.plot_curve(procset=procset,**kwargs)
#     #     elif attr == 'pseudosection':
#     #         self.plot_pseusodsection(procset=procset,**kwargs)
#     #     else:
#     #         figures = []
#     #         labels = []
#     #         figures_windows = []
#     #         labels_windows = []
#     #
#     #         for sin in self.data.keys():
#     #             for rep in self.data[sin].keys():
#     #                 self.select_data(sin, rep, inplace=True, verbose=False)
#     #                 fig = self._plot(attr, procset=procset,show = False,**kwargs)
#     #                 figures.append(fig)
#     #                 labels.append(f"SIN {sin} | REP {rep} | WIN {-1}")
#     #
#     #                 win_ax, wids = self._plot(attr, procset=procset, show=False, use_windows=True, **kwargs)
#     #                 figures_windows.append(win_ax)
#     #                 labels_windows.append([f"SIN {sin} | REP {rep} | WIN {x+1}" for x in wids])
#     #
#     #         if not any(figures_windows):
#     #             window = FigureSwitcher(figures, labels,
#     #                                     procset = procset,
#     #                                     procsets = self._sql.get_proc_labels(),
#     #                                     sql = self._sql)
#     #             window.resize(800, 600)
#     #             window.show()
#     #             self.app.exec_()
#     #         else:
#     #             raise NotImplementedError
#     #             # window = DualFigureSwitcher(figures, labels,
#     #             #                             figures_windows, labels_windows,
#     #             #                             procset = procset,
#     #             #                             procsets = self._sql.get_proc_labels())
#     #             # window.resize(1600, 600)
#     #             # window.show()
#     #             # self.app.exec_()
#
# # class FigureSwitcher(QWidget):
# #     index_changed = pyqtSignal(int)
# #
# #     def __init__(self, figures, labels, windows=False,
# #                  procset = None, procsets = None, sql = None, **kwargs):
# #         super().__init__()
# #
# #         self.logger = create_logging(name='QApp')
# #
# #         self.setWindowTitle("Data Viewer")
# #         self._sql = sql
# #
# #         self.is_grouped = windows
# #         self.all_figures = figures  # List of figures or list of lists
# #         self.all_labels = labels
# #
# #         self.group_index = 0
# #         self.current_index = 0
# #
# #         self.figures = self._get_current_figures()
# #         self.labels = self._get_current_labels()
# #
# #         # figure sets
# #         self.procset = procset
# #         self.procsets = procsets
# #         self.figure_sets = {procset: self.figures}
# #         self.label_sets = {procset: self.labels}
# #
# #         self.kwargs = kwargs
# #
# #         self.init_ui()
# #         self.update_display()
# #         self.canvas.setFocus()
# #
# #     def _get_current_figures(self):
# #         return self.all_figures if not self.is_grouped else self.all_figures[self.group_index]
# #
# #     def _get_current_labels(self):
# #         return self.all_labels if not self.is_grouped else self.all_labels[self.group_index]
# #
# #     def init_ui(self):
# #         self.layout = QVBoxLayout(self)
# #
# #         # Navigation bar
# #         self.nav_layout = QHBoxLayout()
# #         self.left_btn = QPushButton()
# #         self.left_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
# #         self.left_btn.setFixedSize(40, 40)
# #         self.right_btn = QPushButton()
# #         self.right_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
# #         self.right_btn.setFixedSize(40, 40)
# #
# #         # SIN/REP/WIN index
# #         self.label = QLabel()
# #         self.label.setStyleSheet("font-size: 14px; color: gray;")
# #
# #         self.nav_layout.addWidget(self.left_btn)
# #         self.nav_layout.addWidget(self.right_btn)
# #         self.nav_layout.addStretch()
# #         self.nav_layout.addWidget(self.label)
# #
# #         self.layout.addLayout(self.nav_layout)
# #
# #         self.left_btn.clicked.connect(self.show_previous_figure)
# #         self.right_btn.clicked.connect(self.show_next_figure)
# #
# #         # Canvas
# #         if self.figures:
# #             self.canvas = FigureCanvas(self.figures[self.current_index])
# #         else:
# #             self.canvas = FigureCanvas()
# #
# #         self.layout.addWidget(self.canvas)
# #
# #     def show_previous_figure(self):
# #         if not self.figures:
# #             return
# #         self.current_index = (self.current_index - 1) % len(self.figures)
# #         self.update_display()
# #         self.canvas.setFocus()
# #         if not self.is_grouped:
# #             self.index_changed.emit(self.current_index)
# #
# #     def show_next_figure(self):
# #         if not self.figures:
# #             return
# #         self.current_index = (self.current_index + 1) % len(self.figures)
# #         self.update_display()
# #         self.canvas.setFocus()
# #         if not self.is_grouped:
# #             self.index_changed.emit(self.current_index)
# #
# #     def update_display(self):
# #
# #         # Enable/disable navigation buttons
# #         num_figures = len(self.figures)
# #         is_navigation_enabled = num_figures > 1
# #         self.left_btn.setEnabled(is_navigation_enabled)
# #         self.right_btn.setEnabled(is_navigation_enabled)
# #
# #         if not self.figures:
# #             self.label.setText("No data")
# #             placeholder = QWidget()
# #             placeholder.setFixedSize(self.canvas.size())
# #             self.layout.replaceWidget(self.canvas, placeholder)
# #             self.canvas.setParent(None)
# #             self.canvas.deleteLater()
# #             self.canvas = placeholder
# #             return
# #
# #         # Update label
# #         self.label.setText(self.labels[self.current_index])
# #
# #         # Replace canvas
# #         self.layout.removeWidget(self.canvas)
# #         self.canvas.setParent(None)
# #         self.canvas.deleteLater()
# #         self.canvas = FigureCanvas(self.figures[self.current_index])
# #         self.layout.addWidget(self.canvas)
# #
# #     def set_group(self, group_index):
# #         """Used when figures are grouped (e.g., in a multi-view setup)."""
# #         if not self.is_grouped or group_index >= len(self.all_figures):
# #             return
# #
# #         self.group_index = group_index
# #         self.current_index = 0
# #         self.figures = self._get_current_figures()
# #         self.labels = self._get_current_labels()
# #         self.update_display()
# #
# #
# # class DualFigureSwitcher(QMainWindow):
# #     def __init__(self, figures1, labels1, grouped_figures2, grouped_labels2, procests = None):
# #         super().__init__()
# #         self.setWindowTitle("Data Viewer")
# #
# #         central_widget = QWidget()
# #         self.setCentralWidget(central_widget)
# #         layout = QHBoxLayout()
# #         central_widget.setLayout(layout)
# #
# #         # Viewer 1: controls the index
# #         self.viewer1 = FigureSwitcher(figures1, labels1, procests = procests)
# #         self.viewer1.setFixedSize(800, 600)
# #
# #         # Viewer 2: shows groups of figures based on viewer1's index
# #         self.viewer2 = FigureSwitcher(grouped_figures2, grouped_labels2, windows=True, procests = procests)
# #         self.viewer2.setFixedSize(800, 600)
# #
# #         layout.addWidget(self.viewer1)
# #         layout.addWidget(self.viewer2)
# #
# #         # Link left to right
# #         self.viewer1.index_changed.connect(self.viewer2.set_group)
#
# from swa import *
#
# # First figure
# fig1, ax1 = plt.subplots()
# ax1.plot(np.random.rand(10), np.random.rand(10))
# ax1.set_title("Figure 1 Title")
# ax1.set_xlabel("X Label")
# ax1.set_ylabel("Y Label")
#
# # Second figure
# fig2, ax2 = plt.subplots()
# ax2.plot(np.random.rand(10), np.random.rand(10))
# #ax2.set_title("Figure 2 Title")
# ax2.set_xlabel("X Label", labelpad=15)  # xlabel at bottom
#
# # Get position of ax1 in figure coordinates (bbox)
# pos1 = ax1.get_position()
#
# # Set position of ax2 to match ax1's position and size
# ax2.set_position(pos1)
#
# # # Ensure both figures have the same height for the axes
# # height1 = pos1.height
# # pos2 = ax2.get_position()
# #
# # # Adjust ax2's position height to match ax1's height
# # ax2.set_position([pos2.x0, pos2.y0, pos2.width, height1])
# #
# # # Adjust layout so that the figure fits well and titles/labels don't overlap
# # fig1.subplots_adjust(top=0.85, bottom=0.15)  # Adjust fig1 layout
# # fig2.subplots_adjust(top=0.85, bottom=0.15)  # Adjust fig2 layout
#
# plt.show()

from swa import *

prjdir = '/home/Natalie/Documents/Projects/GIT/swa/data/real_data/Moriago/test/'
path2raw = os.path.join(prjdir,'RIFL1')

setup_projectdir(prjdir)
rename_files(path2raw, extension = '.sg2', prjdir = prjdir, channel_nr = 1000)