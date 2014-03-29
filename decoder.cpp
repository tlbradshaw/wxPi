#include "Python.h"
#include <iostream>
#include <stdlib.h>
#include <time.h>
#include <errno.h>
#include <signal.h>
#include "wiringPi.h"

#include "RCSwitch.h"
#include "RcOok.h"

using namespace std;


static int do_exit = 0;

/*
  sighandler - Signal handler for the read433 function
*/

static void sighandler(int signum)
{
	fprintf(stderr, "Signal caught, exiting!\n");
	do_exit = 1;
}


/*
  read433 - Function for reading directly from an RTL-SDR and returning a list of
  Manchester decoded bits.
*/

static PyObject *read433(PyObject *self, PyObject *args) {
	PyObject *output, *bits, *temp, *temp2, *temp2a, *temp2b, *temp3;
	long inputPin, duration, tStart;
	struct sigaction sigact;
	char message[512];
	
	if( !PyArg_ParseTuple(args, "ii", &inputPin, &duration) ) {
		PyErr_Format(PyExc_RuntimeError, "Invalid parameters");
		return NULL;
	}
	
	// Validate the input
	if( duration <= 0 ) {
		PyErr_Format(PyExc_ValueError, "Duration value must be greater than zero");
		return NULL;
	}
	
	// Setup the 433 MHz receiver
	if(wiringPiSetupSys() == -1) {
       PyErr_Format(PyExc_RuntimeError, "Cannot initialize the wiringPi library");
       return NULL;
   	}
   	RCSwitch *rc = new RCSwitch(inputPin,-1);
   	
   	// Setup the signal handler	so that we can exit the callback function
	sigact.sa_handler = sighandler;
	sigemptyset(&sigact.sa_mask);
	sigact.sa_flags = 0;
	sigaction(SIGINT, &sigact, NULL);
	sigaction(SIGTERM, &sigact, NULL);
	sigaction(SIGQUIT, &sigact, NULL);
	sigaction(SIGPIPE, &sigact, NULL);
   	
	// Setup the output list
	bits = PyList_New(0);
	
	// Go
	tStart = (long) time(NULL);
	while ((long) time(NULL) - tStart < duration && !do_exit) {
		//// Check for a message
		if ( rc->OokAvailable() ) {
			rc->getOokCode(message);
			
			cout << message << "\n" << flush;
			
			temp = PyString_FromString(message);
			temp2 = PyObject_CallMethod(temp, "split", "(si)", " ", 1);
			
			temp2a = PyList_GetItem(temp2, (Py_ssize_t) 0);
			temp2b = PyList_GetItem(temp2, (Py_ssize_t) 1);
			temp3 = PyTuple_Pack((Py_ssize_t) 2, temp2a, temp2b);
			PyList_Append(bits, temp3);
			
			Py_DECREF(temp);
			Py_DECREF(temp2);
			Py_DECREF(temp3);
		}
		
		//// Wait a bit (~1 ms)
		usleep(1000);
	}
	
	// Return
	output = Py_BuildValue("O", bits);
	return output;
}

PyDoc_STRVAR(read433_doc, \
"Read in the data from a 433 MHz receiver device and perform Manchester\n\
decoding, and return a list of strings for each packet received that is\n\
suitable for identifying Oregon Scientific v2.1 and v3.0 sensor data.\n\
\n\
Inputs:\n\
  * inputPin - GPIO pin on the Raspberry Pi to use\n\
  * duration - integer number of seconds to capture data for\n\
\n\
Outputs:\n\
 * packets - a list of two-element tuples containing the protocol and\n\
             the packat data-header as a hex string\n\
\n\
Based on:\n\
 * http://www.osengr.org/WxShield/Downloads/OregonScientific-RF-Protocols-II.pdf\n\
 * http://www.disk91.com/2013/technology/hardware/oregon-scientific-sensors-with-raspberry-pi/\n\
 * https://github.com/daveblackuk/RPI_Oregan.git\n\
");
 
 
/*
  Module Setup - Function Definitions and Documentation
*/

static PyMethodDef DecoderMethods[] = {
	{"read433", (PyCFunction) read433, METH_VARARGS, read433_doc}, 
	{NULL, NULL, 0, NULL}
};

PyDoc_STRVAR(Decoder_doc, \
"Module to read in and Manchester decode Oregon Scientific v2.1 and v3.0 weather\n\
station data.");


/*
  Module Setup - Initialization
*/

PyMODINIT_FUNC initdecoder(void) {
	PyObject *m;

	// Module definitions and functions
	m = Py_InitModule3("decoder", DecoderMethods, Decoder_doc);
	
	// Version and revision information
	PyModule_AddObject(m, "__version__", PyString_FromString("0.2"));
}