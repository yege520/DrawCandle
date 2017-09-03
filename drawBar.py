# !/home/Jack/anaconda2/bin/python
# coding:utf-8
"""
Demonstrate creation of a custom graphic (a candlestick plot)
"""
# import initExample  ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui
import tushare as tu
import time

pg.USE_PYQT5


class DateAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        strns = []
        rng = max(values) - min(values)
        # if rng < 120:
        #    return pg.AxisItem.tickStrings(self, values, scale, spacing)
        if rng < 3600 * 24:
            string = '%H:%M:%S'
            label1 = '%b %d -'
            label2 = ' %b %d, %Y'
        elif rng >= 3600 * 24 and rng < 3600 * 24 * 30:
            string = '%d'
            label1 = '%b - '
            label2 = '%b, %Y'
        elif rng >= 3600 * 24 * 30 and rng < 3600 * 24 * 30 * 12:
            string = '%b'
            label1 = '%Y -'
            label2 = ' %Y'
        elif rng >= 3600 * 24 * 30 * 12:
            string = '%Y'
            label1 = ''
            label2 = ''
        for x in values:
            try:
                strns.append(time.strftime(string, time.localtime(x)))
            except ValueError:  # Windows can't handle dates before 1970
                strns.append('')
        try:
            label = time.strftime(label1, time.localtime(min(values))) + time.strftime(label2, time.localtime(max(values)))
        except ValueError:
            label = ''
        # self.setLabel(text=label)
        return strns


class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        self.setMouseMode(self.RectMode)

    # reimplement right-click to zoom out
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.autoRange()

    def mouseDragEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev)


# Create a subclass of GraphicsObject.
# The only required methods are paint() and boundingRect()
# (see QGraphicsItem documentation)


class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data  # data must have fields: time, open, close, min, max
        self.generatePicture()

    def day2num(self, string):
        timeArray = time.strptime(string, "%Y-%m-%d")
        timestamp = int(time.mktime(timeArray))
        return timestamp

    def generatePicture(self):
        # pre-computing a QPicture object allows paint() to run much more quickly,
        # rather than re-drawing the shapes every time.
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('w'))
        ################################################################################
        w = (self.day2num(self.data[1][0]) - self.day2num(self.data[0][0])) / 3
        ################################################################################
        for (t, open, close, high, low, vol, code) in self.data:
            t = self.day2num(str(t))
            p.drawLine(QtCore.QPointF(t, high), QtCore.QPointF(t, low))
            if open > close:
                p.setBrush(pg.mkBrush('g'))
            else:
                p.setBrush(pg.mkBrush('r'))
            p.drawRect(QtCore.QRectF(t - w, open, w * 2, close - open))
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        # boundingRect _must_ indicate the entire area that will be drawn on
        # or else we will get artifacts and possibly crashing.
        # (in this case, QPicture does all the work of computing the bouning rect for us)
        return QtCore.QRectF(self.picture.boundingRect())


data = tu.get_k_data('600606', start='2017-01-01', end='2017-09-01')
data.set_index('date')
temp = []
lt = ()
for i in range(len(data)):
    lt = tuple(data.iloc[i])
    temp.append(lt)

item = CandlestickItem(temp)
############################################################
# ndays = 146
app = pg.mkQApp()
# pg.dbg()
axis = DateAxis(orientation='bottom')
sn = temp[0][6]
dt = temp[-1][0]
labelStyle = {'color': '#FFF', 'font-size': '12pt'}
axis.setLabel(sn, units=dt, **labelStyle)
vb = CustomViewBox()
p1 = pg.PlotWidget(viewBox=vb,
                   axisItems={'bottom': axis},
                   enableMenu=False,
                   )
# dates = np.arange(ndays) * (3600 * 24 * 356)
# pw = pg.plot(x=dates, y=np.array(data['close']))
###################################################

# cross hair
vLine = pg.InfiniteLine(angle=90, movable=False)
hLine = pg.InfiniteLine(angle=0, movable=False)
p1.addItem(vLine, ignoreBounds=True)
p1.addItem(hLine, ignoreBounds=True)

vb_ =vb

p1.show()
p1.addItem(item)
p1.setWindowTitle('Stock Market Monitor: ' + sn)
#
def mouseMoved(evt):
    pos = evt[0]  # using signal proxy turns original arguments into a tuple
    if p1.sceneBoundingRect().contains(pos):
        mousePoint = vb_.mapSceneToView(pos)
        index = int(mousePoint.x())
        if index > 0 and index < len(temp):
            print mousePoint.x(), temp[index][2], temp[index][5]
            # label.setText("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y1=%0.1f</span>,   <span style='color: green'>y2=%0.1f</span>" % (mousePoint.x(), temp[index][2], temp[index][5]))
        vLine.setPos(mousePoint.x())
        hLine.setPos(mousePoint.y())


proxy = pg.SignalProxy(p1.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)

# Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
