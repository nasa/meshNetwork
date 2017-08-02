
CC:=gcc
CPP:=g++
LD:=g++
AR:=ar

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

OBJS:=$(patsubst %.cpp, %.o, $(SRC))
DEPS:=$(patsubst %.cpp, %.d, $(SRC))
OBJS:=$(OBJS:%.c=%.o)
DEPS:=$(DEPS:%.c=%.d)

TEST_OBJS:=$(patsubst %.cpp, %.o, $(TEST_SRC))
TEST_DEPS+=$(patsubst %.cpp, %.d, $(TEST_SRC))

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

.PHONY:all test clean $(SUBDIRS)

all: TARGET:=all
all: $(SUBDIRS) $(OBJS) $(TGT)

$(SUBDIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

%.a: $(OBJS)
	$(AR) rcs $@ $(OBJS)

%.d:%.cpp
	$(CPP) -MM $(CPPFLAGS) -MT $*.o $< -o $@

GTEST:=../lib/gtest
TEST_DRIVER:=run_test
test: TARGET:=test
test: CPPFLAGS+=-DASSERT_THROWS_EXCEPTION -I$(GTEST)/include -L$(GTEST)/cmake \
                -lgtest_main -lgtest
test: $(SUBDIRS) $(TEST_DRIVER)

$(TEST_DRIVER): $(TEST_OBJS) $(OBJS)
ifdef TEST_OBJS
	$(CPP) -o $@ $(CPPFLAGS) $(TEST_OBJS) $(OBJS) $(TESTDEPS) $(LDFLAGS)
endif
TEST_DRIVER:=run_test

clean: TARGET:=clean
clean: $(SUBDIRS)
	rm -f $(OBJS) $(DEPS) $(TEST_OBJS) $(TEST_DEPS) $(TGT) $(TEST_DRIVER) \
          $(EXTRA_CLEAN) *.stackdump *~

ifneq ($(MAKECMDGOALS),clean)
-include $(DEPS)
-include $(TEST_DEPS)
endif
