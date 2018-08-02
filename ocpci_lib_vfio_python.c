#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <stdint.h>
#include <Python.h>
#include <structmember.h>

#include "ocpci_lib_vfio.h"

typedef struct {
  PyObject_HEAD
  ocpci_vfio_dev_h dev;
  PyObject *path;
} ocpci_vfio_Device;

static PyObject *
ocpci_vfio_Device_dma_read(ocpci_vfio_Device *self, PyObject *args) {
  // passed 2 integers (offset/size)
  uint32_t offset;
  uint32_t size;
  int ret;
  char *buf;
  PyObject *bytearr;
  
  offset = 0;
  if (!PyArg_ParseTuple(args, "I|I", &size, &offset)) return NULL;
  buf = malloc(size);
  if (!buf) {
    PyErr_SetString(PyExc_MemoryError, "Could not allocate copy buffer");
    return NULL;
  }
  ret = ocpci_lib_vfio_dma_read(&self->dev, buf, offset, size);
  if (ret != OCPCI_SUCCESS) {
    PyErr_SetString(PyExc_OverflowError, "Read is out of range");
    return NULL;
  }
  bytearr = PyByteArray_FromStringAndSize(buf, size);
  free(buf);
  return bytearr;
}

static PyObject *
ocpci_vfio_Device_dma_init(ocpci_vfio_Device *self, PyObject *args) {
  // passed 2 integers (size, device base address)
  uint32_t size;
  __u64 base_address;
  int ret;
  if (!PyArg_ParseTuple(args, "KI", &base_address, &size)) return NULL;
  ret = ocpci_lib_vfio_dma_init(&self->dev, base_address, size);
  return Py_BuildValue("i", ret);
}

static PyObject *
ocpci_vfio_Device_dma_finish(ocpci_vfio_Device *self) {
  int ret;
  ret = ocpci_lib_vfio_dma_finish(&self->dev);
  return Py_BuildValue("i", ret);
}

static PyObject *
ocpci_vfio_Device_read(ocpci_vfio_Device *self, PyObject *args) {
  // passed 1 integer 
  uint32_t offset;
  uint32_t val;
  if (!PyArg_ParseTuple(args, "I", &offset)) return NULL;
  val = ocpci_lib_vfio_bar1_read(&self->dev, offset);
  return Py_BuildValue("i", val);
}

static PyObject *
ocpci_vfio_Device_write(ocpci_vfio_Device *self, PyObject *args) {
  // passed 2 integers: address and value to write.
  uint32_t offset;
  uint32_t value;
  if (!PyArg_ParseTuple(args, "II",
			&offset, &value))
    return NULL;  
  if (ocpci_lib_vfio_bar1_write(&self->dev, offset, value)) {
    PyErr_SetString(PyExc_ValueError,"Illegal offset");
    return NULL;
  }
  Py_RETURN_NONE;
}

static PyMemberDef ocpci_vfio_Device_members[] = {
  {"path", T_OBJECT_EX, offsetof(ocpci_vfio_Device, path), 0, "VFIO PCI device path"},
  { NULL } /* Sentinel */
};

static PyMethodDef ocpci_vfio_Device_methods[] = {
  { "read", (PyCFunction) ocpci_vfio_Device_read, METH_VARARGS,
    "Read from a WISHBONE address behind the OpenCores PCI Bridge."},
  { "write", (PyCFunction) ocpci_vfio_Device_write, METH_VARARGS,
    "Write to a WISHBONE address behind the OpenCores PCI Bridge."},
  { "dma_init", (PyCFunction) ocpci_vfio_Device_dma_init, METH_VARARGS,
    "initialize a buffer for DMA at a device base address of a specific size."},
  { "dma_finish", (PyCFunction) ocpci_vfio_Device_dma_finish, METH_NOARGS,
    "end usage of DMA buffer."},
  { "dma_read", (PyCFunction) ocpci_vfio_Device_dma_read, METH_VARARGS,
    "read bytes from the DMA buffer at a specific offset."},
  { NULL } /* Sentinel */
};

static void
ocpci_vfio_Device_dealloc(ocpci_vfio_Device *self)
{
  if (ocpci_vfio_is_open(&self->dev)) ocpci_lib_vfio_close(&self->dev);  
  Py_XDECREF(self->path);
  self->ob_type->tp_free((PyObject*) self);
}

static PyObject *
ocpci_vfio_Device_new( PyTypeObject *type, PyObject *args, PyObject *kwds) {
  ocpci_vfio_Device *self;
  self = (ocpci_vfio_Device *) type->tp_alloc(type, 0);
  if (self != NULL) {
    self->path = PyString_FromString("");
    if (self->path == NULL) {
      Py_DECREF(self);
      return NULL;
    }
  }
  return (PyObject *) self;
}

// Default path.
const char *ocpci_vfio_Device_path_default = "0000:02:0f.0";

static int
ocpci_vfio_Device_init( ocpci_vfio_Device *self, PyObject *args, PyObject *kwds) {
  static char *kwlist[] = {"path",NULL};
  PyObject *path_obj;
  const char *path;
  path = ocpci_vfio_Device_path_default;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "|s", kwlist,
				   &path)) return -1;
  path_obj = PyString_FromString(path);
  if (path_obj == NULL) return -1;
  Py_DECREF(self->path);
  self->path = path_obj;
  if (ocpci_lib_vfio_open(&self->dev, path)) return -1;
  return 0;
}

static PyTypeObject ocpci_vfio_DeviceType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "ocpci_vfio.Device",       /*tp_name*/
    sizeof(ocpci_vfio_Device), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor) ocpci_vfio_Device_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,        /*tp_flags*/
    "OCPCI VFIO Devices",      /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    ocpci_vfio_Device_methods,      /* tp_methods */
    ocpci_vfio_Device_members,      /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)ocpci_vfio_Device_init,      /* tp_init */
    0,                         /* tp_alloc */
    ocpci_vfio_Device_new,          /* tp_new */
};


static PyMethodDef module_methods[] = {
  {NULL} /* Sentinel */
};

#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif

PyMODINIT_FUNC
initocpci_vfio(void)
{
  PyObject *m;
  if (PyType_Ready(&ocpci_vfio_DeviceType) < 0) 
    return;

  m = Py_InitModule3("ocpci_vfio", module_methods,
		     "OpenCores PCI Bridge VFIO library.");
  
  if (m == NULL) 
    return;
  
  Py_INCREF(&ocpci_vfio_DeviceType);
  PyModule_AddObject(m, "Device", (PyObject *) &ocpci_vfio_DeviceType);
}
