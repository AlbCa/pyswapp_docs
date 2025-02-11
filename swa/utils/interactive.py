import matplotlib
#matplotlib.use("Qt5Agg")

import warnings
import numbers
from collections.abc import Iterable

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpltPath
from matplotlib.backend_bases import MouseEvent

from .physics import lorentzian_err

# TODO load database and define functions to change data!

class DraggablePoints:
    """
    class to draw draggable points
    base from https://github.com/yuma-m/matplotlib-draggable-plot/blob/master/draggable_plot.py
    """

    def __init__(self, ax,kwargs=None):

        self._line = None

        self.ax = ax
        self.canvas = self.ax.figure.canvas

        self.distance_threshold = 5
        self._dragging_point = None
        self._points = {}
        #self._points_list = []

        if kwargs is None:
            kwargs = dict(color='r', linestyle='--', linewidth=1, markersize=7, marker='x')
        self._kwargs = kwargs #{**kwargs}

        self._init_plot()

    def _init_plot(self):
        """matplotlib event connections"""

        self.canvas.mpl_connect('button_press_event', self._on_click)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)

    def _update_plot(self):
        """update the figure"""

        if not self._points:
            self._line.set_data([], [])
        else:
            x, y = zip(*sorted(self._points.items()))

            if not self._line:
                self._line, = self.ax.plot(x, y, **self._kwargs)

            else:
                self._line.set_data(x, y)

        self.canvas.draw_idle()

    # def _update_points_list(self):
    #     """update the point list"""
    #
    #     x, y = zip(*sorted(self._points.items()))
    #     points_list = []
    #     for i in range(len(x)):
    #         points_list.append((x[i], y[i]))
    #     self._points_list = points_list

    def _add_point(self, x, y=None):
        """add a new point"""
        if isinstance(x, MouseEvent):
            x, y = float(x.xdata), float(x.ydata)

        self._points[x] = y
        return x, y

    def _remove_point(self, x, _):
        """remove a point"""
        if x in self._points:
            self._points.pop(x)

    def _find_neighbor_point(self, event):
        """ Find point around mouse position"""

        if self._points:
            # poinst list
            points = []
            for x, y in self._points.items():
                if isinstance(y, Iterable):
                    y = y[0]
                points.append((x, y))

            mouse_pos = np.array([event.xdata,event.ydata])

            # get nearest point
            distance = np.sum((np.asarray(points) - mouse_pos) ** 2, axis=1)
            nearest_id = np.argmin(distance)
            nearest_point = (points[nearest_id][0],points[nearest_id][1])

            if distance[nearest_id] < self.distance_threshold:
                return nearest_point
            else:
                return None
        else:
            return None

    def _on_click(self, event):
        u""" callback method for mouse click event
        :type event: MouseEvent
        """
        # left click
        if event.button == 1 and event.inaxes in [self.ax]:
            point = self._find_neighbor_point(event)
            if point:
                self._dragging_point = point
            else:
                self._add_point(event)
            #self._update_points_list()
            self._update_plot()

        # right click
        elif event.button == 3 and event.inaxes in [self.ax]:
            point = self._find_neighbor_point(event)
            if point:
                self._remove_point(*point)
                #self._update_points_list()
                self._update_plot()

    def _on_release(self, event):
        u""" callback method for mouse release event
        :type event: MouseEvent
        """
        if event.button == 1 and event.inaxes in [self.ax] and self._dragging_point:
            self._dragging_point = None
            #self._update_points_list()
            self._update_plot()

    def _on_motion(self, event):
        u""" callback method for mouse motion event
        :type event: MouseEvent
        """
        if not self._dragging_point:
            return
        if event.xdata is None or event.ydata is None:
            return
        self._remove_point(*self._dragging_point)
        self._dragging_point = self._add_point(event)
        self._update_plot()

    @property
    def points(self):
        return self._points


class SeismoInteractive(DraggablePoints):

    def __init__(self, ax, receiver, kwargs=None):

        if kwargs is None:
            kwargs = dict(color='k', linestyle='--', linewidth=2, alpha=0.5, markersize=5, marker='o')
        else:
            kwargs.setdefault('color','r')
            kwargs.setdefault('linestyle', '--')
            kwargs.setdefault('linewidth', 1)
            kwargs.setdefault('markersize', 7)
            kwargs.setdefault('marker', 'x')

        super().__init__(ax,kwargs)

        self.receiver = receiver
        self.x = np.arange(0,len(receiver),1)
        self._init_param()
        self.canvas.mpl_connect('key_press_event', self._on_key)

    def _init_param(self):

        self._key = 't'
        self._terminate = False
        self._reset = False
        self._reset_last = False
        self.slope = None
        self.tbox = None

    def _add_point(self, x, y=None):
        if isinstance(x, MouseEvent):
            x, y = float(x.xdata), float(x.ydata)

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

            x1 = self.receiver[round(idx[0])]
            x2 = self.receiver[round(idx[1])]

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
            self._reset = True
            plt.close()

        if event.key == 'ctrl+z':
            #print(f'You pressed {event.key}. Reset last step')
            self._reset_last = True
            plt.close()

        if event.key == 't':
            #print(f'You pressed {event.key}.')
            self._key = 't'
            self.ax.set_title('Top mute active', fontweight='bold')
            self.canvas.draw_idle()

        if event.key == 'b':
            #print(f'You pressed {event.key}.')
            self._key = 'b'
            self.ax.set_title('Bottom mute active', fontweight='bold')
            self.canvas.draw_idle()

        if event.key == 'v':
            #print(f'You pressed {event.key}.')
            self._estimate_velocity()
            self.ax.set_title('Velocity estimation', fontweight='bold')
            self.canvas.draw_idle()

            if self.tbox is not None:
                self.tbox.remove()

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

class FKFilterInteractive(DraggablePoints):

    def __init__(self, ax, kwargs=None):

        if kwargs is None:
            kwargs = dict(color='r', linestyle='--', linewidth=1, markersize=7, marker='x')
        else:
            kwargs.setdefault('color','r')
            kwargs.setdefault('linestyle', '--')
            kwargs.setdefault('linewidth', 1)
            kwargs.setdefault('markersize', 7)
            kwargs.setdefault('marker', 'x')

        super().__init__(ax,kwargs)

        self._init_param()
        self.canvas.mpl_connect('key_press_event', self._on_key)

    def _init_param(self):
        """initialize some parameters"""

        self._key = 't'
        self._terminate = False
        self._reset = False
        self._reset_last = False

    def _on_key(self, event):
        """keyboard events"""
        if event.key == 'e':
            #print(f'You pressed {event.key}. Process stopped.')
            self._terminate = True
            plt.close()

        if event.key == 't':
            #print(f'You pressed {event.key}.')
            self._key = 't'
            self.ax.set_title('Top filter active', fontweight='bold')
            self.canvas.draw_idle()

        if event.key == 'b':
            #print(f'You pressed {event.key}.')
            self._key = 'b'
            self.ax.set_title('Bottom filter active', fontweight='bold')
            self.canvas.draw_idle()

    @property
    def key(self):
        return self._key

    @property
    def terminate(self):
        return self._terminate

class DCPickingInteractive(DraggablePoints):
    """class for drawing boundaries for dispersion curve extraction"""

    # TODO: save boundary for next picking?

    def __init__(self, ax, freq=None, vel=None ,power=None, offsets=None, err = 'lor'):

        super().__init__(ax)

        #self.canvas = self.ax.figure.canvas

        # data
        self._freq = freq
        self._vel = vel
        self._power = power
        self._offsets = offsets
        self._err = err

        self._init_param()
        self._init_plot()

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
        self._points_prior = {}

        self._pick_line = None
        self._line = None
        self._upper_bound_line = None
        self._lower_bound_line = None

    def _update_plot(self):
        """update plot after event"""

        if not self._points:
            self._line.set_data([], [])
            self._upper_bound_line.set_data([], [])
            self._lower_bound_line.set_data([], [])

            if (self._picks) and (not self._reset):
                self._pick_line, = self.ax.plot(self._picks[self._mode]['f'],
                                                self._picks[self._mode]['v'],
                                                markeredgecolor='k',
                                                marker="s",
                                                markersize=5,
                                                color='white',
                                                linewidth=0)
            elif self._reset:
                self._pick_line.set_data([], [])

        else:
            x, y = zip(*sorted(self._points.items()))

            y_data = [];
            y_up = [];
            y_lo = []
            for i in range(len(y)):
                y_data.append(y[i][0])
                y_lo.append(y[i][2])
                y_up.append(y[i][1])

            # Add new plot
            if self._line is None:
                # plot clicked points
                self._line, = self.ax.plot(x,
                                           y_data,
                                           markeredgecolor='k',
                                           marker="o",
                                           markersize=7,
                                           color='white',
                                           linewidth=0)
                # plot boundaries
                marker_style = dict(color="k", marker="o", markersize=3, linestyle='--', linewidth=0.8)
                self._upper_bound_line, = self.ax.plot(x, y_lo, **marker_style)
                self._lower_bound_line, = self.ax.plot(x, y_up, **marker_style)

            # update current plot
            else:
                self._line.set_data(x, y_data)
                self._upper_bound_line.set_data(x, y_lo)
                self._lower_bound_line.set_data(x, y_up)

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
                err = lorentzian_err(self._offsets, y, x, a=self._boundary_strength)
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
        self._polygons[self._mode] = polygon

    def _extract_dccurve(self):
        """extract the dispersion curve based on the maximum dispersive energy within the drawn boundaries"""

        if (self._freq is not None) and (self._vel is not None) and (self._power is not None):

            fgrid, vgrid = np.meshgrid(self._freq, self._vel)
            polygon = self._polygons[self._mode]

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
            increment = 0.1
            if event.button == 'up':
                self._boundary_strength += increment
            else:
                if self._boundary_strength - increment > 0:
                    self._boundary_strength -= increment

            #print(event.button, event.step,self._boundary_strength)

            self._update_bounds()
            self._update_plot()

    def _on_key(self, event):
        """keyboard events"""

        if event.key.isnumeric():
            #print(f'Picking F{event.key}.')

            mode = int(event.key)

            if self._mode != mode:

                self._mode = mode

                # reset plot
                self._points = {}
                self._update_plot()

        if event.key == 'p':
            #print(f'Extracting F{self._mode} DC curve.')
            self._extract_dccurve()

            # reset plot
            self._points = {}
            self._update_plot()

        if event.key == 'r':
            #print(f'Reset.')

            self._reset = True

            # reset plot
            self._polygons.pop(self._mode)
            self._picks.pop(self._mode)
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

