mymodule: renderer.c
	gcc -shared -fPIC -I/usr/include/python2.7/ -lpython2.7 `pkg-config cairo --libs --cflags` `pkg-config pycairo --libs --cflags` -o renderer.so renderer.c
