#include <stdio.h>
#include <python3.14/Python.h>

PyObject* print_greetings(PyObject* frame, char* script_path) {
    PyGILState_STATE state = PyGILState_Ensure();
    printf("Called from script:  %s\n", script_path);
    printf("Frame Type:          %s\n", Py_TYPE(frame)->tp_name);
    printf("Frame Size:          %i\n", PyList_Size(frame));
    PyObject* local = PyList_GetItem(frame, PyList_Size(frame)-1); // get local frame
    printf("Setting variable...\n");
    printf("Checking local scope...\n");
    if (local && PyDict_Check(local)) {
        printf("Check passed!\n");
    } else {
       printf("Checked failed!\n");
       Py_RETURN_NONE;
    }
    PyObject* obj = Py_BuildValue(
        "{"
            "s:s"
        "}",
        "test", "it works!"
    );
    printf("Setting variable test to 'Hello, DPL!\n");
    PyObject_Repr(obj);
    if (PyDict_SetItemString(local, "test", obj) != 0) {
        printf("Setting of variable failed!\n");
    }
    Py_DECREF(obj);
    Py_DECREF(local); // since we got access to frame[-1]
    PyGILState_Release(state);
    printf("Done!\nIf You can read this, DPL can talk with C!\n");
    Py_RETURN_NONE;
}

PyObject* set_var(PyObject* frame, char* script_path, char* test) {
    printf("Name: %s\n", test);
    Py_RETURN_NONE;
}
