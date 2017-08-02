BBB_SRC:=GPIOWrapper_BBB.cpp \
         BeagleBoneBlack-GPIO/GPIO/GPIOManager.cpp \
         BeagleBoneBlack-GPIO/GPIO/GPIOConst.cpp

BBB_OBJS:=$(patsubst %.cpp, %.o, $(BBB_SRC))
BBB_OBJS:=$(BBB_OBJS:%.c=%.o)

RASPI_SRC:=GPIOWrapper_PI.cpp 
RASPI_OBJS:=$(patsubst %.cpp, %.o, $(RASPI_SRC))
RASPI_OBJS:=$(RASPI_OBJS:%.c=%.o)

default: GPIOWrapper.o
	ar rcs libgpiowrapper.a GPIOWrapper.o

bbb: $(BBB_OBJS)
	ar rcs libgpiowrapper.a $(BBB_OBJS)

pi: $(RASPI_OBJS)
	ar rcs libgpiowrapper.a $(RASPI_OBJS)

clean:
	rm -f *.o BeagleBoneBlack-GPIO/GPIO/*.o *.a
