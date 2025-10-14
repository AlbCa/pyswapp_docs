from contextlib import suppress

import warnings
import numbers
from collections.abc import Iterable

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpltPath
from matplotlib.backend_bases import MouseEvent
from scipy.stats import alpha

from .physics import lorentzian_err

class DraggablePoints:
    def __init__(self, ax, points=None, **kwargs):
        self.ax = ax
        self.canvas = self.ax.figure.canvas

        self.distance_threshold = 0.1  # Threshold in data coords (adjust if needed)
        self._dragging_point = None
        self._points = {}  # Dict: x -> y
        self._line = None

        color = kwargs.pop('color', 'r')
        ls = kwargs.pop('linestyle', '--')
        lw = kwargs.pop('linewidth', 1)
        ms = kwargs.pop('markersize', 7)
        marker = kwargs.pop('marker', 'x')
        self._plot_kwargs = {'color':color,'linestyle':ls,'linewidth':lw, 'markersize':ms,'marker':marker}

        self._kwargs = kwargs

        if points:
            for x, y in points.items():
                self._points[x] = y

            try:
                self.ax.lines[-1].remove()
            except IndexError:
                pass

            self._update_plot()

        self._init_plot()

    def _init_plot(self):
        """Connect matplotlib events."""
        self.canvas.mpl_connect('button_press_event', self._on_click)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)

    def _update_plot(self,kwargs=None):
        """Update line data and redraw."""

        if self._line and (self._line in self.ax.lines):
            self._line.remove()  # Remove the old line artist
            self._line = None

        if self._points:

            x, y = zip(*sorted(self._points.items()))
            self._line, = self.ax.plot(x, y, **self._plot_kwargs)

        self.canvas.draw_idle()

    def _add_point(self, x, y=None):
        """add a new point"""
        # if isinstance(x, MouseEvent):
        #     x, y = float(x.xdata), float(x.ydata)

        self._points[x] = y
        return x, y

    def _remove_point(self, x, _):
        """Remove a point by its x coordinate."""
        if x in self._points:
            self._points.pop(x)

    def _find_neighbor_point(self, event):
        """ Find point around mouse position"""

        if not self._points or event.xdata is None or event.ydata is None:
            return None

        if self._points:
            # poinst list
            points = []
            for x, y in self._points.items():
                if isinstance(y, Iterable):
                    y = y[0]
                points.append((x, y))

            mouse_pos = np.array([event.xdata,event.ydata])

            # get nearest point
            distances = np.sum((np.asarray(points) - mouse_pos) ** 2, axis=1)
            nearest_idx = np.argmin(distances)

            if distances[nearest_idx] < self.distance_threshold:
                nearest_point = (points[nearest_idx][0], points[nearest_idx][1])
                return nearest_point
            else:
                return None


    def _on_click(self, event):
        if event.inaxes != self.ax:
            return

        # Left click: start drag or add point
        if event.button == 1:
            point = self._find_neighbor_point(event)
            if point:
                self._dragging_point = point
            else:
                self._add_point(event.xdata, event.ydata)
                self._update_plot()

        # Right click: remove point
        elif event.button == 3:
            point = self._find_neighbor_point(event)
            if point:
                self._remove_point(*point)
                self._update_plot()

    def _on_release(self, event):
        if event.button == 1 and self._dragging_point:
            self._dragging_point = None
            self._update_plot()

    def _on_motion(self, event):
        if not self._dragging_point or event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        self._remove_point(*self._dragging_point)
        self._dragging_point = self._add_point(event.xdata, event.ydata)
        self._update_plot()

    @property
    def points(self):
        return self._points


class SeismoInteractive(DraggablePoints):

    def __init__(self, ax, receiver = None, points=None, data  = None, picks = None, **kwargs):

        super().__init__(ax,points,**kwargs)

        self.data = data

        if receiver is None:
            receiver = self.data.receiver

        self.receiver = receiver
        self.x = np.arange(0,len(self.receiver),1)
        self._init_param()
        self.canvas.mpl_connect('key_press_event', self._on_key)

    def _init_param(self):

        self._key = 't'
        self._terminate = False
        self._reset = False
        self._reset_last = False
        self.slope = None
        self.tbox = None
        self.plot_slope = None

    def _add_point(self, x, y=None):

        # if isinstance(x, MouseEvent):
        #     x, y = float(x.xdata), float(x.ydata)

        # snap to data
        indx = np.searchsorted(self.x, [x])[0]

        try:
            x = self.x[indx]
        except IndexError:
            if indx > 0:
                x = self.x[indx-1]
            else:
                x = self.x[0]

        if len(self._points) == 2:
            id = sorted(self._points.keys())

            lxo = id[0]
            rxo = id[1]
            if x <= lxo:
                self._points.pop(lxo)
            else:
                self._points.pop(rxo)

        self._points[x] = y
        return x, y

    def _estimate_velocity(self):
        """calculate the slope"""

        if (len(self._points) == 2) & (self.receiver is not None):
            idx, t = zip(*sorted(self._points.items()))

            x1 = self.receiver[int(idx[0])]
            x2 = self.receiver[int(idx[1])]

            t1 = t[0]
            t2 = t[1]

            self.slope = (t2-t1)/(x2-x1)

            props = dict(boxstyle='round', facecolor='white', alpha=0.5)
            self.tbox = self.ax.text(np.mean(idx), np.mean(t),f'v={round(1/self.slope,2)} m/s', bbox = props)

    def _on_key(self, event):

        if event.key == 'enter':
            plt.close()

        if event.key == 'e':
            #print(f'You pressed {event.key}. Process stopped.')
            self._terminate = True
            plt.close()

        if event.key == 'r':
            #print(f'You pressed {event.key}. Reset mute')
            if self.tbox is not None:
                self.tbox.remove()

            self._reset = True
            plt.close()

        if event.key == 'ctrl+z':
            #print(f'You pressed {event.key}. Reset last step')
            self._reset_last = True
            plt.close()

        if event.key == 't':
            #print(f'You pressed {event.key}.')
            if self.tbox is not None:
                with suppress(ValueError):
                    self.tbox.remove()

            self._key = 't'

            self.ax.set_title('Top mute active', fontweight='bold')
            self.canvas.draw_idle()

        if event.key == 'b':
            #print(f'You pressed {event.key}.')
            if self.tbox is not None:
                with suppress(ValueError):
                    self.tbox.remove()

            self._key = 'b'

            self.ax.set_title('Bottom mute active', fontweight='bold')
            self.canvas.draw_idle()

        if event.key == 'v':
            #print(f'You pressed {event.key}.')
            if self.tbox is not None:
                with suppress(ValueError):
                    self.tbox.remove()

            self._estimate_velocity()
            self.ax.set_title('Velocity estimation', fontweight='bold')
            self.canvas.draw_idle()

    def filter(self):

        kwargs = self._kwargs
        taper_type = kwargs.pop('taper_type', 'tukey')
        taper = kwargs.pop('tapering', 'mild')

        if self._points:
            self.data.linear_mute(self._points, key=self._key, taper = taper, taper_type = taper_type)

            # reset plot
            self._points = {}
            self._update_plot()

        return self.data

    @property
    def key(self):
        return self._key

    @property
    def terminate(self):
        return self._terminate

    @property
    def reset(self):
        return self._reset

    @property
    def reset_last(self):
        return self._reset_last

    @property
    def picks(self):
        return self._points

class FKFilterInteractive(DraggablePoints):

    def __init__(self, ax, points=None, data  = None, picks = None, **kwargs):

        super().__init__(ax, points, **kwargs)

        self.data = data
        self._init_param()
        self.canvas.mpl_connect('key_press_event', self._on_key)

    def _init_param(self):
        """initialize some parameters"""

        self._key = 't'
        self._terminate = False
        # self._reset = False
        # self._reset_last = False

    def filter(self):

        kwargs = self._kwargs
        taper_length = kwargs.pop('taper_length', 5)

        if self._points:
            self.data.fk_filter_from_pick_ui(self._points, key = self._key, taper_length = taper_length)

            # reset plot
            self._points = {}
            self._update_plot()

        return self.data

    def _on_key(self, event):
        """keyboard events"""
        if event.key == 'e':
            #print(f'You pressed {event.key}. Process stopped.')
            self._terminate = True
            plt.close()

        if event.key == 't':
            #print(f'You pressed {event.key}.')
            self._key = 't'
            self.ax.set_title('Top filter active', fontweight='bold') # change to textbox
            self.canvas.draw_idle()

        if event.key == 'b':
            #print(f'You pressed {event.key}.')
            self._key = 'b'
            self.ax.set_title('Bottom filter active', fontweight='bold') # change to textbox
            self.canvas.draw_idle()


    @property
    def key(self):
        return self._key

    @property
    def terminate(self):
        return self._terminate

    @property
    def picks(self):
        return self._points

class DCPickingInteractive(DraggablePoints):
    """class for drawing boundaries for dispersion curve extraction"""

    def __init__(self, ax, points = None,
                 data = None, freq=None, vel=None, power=None, offsets=None, err = 'lor', picks = None, **kwargs):

        super().__init__(ax)

        # data
        if data:
            self._freq = data.frequency
            self._vel = data.velocity
            self._power = data.dispersive_energy
            self._offsets = data.offset
        else:
            self._freq = freq
            self._vel = vel
            self._power = power
            self._offsets = offsets

        self._err = err

        self._init_param()
        self._init_plot()

        if picks is not None:
            self._picks = picks
            self._update_plot(**kwargs)

        elif points:
            for x, y in points.items():
                self._points[x] = y

            for line in ax.lines:
                line.remove()

            self._update_polygons()
            self._update_plot()

    def _init_plot(self):
        """event connections"""

        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('button_press_event', self._on_click)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.canvas.mpl_connect('key_press_event', self._on_key)
        self.canvas.mpl_connect('scroll_event', self._on_scroll)

    def _init_param(self):
        """initialize some parameters"""

        # picks
        self._reset = False
        self._mode = 0
        self._polygons = {}
        self._picks = {}
        self._ppid = 0
        self._picks_prior = {}

        # boundary
        self._boundary_strength = 0.3
        self._minVelErr = 20
        self._boundary_min = self._minVelErr
        self._points_prior = {}

        # lines
        self._pick_lines = {}
        self._line = None
        self._upper_bound_line = None
        self._lower_bound_line = None

    def _update_plot(self, **kwargs):
        """update plot after event"""

        show_legend = kwargs.pop('show_legend',True)
        marker_size = kwargs.pop('markersize',3)
        alpha = kwargs.pop('alpha',1)

        # plot picked dispersion curve
        if not self._points:

            cmap = getattr(plt.cm, 'Greys')
            color = cmap(np.linspace(0, 1, 10))

            # Remove existing pick line if present
            if self._mode in self._pick_lines:
                self._pick_lines[self._mode].remove()
                self._pick_lines.pop(self._mode)

                if self._pick_lines:
                    self.ax.legend(loc='upper right')
                else:
                    try:
                        self.ax.get_legend().remove()
                    except AttributeError:
                        pass

            # Clear existing lines
            if self._line:
                self._line.set_data([], [])
            if self._upper_bound_line:
                self._upper_bound_line.set_data([], [])
            if self._lower_bound_line:
                self._lower_bound_line.set_data([], [])

            # Plot picks if available
            for self._mode in self._picks:
                if self._mode not in self._pick_lines and not self._reset:
                    picks = self._picks[self._mode]
                    pick_line, = self.ax.plot(
                        picks['f'],
                        picks['v'],
                        marker="s",
                        markersize=marker_size,
                        markeredgecolor='k',
                        color=color[self._mode],
                        linewidth=0,
                        alpha = alpha,
                        label=f'Mode {self._mode}'
                    )
                    if show_legend:
                        self.ax.legend(loc='upper right')
                    self._pick_lines[self._mode] = pick_line

        # draw boundary
        else:
            x, raw_y = zip(*sorted(self._points.items()))
            y_data = [val[0] for val in raw_y]
            y_lower = [val[2] for val in raw_y]
            y_upper = [val[1] for val in raw_y]

            if self._line is None:
                # Initial plot
                self._line, = self.ax.plot(
                    x, y_data, marker="o", markersize=7,
                    markeredgecolor='k', color='white', linewidth=0
                )
                marker_style = dict(color="k", marker="o", markersize=3, linestyle='--', linewidth=0.8)
                self._upper_bound_line, = self.ax.plot(x, y_lower, **marker_style)
                self._lower_bound_line, = self.ax.plot(x, y_upper, **marker_style)
            else:
                # Update plot data
                self._line.set_data(x, y_data)
                self._upper_bound_line.set_data(x, y_lower)
                self._lower_bound_line.set_data(x, y_upper)

        self.canvas.draw_idle()

    def _add_point(self, x, y=None):
        """add new point with upper and lower boundary"""

        if isinstance(x, MouseEvent):
            x, y = float(x.xdata), float(x.ydata)

        if (self._err == 'lor') and (self._offsets is not None):
            err = lorentzian_err(self._offsets,y, x)
        elif isinstance(self._err, numbers.Number):
            err = self._err
        else:
            err = 10

        self._points[x] = [y, y + err, y - err]

        return x, y

    def _update_bounds(self):
        """update boundaries"""

        xs, ys = zip(*sorted(self._points.items()))

        for i in range(len(ys)):
            x = xs[i]
            y = ys[i][0]
            if (self._err == 'lor') and (self._offsets is not None):
                err = lorentzian_err(self._offsets, y, x, a=self._boundary_strength,minvelerr= self._boundary_min)
            elif isinstance(self._err, numbers.Number):
                err = self._err*self._boundary_strength
            else:
                err = 10*self._boundary_strength

            self._points[x] = [y, y + err, y - err]

    def _update_polygons(self):
        """update polygons after event"""

        x, ys = zip(*sorted(self._points.items()))
        y = [];
        y_lo = [];
        y_up = []
        for i in range(len(ys)):
            y.append(ys[i][0])
            y_lo.append(ys[i][2])
            y_up.append(ys[i][1])

        bound_lo = np.vstack((np.array(x), np.array(y_lo))).T
        bound_up = np.flipud(np.vstack((np.array(x), np.array(y_up))).T)
        polygon = np.vstack((bound_up, bound_lo))
        self._polygons = polygon

    def _extract_dccurve(self):
        """extract the dispersion curve based on the maximum dispersive energy within the drawn boundaries"""

        if (self._freq is not None) and (self._vel is not None) and (self._power is not None):

            fgrid, vgrid = np.meshgrid(self._freq, self._vel)
            polygon = self._polygons

            path = mpltPath.Path(polygon)
            flags = path.contains_points(np.hstack((fgrid.flatten()[:, np.newaxis],
                                                    vgrid.flatten()[:, np.newaxis])))
            flags = flags.reshape(self._power.shape)

            row_cols = np.where(flags[:, ])
            power_mask = np.ma.masked_array(self._power, mask=~flags, fill_value=0)
            peaks_idx = np.argmax(power_mask, axis=0)

            idx = np.unique(row_cols[1])
            freq_pick = self._freq[idx]
            vel_pick = self._vel[peaks_idx][idx]

            self._picks[self._mode] = {'f':freq_pick,'v':vel_pick}

            # visualize prior picks (needs to be stored somewhere)
            self._picks_prior[self._ppid] = {'f':freq_pick,'v':vel_pick}
            self._ppid += 1
            if self._ppid < 5:
                self._ppid += 1
            else:
                self._ppid = 0
        else:
            warnings.warn("Dispersive energy, frequency and velocity ranges"
                          " must be provided for dispersion curve extraction.")

    def interact(self):
        """extract dispersion curve within boundary"""

        if self._points:
            self._extract_dccurve()

            # reset plot
            self._points = {}
            self._update_plot()

    def _on_click(self, event):
        """add/remove points on click"""

        # left click
        if event.button == 1 and event.inaxes in [self.ax]:
            point = self._find_neighbor_point(event)
            if point:
                self._dragging_point = point
            else:
                self._add_point(event)
            self._update_plot()

            if len(self._points) > 1:
                self._update_polygons()

        # right click
        elif event.button == 3 and event.inaxes in [self.ax]:
            point = self._find_neighbor_point(event)
            # clicking on point calls point deletion
            if point:
                self._remove_point(*point)
                self._update_plot()

    def _on_scroll(self,event):
        """tighten or loosen boundary on mouse scroll"""

        if len(self._points) > 0:
            increment_strength = 0.05
            increment_min = 0.5
            if event.button == 'up':

                if self._boundary_strength <= 1:
                    self._boundary_strength += increment_strength
                elif self._boundary_min > 1 + increment_min:
                    self._boundary_min -= increment_min
            else:
                if self._boundary_strength > increment_strength:
                    self._boundary_strength -= increment_strength

                if self._boundary_min < self._minVelErr:
                    self._boundary_min += increment_min

            self._update_bounds()
            self._update_polygons()
            self._update_plot()

    def _on_key(self, event):
        """keyboard events"""

        if event.key.isnumeric():

            mode = int(event.key)
            if self._mode != mode:
                self._mode = mode

        if event.key == 'p':
            #print(f'Extracting F{self._mode} DC curve.')

            if self._points:
                self._extract_dccurve()

                # reset plot
                self._points = {}
                self._update_plot()

        if event.key == 'r':
            #print(f'Reset.')

            self._reset = True

            # reset plot
            if self._mode in self._picks.keys():
                self._picks.pop(self._mode)

            self._polygons = {}
            self._points = {}
            self._update_plot()

            self._reset = False

        if event.key == 'd':
            #print(f'Delete boundary.')

            # reset plot
            self._points = {}
            self._update_plot()

        if event.key == 'e':
            #print(f'You pressed {event.key}. Process stopped.')
            self._terminate = True
            plt.close()

    @property
    def polygons(self):
        return self._polygons

    @property
    def picks(self):
        return self._picks

