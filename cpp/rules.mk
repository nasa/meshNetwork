
CC:=gcc
CPP:=g++
CXX:=g++
LD:=g++
AR:=ar

#CC:=/home/aerom/test/gcc-linaro-6.3.1-2017.05-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-gcc
#CPP:=/home/aerom/test/gcc-linaro-6.3.1-2017.05-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-g++
#CXX:=/home/aerom/test/gcc-linaro-6.3.1-2017.05-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-g++
#LD:=/home/aerom/test/gcc-linaro-6.3.1-2017.05-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-g++
#AR:=/home/aerom/test/gcc-linaro-6.3.1-2017.05-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-ar
#CPLUS_INCLUDE_PATH=-I/usr/local/include/ -I/usr/include/

BASEDIR:=$(SP)
LDFLAGS:=
CFLAGS+=-O2 
CPPFLAGS+=$(CFLAGS) -g -Wall

SYSTEM:=$(shell uname)
ARCH:=$(shell uname -m)
SYS_CYGWIN:=CYGWIN_NT-5.1
SYS_MINGW:=MINGW32_NT-5.1
SYS_LINUX:=Linux
SYS_DARWIN:=Darwin

## Object and fependency files
# Comm object and dependency files
COMM_OBJS:=$(patsubst %.cpp, %.o, $(COMM_SRC))
COMM_DEPS:=$(patsubst %.cpp, %.d, $(COMM_SRC))

# Node object and dependency files
NODE_OBJS:=$(patsubst %.cpp, %.o, $(NODE_SRC))
NODE_DEPS:=$(patsubst %.cpp, %.d, $(NODE_SRC))

# Test object and dependency files
TEST_OBJS:=$(patsubst %.cpp, %.o, $(TEST_SRC))
TEST_DEPS+=$(patsubst %.cpp, %.d, $(TEST_SRC))

## Targets
all: $(SUBDIRS) comm $(TGT)

comm: $(COMM_OBJS) commControl

node: $(SUBDIRS) $(COMM_OBJS) $(NODE_OBJS) $(TGT)

$(SUBDIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

%.a: $(COMM_OBJS) $(NODE_OBJS)
	$(AR) rcs $@ $(COMM_OBJS) $(NODE_OBJS)

%.d:%.cpp
	$(CPP) -MM $(CPPFLAGS) -MT $*.o $< -o $@


ifeq ($(TGTTYPE), static_lib)
TGT:=lib$(TGT).a
LDFLAGS+=-lrt -ldl -lpthread
endif

ifeq ($(TGTTYPE), application)
ifeq ($(SYSTEM),$(SYS_CYGWIN))
TGT:=$(TGT).exe
else
ifeq ($(SYSTEM),$(SYS_MINGW))
TGT:=$(TGT).exe
else
TGT:=$(TGT)
LDFLAGS+=-ldl -lpthread
endif
endif
endif



# All Google Test headers.  Usually you shouldn't change this
# definition.
GTEST_DIR:=$(LIBDIR)/gtest
GTESTINCDIR:=$(LIBDIR)/gtest/include
GTEST_HEADERS = $(GTEST_DIR)/include/gtest/*.h \
                $(GTEST_DIR)/include/gtest/internal/*.h

# Usually you shouldn't tweak such internal variables, indicated by a
# trailing _.
GTEST_SRCS_ = $(GTEST_DIR)/src/*.cc $(GTEST_DIR)/src/*.h $(GTEST_HEADERS)

# For simplicity and to avoid depending on Google Test's
# implementation details, the dependencies specified below are
# conservative and not optimized.  This is fine as Google Test
# compiles fast and for ordinary users its source rarely changes.
gtest-all.o : $(GTEST_SRCS_)
	$(CXX) $(CPPFLAGS) -I$(GTEST_DIR) $(CXXFLAGS) -c $(GTEST_DIR)/src/gtest-all.cc

gtest_main.o : $(GTEST_SRCS_)
	$(CXX) $(CPPFLAGS) -I$(GTEST_DIR) $(CXXFLAGS) -c $(GTEST_DIR)/src/gtest_main.cc

gtest.a : gtest-all.o
	$(AR) $(ARFLAGS) $@ $^

gtest_main.a : gtest-all.o gtest_main.o
	$(AR) $(ARFLAGS) $@ $^

TEST_DRIVER:=run_test
test: TARGET:=test
test: CPPFLAGS+=-DASSERT_THROWS_EXCEPTION -I$(GTESTINCDIR)

test: gtest_main.a $(SUBDIRS) $(TEST_DRIVER) $(GTEST_HEADERS)

#$(TEST_DRIVER): $(BASEDIR)test_harness.cpp $(TEST_OBJS) $(OBJS)
$(TEST_DRIVER): $(TEST_OBJS) $(COMM_OBJS) gtest_main.a
ifdef TEST_OBJS
	$(CPP) -o $@ $(CPPFLAGS) $(TEST_OBJS) $(COMM_OBJS) $(TESTDEPS) $(LDFLAGS) gtest_main.a -lpthread
endif

clean: TARGET:=clean
clean: $(SUBDIRS)
	rm -f *.o $(COMM_OBJS) $(NODE_OBJS) $(COMM_DEPS) $(NODE_DEPS) $(TEST_OBJS) $(TEST_DEPS) $(TGT) $(TEST_DRIVER) \
          $(EXTRA_CLEAN) gtest* *.stackdump *~

ifneq ($(MAKECMDGOALS),clean)
-include $(COMM_DEPS)
-include $(TEST_DEPS)
endif
