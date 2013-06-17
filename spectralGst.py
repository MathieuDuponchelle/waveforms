from gi.repository import GObject
from gi.repository import Clutter
Clutter.init([])
import cairo

from datetime import datetime
import numpy
import sys

from gi.repository import Gst
from gi.repository import GLib

class WaveformWidget(Clutter.Actor):
    def __init__(self, peaks):
        Clutter.Actor.__init__(self)
        self.set_size(700, 100)
        self.offset = 0

        self.peaks = peaks


        Clutter.Actor.__init__(self)
        self.set_content_scaling_filters(Clutter.ScalingFilter.NEAREST, Clutter.ScalingFilter.NEAREST)
        self.canvas = Clutter.Canvas()
        self.canvas.set_size(700, 100)
        self.set_content(self.canvas)
        self.width = 700
        self.canvas.connect("draw", self.draw_content)
        self.createNumpyArray()
        self.canvas.invalidate()

    # The purpose of this method is to translate our peaks to a numpy array,
    # which will be directly mappable on a cairo surface. It will get called
    # for each zoom action, in a thread.
    def createNumpyArray(self):
        n = datetime.now()
        nbSamples = len(self.peaks[0])

        if (len(self.peaks) > 1):
            samples = (numpy.array(self.peaks[0]) + numpy.array(self.peaks[1])) / 2
        else:
            samples = numpy.array(self.peaks[0])

        nbSamples = len(samples)

        data = numpy.empty([int(nbSamples), 100], numpy.uint32, 'F')

        data[:] = 0

        for x in range(int(nbSamples)):
            val = samples[x]
            top = 50 + val
            bottom = 50 - val
            data[x][bottom:top] = 0xFF2D9FC9

        self.data = data
        self.nbSamples = nbSamples

        print "time to create :", datetime.now() - n

    def draw_content(self, canvas, cr, surf_w, surf_h):
        n = datetime.now()
        data = self.data.flatten('F')

        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, self.nbSamples)

        self.surface = cairo.ImageSurface.create_for_data(
                data, cairo.FORMAT_ARGB32, self.nbSamples, 100, stride)

        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.set_source_surface(self.surface, 0, 0)
        cr.paint()

        cr.set_operator(cairo.OPERATOR_OVER)
        cr.scale(float(self.width) / self.nbSamples, 1.0)
        cr.translate(self.offset * -1, 0)
        cr.set_source_surface(self.surface, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_NEAREST)

        cr.paint()

        print "time to render :", datetime.now() - n

    def _scrollInCb(self, actor, event):
        if event.direction == Clutter.ScrollDirection.UP:
            self.width += 100
        else:
            self.width -= 100

        self.canvas.invalidate()

    def _scrolledCb(self, actor, event):
        if event.keyval == 65361:  #left
            self.offset -= 10
        else:  #right
            self.offset += 10

        if self.offset < 0:
            self.offset = 0

        if self.offset > self.width - 700:
            self.offset = self.width - 700
            print "stop !"

        self.canvas.invalidate()

def buildPipeline():
    pipeline = Gst.parse_launch("uridecodebin uri=file://" + sys.argv[1] + " ! audioconvert ! level interval=100000000 post-messages=true ! fakesink")
    return pipeline

def quit_(stage, pipeline):
    pipeline.set_state(Gst.State.NULL)
    Clutter.main_quit()

peaks = [[], []]

def lol(bus, message, loop):
    global peaks
    s = message.get_structure()
    p = None
    if s:
        p = s.get_value("rms")
    if p:
        p[0] = 10 ** (p[0] / 20) * 100
        p[1] = 10 ** (p[1] / 20) * 100
        peaks[0].append(p[0])
        peaks[1].append(p[1])
    if message.type == Gst.MessageType.EOS:
        loop.quit()

def _quitCb(stage, event):
    Clutter.main_quit()

if __name__ == "__main__":
    GObject.threads_init()

    pipeline = buildPipeline()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    loop = GLib.MainLoop()
    bus.connect("message", lol, loop)
    pipeline.set_state(Gst.State.PLAYING)

    n = datetime.now()
    loop.run()

    pipeline.set_state(Gst.State.NULL)

    print datetime.now() - n

    stage = Clutter.Stage()

    stage.set_size(1500, 600)

    widget = WaveformWidget(peaks)

    stage.connect("scroll-event", widget._scrollInCb)
    stage.connect("key-release-event", widget._scrolledCb)

    stage.add_child(widget)
    widget.set_position(50, 350)
    stage.show_all()
    stage.connect("delete-event", _quitCb)
    Clutter.main()
