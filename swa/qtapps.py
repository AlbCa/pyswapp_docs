import copy
from .utils.utils import *
from .utils.interactive import *
from .utils.sql import *
from .curve import DispersionCurve
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QLabel, QComboBox)

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure

from matplotlib.widgets import PolygonSelector
from matplotlib.path import Path

class FigureSwitcher(QMainWindow):
    """User interface to view the seismic data"""

    def __init__(self, figures):
        super().__init__()
        self.setWindowTitle("Data Preview Mode")

        self.figures = figures
        self.current_index = 0

        self.init_ui()

    def init_ui(self):
        """interface design"""

        # Canvas for figure
        self.canvas = FigureCanvas(self.figures[self.current_index])

        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Layouts
        layout = QVBoxLayout()
        nav_layout = QHBoxLayout()
        layout.addLayout(nav_layout)
        central_widget.setLayout(layout)

        # Navigation buttons
        self.left_btn = QPushButton()
        self.left_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
        self.left_btn.setFixedSize(40, 40)

        self.right_btn = QPushButton()
        self.right_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
        self.right_btn.setFixedSize(40, 40)

        nav_layout.addWidget(self.left_btn)
        nav_layout.addWidget(self.right_btn)
        nav_layout.addStretch()

        layout.addWidget(self.toolbar)

        self.left_btn.clicked.connect(self.show_previous_figure)
        self.right_btn.clicked.connect(self.show_next_figure)

        layout.addWidget(self.canvas)

    def show_previous_figure(self):
        """Switch to previous figure"""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_figure()
        else:
            self.current_index = len(self.figures) - 1
            self.update_figure()

    def show_next_figure(self):
        """Switch to next figure"""
        if self.current_index < len(self.figures) - 1:
            self.current_index += 1
            self.update_figure()
        else:
            self.current_index = 0
            self.update_figure()

    def update_figure(self):
        """Update figure"""
        self.canvas.setParent(None)
        self.canvas = FigureCanvas(self.figures[self.current_index])
        self.centralWidget().layout().addWidget(self.canvas)

class DualDataSwitcher(QMainWindow):
    """User interface to display raw data and select subset of data (e.g., based on windowing) side by side"""
    def __init__(self, data, sql, plot = 'geom', DataSwitcher = None, procset = None,
                 procsets = None, window_title = "SWA Viewer",select_plot = True, **kwargs):
        super().__init__()

        self.setWindowTitle(window_title)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        if not DataSwitcher:
            DataSwitcher = DataSwitcherBase

        # Viewer 1: controls the index
        self.viewer1 = DataSwitcherBase(data, sql, plot = '', procset = procset, procsets = procsets,
                                        select_plot = select_plot, **kwargs)
        self.viewer1.setFixedSize(400, 600)

        # Viewer 2: shows groups of figures based on viewer1's index
        self.viewer2 = DataSwitcher(data, sql, plot = plot, use_windows=True, procset = procset, procsets = procsets,
                                        select_plot = select_plot,
                                    window_label = 'WINDOWS',**kwargs)
        self.viewer2.setFixedSize(800, 600)

        layout.addWidget(self.viewer1)
        layout.addWidget(self.viewer2)

        # Link left to right
        self.viewer1.index_changed.connect(self.viewer2.set_group)
        self.viewer1.procset_changed.connect(self.viewer2.set_procset)
        self.viewer1.plot_changed.connect(self.viewer2.set_plot)

    def clean(self):
        self.viewer1.clean()
        self.viewer2.clean()

    def closeEvent(self, event):
        self.viewer1.closeEvent(event)
        self.viewer2.closeEvent(event)


class DataSwitcherBase(QWidget):
    """Base user interface to manipulate seismic dataset"""

    index_changed = pyqtSignal(int)
    procset_changed = pyqtSignal(str)
    plot_changed = pyqtSignal(str)
    index_pair_changed = pyqtSignal(int, str)

    def __init__(self, data, sql, plot = 'TX',
                 use_windows=False, interaction_class=None,
                 procset = None, procsets = None,
                 btn_label = 'Click me',
                 window_label = 'SHOTFILES',
                 window_title = 'SWA Viewer',
                 select_plot = True,
                 **kwargs):
        super().__init__()

        self.logger = create_logging(name='GUI')

        #self.data = data
        self.data = data

        if not plot:
            self.plot = 'TX'
        else:
            self.plot = plot
        self.plots = ['TX','FX','spectra','SFR','FK','FV','DC']
        self.select_plot = select_plot

        self.stream = None
        self.canvas0 = FigureCanvas()
        self.canvas = FigureCanvas()

        self.setWindowTitle(window_title)
        self.window_label = window_label
        self._sql = SQL(database=sql)

        self.active_label = 'PLOT INACTIVE'

        # remove raw from processing ???
        if interaction_class:
            procsets = list(procsets)
            procsets = [p for p in procsets if p != 'raw']
            self.active_label = 'PLOT ACTIVE'

        if procsets is None:
            raise ValueError("procsets must not be empty")

        self.procsets = procsets
        if procset not in procsets:
            procset = procsets[-1]
        self.procset = procset

        self.is_grouped = use_windows
        self.all_labels = self._get_all_labels()

        self.interaction_class = interaction_class

        self.group_index = 0
        self.current_index = 0
        self.interactor = None
        self.points = {}
        self.picks = {}

        self.grouped_methods = {}
        for procset in procsets:
            self.grouped_methods[procset] = list(self._sql.get_trafo_labels(procset,use_windows))
        self.methods = self.grouped_methods[procset]

        if not self.methods:
            self.method = "phaseshift"
            self.methods = [self.method]
        else:
            self.method = self.methods[0]

        self.labels = self._get_current_labels()
        self.btn_label = btn_label

        self.kwargs = kwargs

        self.init_ui()
        self.update_display()
        self.canvas.setFocus()

    def init_ui(self):
        """interface design"""

        # canvas
        if self.labels:
            figure0 = self.create_figure(plot = 'geomShort')
            self.canvas0 = FigureCanvas(figure0)

            figure = self.create_figure()
            self.canvas = FigureCanvas(figure)
            self.canvas.setFocusPolicy(Qt.StrongFocus)
            self.canvas.setFocus()

        # layout
        self.layout = QVBoxLayout(self)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setParent(self.canvas)

        self.info_layout = QHBoxLayout()

        label = QLabel(self.window_label)
        label.setStyleSheet("font-size: 14px; color: gray;")
        self.info_layout.addWidget(label)

        # SIN/REP/WIN index
        self.label = QLabel()
        self.label.setStyleSheet("font-size: 14px; color: gray;")

        self.info_layout.addStretch()
        self.info_layout.addWidget(self.label)
        self.layout.addLayout(self.info_layout)

        # Navigation bar
        self.nav_layout = QHBoxLayout()
        self.left_btn = QPushButton()
        self.left_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
        self.left_btn.setFixedSize(40, 40)
        self.right_btn = QPushButton()
        self.right_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
        self.right_btn.setFixedSize(40, 40)

        self.nav_layout.addWidget(self.left_btn)
        self.nav_layout.addWidget(self.right_btn)

        # Dropdown menu to select procset
        if not self.is_grouped:
            self.combo =  self.add_combobox(self.procsets, self.procset)
            self.combo.currentTextChanged.connect(self.set_procset)
            self.nav_layout.addWidget(self.combo)

        # Dropdown menu to select plot
        if not self.is_grouped and self.select_plot:
            self.combo_plots = self.add_combobox(self.plots, self.plot)
            self.combo_plots.currentTextChanged.connect(self.set_plot)
            self.nav_layout.addWidget(self.combo_plots)

        if not self.is_grouped:
            sins = np.unique(np.asarray(self.labels)[:, 0])
            sins = np.char.mod('%d', sins)

            self.combo_select_sin = self.add_combobox(sins,
                                                      str(self.current_index+1),
                                                      'SIN:',
                                                      50)
            self.combo_select_sin.currentTextChanged.connect(self.set_index)
            self.nav_layout.addWidget(self.combo_select_sin)

        # Interaction buttons
        if self.interaction_class:
            self.interact_btn = QPushButton(self.btn_label)
            self.interact_btn.setFixedSize(100, 40)
            self.nav_layout.addWidget(self.interact_btn)

        self.nav_layout.addStretch()
        self.layout.addLayout(self.nav_layout)

        self.left_btn.clicked.connect(self.show_previous_figure)
        self.right_btn.clicked.connect(self.show_next_figure)

        if self.interaction_class:
            self.interact_btn.clicked.connect(self.interact)

        self.layout.addWidget(self.canvas0)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)

    # data base interaction
    def _write_data(self, data, sin, rep, procset, wid=-1):
        """write processed data to database"""
        self._sql.write_data(data, sin, rep, procset, wid)

    def _write_FV(self, data, sin, rep, procset, wid=-1):
        """write FV to database"""
        self._sql.write_FV(data, sin, rep, procset, wid)

    def _get_data(self, sin, rep, procset, wid=-1):
        """get processed data from database"""
        par, amps, recs, sht = self._sql.read_data(sin, rep, procset=procset, wid=wid)
        return par, amps, recs, sht

    def _get_FV(self, sin, rep, procset, wid=-1, method='phaseshift'):
        """get FV data from database"""
        vel, kw, freq, FV = self._sql.read_FV(sin, rep, procset=procset, wid=wid, method=method)
        return vel, kw, freq, FV

    def _get_curve(self, sin, rep, procset, wid=-1, method='phaseshift'):
        """get the curve data"""
        params = {'procset': "'%s'" % procset, 'method': "'%s'" % method,
                  'sin': sin, 'rep': rep, 'wid': wid}
        return self._sql.read_curve(params)

    def _set_data(self, data, sin, rep, procset, wid=-1):
        """set processed data from database to current stream"""

        par, amps, recs, sht = self._get_data(sin, rep, procset=procset, wid=wid)
        amps_ari = amps.values.transpose()
        if not amps.empty:
            data.update_pst(amps_ari, sht, recs, par)
            return True
        else:
            #self.logger.warning('No data.')
            return False

    def _set_FV(self, data, sin, rep, procset, wid=-1, method='phaseshift'):
        """set FV data from database to current stream"""

        vel, kw, freq, FV = self._get_FV(sin, rep, procset=procset, wid=wid, method=method)
        if FV is not None:
            data.update_FV(method, vel, kw, freq, FV)
            return True
        else:
            _, amps, _, _ = self._get_data(sin, rep, procset=procset, wid=wid)
            if not amps.empty:
                self.logger.warning(f'Wave-field transformation not yet performed. Running {method} transformation.')
                data.transform(method = method)
                self._write_FV(data, sin, rep, procset, wid=wid)
                return True
            return False

    # data selection
    def _get_all_labels(self):
        """get all data indices for data selection"""

        labels = []

        if self.is_grouped:
            for sin in self.data.keys():
                for rep in self.data[sin].keys():
                    wids = sorted(self._sql.get_wids(sin, rep, self.procset))
                    labels.append([[sin,rep,x] for x in wids])
        else:
            for sin in self.data.keys():
                for rep in self.data[sin].keys():
                    labels.append([sin,rep,-1])

        return labels

    def _get_current_labels(self):
        """return data indices of current data"""
        return self.all_labels if not self.is_grouped else self.all_labels[self.group_index]

    def select_data(self, sin=1, rep=1):
        """Select one stream object based on source location and shot repetition indices"""

        if sin in self.data.keys():
            if rep in self.data[sin].keys():
                return self.data[sin][rep]

        return None

    def create_figure(self, plot = None, procset = None, **kwargs):
        """plot portions of the stream data"""

        if not self.labels:
            return None

        if procset is None:
            procset = self.procset

        if not plot:
            plot = self.plot

        label = self.labels[self.current_index]

        self.stream = self.select_data(label[0],label[1])
        self.data_exists = self._set_data(self.stream, label[0],label[1], procset, label[2])

        if plot in ['dispersionImage', 'dispersionImageComposite', 'FV', 'FVComposite']:
            FV_flag = self._set_FV(self.stream, label[0],label[1], procset, method=self.method, wid=label[2])
            self.data_exists = self.data_exists & FV_flag

        if plot == 'DC':
            curves = self._get_curve(label[0],label[1], procset, wid=label[2],
                                         method=kwargs.pop('method','phaseshift'))
            if not curves.empty:

                dc_modes = curves['dc_mode'].unique()

                cmap = getattr(plt.cm, 'Greys')
                color = cmap(np.linspace(0, 1, 10))

                fig = Figure(figsize=(8, 8), constrained_layout=True)
                ax = fig.add_subplot(111)

                for dc_mode in dc_modes:
                    curve = curves[curves['dc_mode'] == dc_mode]
                    dc = DispersionCurve()
                    dc.init_data(curve['frequency'], curve['velocity'], curve['error'])
                    ax = dc.plot(show=False,axes = ax, color = color[dc_mode],
                                 edgecolor = 'k', label = f'Mode {dc_mode}', **kwargs)
                return ax.figure

            return None

        if self.data_exists:
            return self.stream.plot(plot, show=False, gui = True, **self.kwargs, **kwargs)

        return None

    def add_combobox(self, sets, set, label=None, size = 90):
        """Add a combo box"""

        combo = QComboBox()
        combo.addItems(sets)
        combo.setFixedSize(size, 40)

        if len(sets) > 0:
            try:
                combo.setCurrentIndex(list(sets).index(set))
            except ValueError:
                combo.setCurrentIndex(sets[0])

        #return dropdown_label, combo
        return combo

    def show_previous_figure(self):
        if not self.labels:
            return
        self.current_index = (self.current_index - 1) % len(self.labels)
        self.update_display()
        self.canvas.setFocus()
        if not self.is_grouped:
            self.index_changed.emit(self.current_index)
            self.combo_select_sin.blockSignals(True)
            self.combo_select_sin.setCurrentIndex(self.current_index)
            self.combo_select_sin.blockSignals(False)

    def show_next_figure(self):
        if not self.labels:
            return
        self.current_index = (self.current_index + 1) % len(self.labels)
        self.update_display()
        self.canvas.setFocus()
        if not self.is_grouped:
            self.index_changed.emit(self.current_index)
            self.combo_select_sin.blockSignals(True)
            self.combo_select_sin.setCurrentIndex(self.current_index)
            self.combo_select_sin.blockSignals(False)

    def interact(self):
        return None

    def create_placeholder(self, canvas):
        """create canvas placeholder"""

        placeholder = QWidget()
        placeholder.setFixedSize(canvas.size())
        self.layout.replaceWidget(canvas, placeholder)
        canvas.setParent(None)
        canvas.deleteLater()
        canvas = placeholder

        return canvas

    def replace_widget(self, canvas, figure):
        """remove widget"""
        self.layout.removeWidget(canvas)
        canvas.setParent(None)
        canvas.deleteLater()
        canvas = FigureCanvas(figure)
        return canvas

    def update_display(self):
        """update the display"""

        # add points from previous session to next plot
        if self.interactor:
            if self.interactor.points:
                self.points[self.current_index] = self.interactor.points

        # enable/disable navigation buttons
        num_figures = len(self.labels)
        is_navigation_enabled = num_figures > 1
        self.left_btn.setEnabled(is_navigation_enabled)
        self.right_btn.setEnabled(is_navigation_enabled)

        figure0 = self.create_figure(plot='geomShort')
        figure = self.create_figure()

        # update label
        if not self.is_grouped:
            label = self.labels[self.current_index]
            if not figure0:
                self.label.setText(f"SIN {label[0]} | REP {label[1]} | No data")
            else:
                self.label.setText(f"SIN {label[0]} | REP {label[1]}")# + " | " + self.active_label)
        else:
            if not figure0:
                self.label.setText(f"No data")
            else:
                label = self.labels[self.current_index]
                self.label.setText(
                    f"SIN {label[0]} | REP {label[1]} | WIN {label[2] + 1}")  # + " | " + self.active_label)

        # return blank canvas if no data exists
        if not figure0:
            self.canvas0 = self.create_placeholder(self.canvas0)
            self.canvas = self.create_placeholder(self.canvas)
            return

        # Replace canvas
        self.canvas0 = self.replace_widget(self.canvas0, figure0)
        self.canvas = self.replace_widget(self.canvas, figure)

        # Reset toolbar
        self.layout.removeWidget(self.toolbar)
        self.toolbar.setParent(None)
        self.toolbar = NavigationToolbar(self.canvas, self.canvas)
        self.layout.addWidget(self.toolbar)

        # Reset canvas
        self.layout.addWidget(self.canvas0)
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()
        self.canvas.setEnabled(self.data_exists)
        self.layout.addWidget(self.canvas)

        # Setup interaction
        self.interactor = None
        if (self.interaction_class is not None) and self.data_exists:

            ax = figure.axes[0]
            points = self.points.get(self.current_index, {})
            picks = self.get_picks()#self.picks.get(self.current_index, {})
            self.interactor = self.interaction_class(ax, points=points, data = self.stream, picks = picks, **self.kwargs)

            #if self.interactor.picks:
            self.points[self.current_index] = self.interactor.points
            self.picks[self.current_index] = self.interactor.picks

    def get_picks(self):
        return self.picks.get(self.current_index, {})

    def set_group(self, group_index):
        """Used when figures are grouped (e.g., in a multi-view setup)."""
        if not self.is_grouped or group_index >= len(self.all_labels):
            return
        self.group_index = group_index
        self.current_index = 0
        self.labels = self._get_current_labels()
        self.update_display()
        self.canvas.setFocus()

    def set_procset(self, procset):
        """set the procset and update figure"""
        self.current_index = 0
        self.procset = procset

        self.procset_changed.emit(procset)
        # self.index_changed.emit(self.current_index)
        #self.index_pair_changed.emit(self.current_index, procset)

        self.all_labels = self._get_all_labels()
        self.labels = self._get_current_labels()
        self.update_display()

        if not self.is_grouped:
            self.combo_select_sin.blockSignals(True)
            self.combo_select_sin.setCurrentIndex(self.current_index)
            self.combo_select_sin.blockSignals(False)

    def set_plot(self, plot):
        """set the plot type and update figure"""
        self.plot = plot
        self.plot_changed.emit(plot)
        self.update_display()

    def set_index(self, current_index):
        """set the sin index and update the figure"""
        _, indices = np.unique(np.asarray(self.labels)[:, 0], return_index=True)
        self.current_index = indices[int(current_index)-1]
        self.index_changed.emit(self.current_index)
        self.update_display()

    def clean(self):
        pass

    def closeEvent(self, event):

        if hasattr(self, 'canvas'):
            self.canvas.setParent(None)
            self.canvas.close()
            del self.canvas
        event.accept()
        plt.close('all')


# TODO: add picking from FK, Radon
# TODO: delete dc from database
# TODO: add subplot with dispersion curves for xmid

class DataSwitcherPick(DataSwitcherBase):
    """Manual dispersion curve picking interface"""

    def __init__(self, data, sql, plot = 'FV', use_windows=False,
                 procset = None, procsets = None,select_plot = True, **kwargs):

        interaction_class = DCPickingInteractive

        super().__init__(data, sql, plot = plot , use_windows=use_windows, interaction_class=interaction_class,
                 procset = procset, procsets = procsets, btn_label = 'Extract Curve', select_plot = select_plot, **kwargs)

    def init_ui(self):
        """interface design"""

        self.layout = QVBoxLayout(self)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.info_layout = QHBoxLayout()

        label = QLabel(self.window_label)
        label.setStyleSheet("font-size: 14px; color: gray;")
        self.info_layout.addWidget(label)

        # SIN/REP/WIN index
        self.label = QLabel()
        self.label.setStyleSheet("font-size: 14px; color: gray;")

        self.info_layout.addStretch()
        self.info_layout.addWidget(self.label)
        self.layout.addLayout(self.info_layout)

        # Navigation bar
        self.nav_layout = QHBoxLayout()
        self.left_btn = QPushButton()
        self.left_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
        self.left_btn.setFixedSize(40, 40)
        self.right_btn = QPushButton()
        self.right_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
        self.right_btn.setFixedSize(40, 40)

        self.nav_layout.addWidget(self.left_btn)
        self.nav_layout.addWidget(self.right_btn)

        if not self.is_grouped:
            # Dropdown menu to select procset
            self.combo = self.add_combobox(self.procsets, self.procset)
            self.combo.currentTextChanged.connect(self.set_procset)
            self.nav_layout.addWidget(self.combo)

        if self.procset is not None:
            self.combo2 = self.add_combobox(self.methods, self.method)
            self.combo2.currentTextChanged.connect(self.set_method)
            self.nav_layout.addWidget(self.combo2)

        if not self.is_grouped:
            _, indices = np.unique(np.asarray(self.labels)[:, 0], return_index=True)
            indices = np.char.mod('%d', indices+1)

            self.combo_select_sin = self.add_combobox(indices,
                                                      str(self.current_index + 1),
                                                      'SIN:',
                                                      50)
            self.combo_select_sin.currentTextChanged.connect(self.set_index)
            self.nav_layout.addWidget(self.combo_select_sin)

        # Interaction buttons
        if self.interaction_class:
            self.interact_btn = QPushButton(self.btn_label)
            self.interact_btn.setFixedSize(100, 40)
            self.nav_layout.addWidget(self.interact_btn)

        self.nav_layout.addStretch()

        self.layout.addLayout(self.nav_layout)
        self.layout.addWidget(self.toolbar)

        self.left_btn.clicked.connect(self.show_previous_figure)
        self.right_btn.clicked.connect(self.show_next_figure)

        if self.interaction_class:
            self.interact_btn.clicked.connect(self.interact)

        # Canvas
        if self.labels:
            figure0 = self.create_figure(plot = 'geomShort')
            self.canvas0 = FigureCanvas(figure0)

            figure = self.create_figure()
            self.canvas = FigureCanvas(figure)
            self.canvas.setFocusPolicy(Qt.StrongFocus)
            self.canvas.setFocus()
        else:
            self.canvas0 = FigureCanvas()
            self.canvas = FigureCanvas()

        self.layout.addWidget(self.canvas0)
        self.layout.addWidget(self.canvas)

    def interact(self):
        if self.interactor:
            self.canvas.setFocus()
            self.interactor.interact()
            self.picks[self.current_index] = self.interactor.picks
            self.write_data_to_sql()
            self.update_display()
            self.canvas.setFocus()

    def get_picks(self):

        label = self.labels[self.current_index]
        params = {'procset': "'%s'" % self.procset, 'method': "'%s'" % self.method,
                  'sin': label[0], 'rep': label[1], 'wid': label[2]}
        curves = self._sql.read_curve(params)

        if not curves.empty:
            picks = {
                mode: {
                    'f': group['frequency'].to_numpy(),
                    'v': group['velocity'].to_numpy()
                }
                for mode, group in curves.groupby('dc_mode')
            }

            return picks

        return {}

    def write_data_to_sql(self):

        label = self.labels[self.current_index]

        if isinstance(type(self.interactor).picks, property):

            # remove from data base
            params = {'procset': "'%s'" % self.procset, 'method': "'%s'" % self.method,
                      'sin': label[0], 'rep': label[1], 'wid': label[2]}
            self._sql.delete_data('curve', params)

            # add to data base
            picks = self.picks[self.current_index]

            for dc_mode in picks.keys():
                dc = {
                    'xmid': self.stream.midpoint,
                    'method': self.method,
                    'dc_mode': dc_mode,
                    'f': picks[dc_mode]['f'],
                    'v': picks[dc_mode]['v'],
                    'err': np.zeros(len(picks[dc_mode]['v']))}

                self._sql.write_curve(dc, label[0], label[1],
                                      procset=self.procset,
                                      wid=label[2],
                                      xmid = self.stream.midpoint)

    def set_method(self, method):

        self.method = method
        self.update_display()


class DataSwitcherFilterSeis(DataSwitcherBase):
    """Manual linear mute interface"""

    def __init__(self, data, sql, plot = '', use_windows=False,
                 procset=None, procsets=None,select_plot = True, **kwargs):

        if plot == 'FK':
            interaction_class = FKFilterInteractive
        elif plot == '':
            interaction_class = SeismoInteractive
        else:
            raise NotImplementedError

        super().__init__(data, sql, plot = plot , use_windows=use_windows, interaction_class=interaction_class,
                 procset = procset, procsets = procsets, btn_label='Filter | Reset', select_plot = select_plot, **kwargs)

    def interact(self):
        """filter data based on FK plot"""
        if self.interactor:
            self.canvas.setFocus()

            points = self.points[self.current_index]
            label = self.labels[self.current_index]

            self._sql.dublicate_data(self.stream, label[0], label[1], label[2])

            # filter data
            if points:
                stream = self.interactor.filter()
                self.points[self.current_index] = {}
            # reset
            else:
                stream = copy.deepcopy(self.stream) #self.select_data(label[0], label[1])
                self._set_data(stream, label[0], label[1], 'tmp', label[2])

            self._write_data(stream, label[0], label[1], self.procset, label[2])

            self.update_display()
            self.canvas.setFocus()

    # remove dublicates
    def clean(self):
        for table in self._sql.get_tables():
            self._sql.delete_data(table, {'procset': "'%s'" % 'tmp'})


class DataSwitcherFilterFK(DataSwitcherBase):
    """Manual FK filter interface"""

    def __init__(self, data, sql, plot = 'FK', use_windows=False,
                 procset=None, procsets=None,select_plot = True, **kwargs):

        interaction_class = FKFilterInteractive
        self.canvas1 = FigureCanvas()
        self.seis_kwargs = {'show_xticks':False,'title':None, 'figsize': (7.2,8)}

        super().__init__(data, sql, plot = plot , use_windows=use_windows, interaction_class=interaction_class,
                 procset = procset, procsets = procsets, btn_label='Filter | Reset',select_plot = select_plot, **kwargs)

    def init_ui(self):
        """interface design"""

        self.layout = QVBoxLayout(self)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.info_layout = QHBoxLayout()

        label = QLabel(self.window_label)
        label.setStyleSheet("font-size: 14px; color: gray;")
        self.info_layout.addWidget(label)

        # SIN/REP/WIN index
        self.label = QLabel()
        self.label.setStyleSheet("font-size: 14px; color: gray;")

        self.info_layout.addStretch()
        self.info_layout.addWidget(self.label)
        self.layout.addLayout(self.info_layout)

        # Navigation bar
        self.nav_layout = QHBoxLayout()
        self.left_btn = QPushButton()
        self.left_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
        self.left_btn.setFixedSize(40, 40)
        self.right_btn = QPushButton()
        self.right_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
        self.right_btn.setFixedSize(40, 40)

        self.nav_layout.addWidget(self.left_btn)
        self.nav_layout.addWidget(self.right_btn)

        if not self.is_grouped:
            self.combo = self.add_combobox(self.procsets, self.procset)
            self.combo.currentTextChanged.connect(self.set_procset)
            self.nav_layout.addWidget(self.combo)

        if not self.is_grouped:
            _,indices = np.unique(np.asarray(self.labels)[:, 0],return_index=True)
            indices = np.char.mod('%d', indices+1)

            self.combo_select_sin = self.add_combobox(indices,
                                                      str(self.current_index+1),
                                                      'SIN:',
                                                      50)
            self.combo_select_sin.currentTextChanged.connect(self.set_index)
            self.nav_layout.addWidget(self.combo_select_sin)

        if self.interaction_class:
            self.interact_btn = QPushButton(self.btn_label)
            self.interact_btn.setFixedSize(100, 40)
            self.nav_layout.addWidget(self.interact_btn)

        self.nav_layout.addStretch()

        self.layout.addLayout(self.nav_layout)
        self.layout.addWidget(self.toolbar)

        self.left_btn.clicked.connect(self.show_previous_figure)
        self.right_btn.clicked.connect(self.show_next_figure)

        if self.interaction_class:
            self.interact_btn.clicked.connect(self.interact)

        # Canvas
        self.fig_layout = QHBoxLayout()

        if self.labels:
            figure0 = self.create_figure(plot = 'geomShort')
            self.canvas0 = FigureCanvas(figure0)

            figure1 = self.create_figure(plot = 'seismogram',**self.seis_kwargs)
            self.canvas1 = FigureCanvas(figure1)

            figure2 = self.create_figure()
            self.canvas = FigureCanvas(figure2)
            self.canvas.setFocusPolicy(Qt.StrongFocus)
            self.canvas.setFocus()

        self.fig_layout.addWidget(self.canvas)
        self.fig_layout.addWidget(self.canvas1)

        self.layout.addWidget(self.canvas0)
        self.layout.addLayout(self.fig_layout)

    def update_display(self):

        # add points from previous session to next plot
        if self.interactor:
            if self.interactor.points:
                self.points[self.current_index] = self.interactor.points

        # enable/disable navigation buttons
        num_figures = len(self.labels)
        is_navigation_enabled = num_figures > 1
        self.left_btn.setEnabled(is_navigation_enabled)
        self.right_btn.setEnabled(is_navigation_enabled)

        figure0 = self.create_figure(plot='geomShort')
        figure1 = self.create_figure(plot='seismogram',**self.seis_kwargs)
        figure = self.create_figure()

        # update label
        if not self.is_grouped:
            label = self.labels[self.current_index]
            if not figure0:
                self.label.setText(f"SIN {label[0]} | REP {label[1]} | No data")
            else:
                self.label.setText(f"SIN {label[0]} | REP {label[1]}")# + " | " + self.active_label)
        else:
            if not figure0:
                self.label.setText(f"No data")
            else:
                label = self.labels[self.current_index]
                self.label.setText(f"SIN {label[0]} | REP {label[1]} | WIN {label[2]+1}")# + " | " + self.active_label)

        #figure0.tight_layout()
        if not figure0:
            self.canvas0 = self.create_placeholder(self.canvas0)
            self.canvas1 = self.create_placeholder(self.canvas1)
            self.canvas = self.create_placeholder(self.canvas)
            return

        # Replace canvas
        self.canvas0 = self.replace_widget(self.canvas0, figure0)
        self.canvas1 = self.replace_widget(self.canvas1, figure1)
        self.canvas = self.replace_widget(self.canvas, figure)

        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()
        self.canvas.setEnabled(self.data_exists)

        self.fig_layout = QHBoxLayout()
        self.fig_layout.addWidget(self.canvas)
        self.fig_layout.addWidget(self.canvas1)
        self.layout.addWidget(self.canvas0)
        self.layout.addLayout(self.fig_layout)

        # Setup interaction
        self.interactor = None
        if (self.interaction_class is not None) and self.data_exists:

            ax = figure.axes[0]
            points = self.points.get(self.current_index, {})
            picks = self.picks.get(self.current_index, {})

            self.interactor = self.interaction_class(ax, points=points, data = self.stream, picks = picks, **self.kwargs)

            #if self.interactor.picks:
            self.points[self.current_index] = self.interactor.points
            self.picks[self.current_index] = self.interactor.picks

    def interact(self):
        """filter data based on FK plot"""
        if self.interactor:
            self.canvas.setFocus()

            points = self.points[self.current_index]
            label = self.labels[self.current_index]
            self._sql.dublicate_data(self.stream, label[0], label[1], label[2])

            # filter data
            if points:
                stream = self.interactor.filter()
                self.points[self.current_index] = {}
                self.kwargs['taper_amps'] = False
            # reset
            else:
                stream = copy.deepcopy(self.stream) #self.select_data(label[0], label[1])
                self._set_data(stream, label[0], label[1], 'tmp', label[2])
                self.kwargs['taper_amps'] = True

            # overwrite in db
            self._write_data(stream, label[0], label[1], self.procset, label[2])

            self.update_display()
            self.canvas.setFocus()

    # remove dublicates
    def clean(self):
        for table in self._sql.get_tables():
            self._sql.delete_data(table, {'procset': "'%s'" % 'tmp'})


class CurveFilter(QWidget):
    """User interface to manually remove points from multiple curves"""

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.keys = list(data.keys())
        self.current_index = 0

        history = []
        for key in self.keys:
            curves = data[key]
            history.append([[np.ones_like(curves[curve_id]['data'].data['vr'], dtype=bool)] for curve_id in curves])
        self.history = history

        self.init_ui()

    def init_ui(self):
        """interface design"""

        # UI Setup
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ax = self.figure.add_subplot(111)
        self.selector = None

        # Buttons
        self.left_btn = QPushButton()
        self.left_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
        self.left_btn.setFixedSize(40, 40)
        self.right_btn = QPushButton()
        self.right_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
        self.right_btn.setFixedSize(40, 40)
        self.undo_btn = QPushButton("Reset")
        self.undo_btn.setFixedSize(80, 40)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.left_btn)
        btn_layout.addWidget(self.right_btn)

        btn_layout.addStretch()

        btn_layout.addWidget(self.undo_btn)

        layout = QVBoxLayout()
        layout.addLayout(btn_layout)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Connect signals
        self.left_btn.clicked.connect(self.show_prev_data)
        self.right_btn.clicked.connect(self.show_next_data)
        self.undo_btn.clicked.connect(self.undo_filter)

        self.update_display()

    def current_mask(self,index):
        """Get the most recent mask for the active curve."""
        return self.history[self.current_index][index][-1].copy()

    def update_display(self):
        """Refresh the plot with current curve and mask."""
        self.ax.clear()

        curves = self.data[self.keys[self.current_index]]

        for i in curves.keys():
            curve = curves[i]['data']
            x, y = curve.data['f'], curve.data['vr']
            mask = self.current_mask(i)

            if i == 0:
                label1 = 'points to keep'
                label2 = 'points to remove'
            else:
                label1 = None
                label2 = None

            curve.plot(axes = self.ax,
                       label = label1,
                         fontsize = 6,
                         show_orig=False)

            self.ax.scatter(x[~mask], y[~mask], color="red", label=label2)

        self.ax.set_title(f"Curves {self.current_index + 1}/{len(self.data)} "
                          f"located at x = {self.keys[self.current_index]}", fontweight = 'bold')
        self.ax.legend()
        self.canvas.draw_idle()

        # Recreate PolygonSelector
        if self.selector:
            self.selector.disconnect_events()
        self.selector = PolygonSelector(self.ax, self.onselect, useblit=True)

    def onselect(self, verts):
        """Handle polygon selection and update mask."""

        curves = self.data[self.keys[self.current_index]]

        for i in curves.keys():
            curve = curves[i]['data']
            x, y = curve.data['f'], curve.data['vr']

            path = Path(verts)
            pts = np.column_stack((x, y))
            inside = path.contains_points(pts)

            # Save current mask state (for undo)
            current = self.current_mask(i)
            self.history[self.current_index][i].append(current.copy())

            # Apply filtering (toggle: points inside polygon are excluded)
            new_mask = current & ~inside
            self.history[self.current_index][i][-1] = new_mask

        self.update_display()

    def undo_filter(self):
        """Undo last filtering operation for current curve."""

        for curve_hist in self.history[self.current_index]:
            if len(curve_hist) > 1:
                curve_hist.pop()  # Remove last mask

        self.update_display()

    def show_next_data(self):
        self.current_index = (self.current_index + 1) % len(self.data)
        self.update_display()

    def show_prev_data(self):
        self.current_index = (self.current_index - 1) % len(self.data)
        self.update_display()

    def remove_points(self):
        """Remove masked points"""
        for j,key in enumerate(self.keys):

            curves = self.data[key]

            for (i,masks) in zip(curves.keys(),self.history[j]):

                curve = curves[i]['data']

                mask = masks[-1]

                curve.markInvalid(mask=~mask)
                curve.dropInvalid(inplace=True)

                self.data[key][i]['data_filt'] = curve

        return self.data