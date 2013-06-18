#include <Python.h>
#include <stdio.h>
#include <cairo.h>
#include </usr/include/pycairo/pycairo.h>

static Pycairo_CAPI_t *Pycairo_CAPI;

/*
 * Function to be called from Python
 */
static PyObject* py_fill_surface(PyObject* self, PyObject* args)
{
  char *s = "Hello from C!";
  PyObject *samples;
  PyObject *sampleObj;
  int length, i;
  double sample;
  cairo_surface_t *surface;
  cairo_t *ctx;
  int width, height;
  float pixelsPerSample;
  float currentPixel;
  int samplesInAccum;
  float x = 0.;
  float lastX = 0.;
  double accum;
  double lastAccum = 0.;

  PyArg_ParseTuple(args, "O!ii", &PyList_Type, &samples, &width, &height);
  length = PyList_Size(samples);

  surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, 700, 100);

  ctx = cairo_create(surface);

  cairo_set_line_width(ctx, 0.5);
  cairo_move_to(ctx, 0, height);

  pixelsPerSample = width / (float) length;
  currentPixel = 0.;
  samplesInAccum = 0;
  accum = 0.;

  for (i = 0; i < length; i++)
    {
      sampleObj = PyList_GetItem(samples, i);
      sample = PyFloat_AsDouble(sampleObj);
      currentPixel += pixelsPerSample;
      samplesInAccum += 1;
      accum += sample;
      if (currentPixel > 1.0)
	{
	  accum /= samplesInAccum;
	  cairo_move_to(ctx, lastX, 50 - lastAccum);
	  cairo_line_to(ctx, x, 50 - accum);
	  cairo_move_to(ctx, lastX, 50 + lastAccum);
	  cairo_line_to(ctx, x, 50 + accum);
	  lastAccum = accum;
	  accum = 0;
	  currentPixel -= 1.0;
	  samplesInAccum = 0;
	  lastX = x;
	}
      x += pixelsPerSample;
    }

  cairo_stroke(ctx);

  return PycairoSurface_FromSurface(surface, NULL);
}

/*
 * Bind Python function names to our C functions
 */
static PyMethodDef renderer_methods[] = {
  {"fill_surface", py_fill_surface, METH_VARARGS},
  {NULL, NULL}
};

/*
 * Python calls this to let us initialize our module
 */
void initrenderer()
{
  Pycairo_IMPORT;
  (void) Py_InitModule("renderer", renderer_methods);
}
