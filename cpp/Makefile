LIBDIR:=./lib
JSONDIR:=$(LIBDIR)/rapidjson
GPIODIR:=$(LIBDIR)/GPIOWrapper
GTESTINCDIR:=/usr/local/include
GTESTLIBDIR:=/usr/local/lib

COMM_SRC:=comm/utilities.cpp \
     comm/radio.cpp \
     comm/udpRadio.cpp \
     comm/commands.cpp \
     comm/msgParser.cpp \
     comm/xbeeRadio.cpp \
     comm/li1Radio.cpp \
     comm/fpgaRadio.cpp \
     comm/crc_8.cpp \
     comm/crc_16.cpp \
     comm/checksum.cpp \
     comm/SLIPMsg.cpp \
     comm/SLIPMsgParser.cpp \
     comm/serialComm.cpp \
     comm/formationClock.cpp \
     comm/cmdHeader.cpp \
     comm/command.cpp \
     comm/nodeMsgProcessor.cpp \
     comm/tdmaMsgProcessor.cpp \
     comm/commandUtils.cpp \
     comm/nodeCmds.cpp \
     comm/tdmaCmds.cpp \
     comm/tdmaComm.cpp \
     comm/tdmaComm_fpga.cpp \
     comm/commControl.cpp \
     node/nodeState.cpp \
     node/nodeConfig.cpp \
     node/nodeParams.cpp \
     node/nodeInterface.cpp \
     node/nodeInterface.pb.cpp \
     node/nodeController.cpp \
     node/nodeExecutive.cpp \
     node/nodeControl.cpp 
     #node/pixhawk/pixhawkCmds.cpp

NODE_SRC:=node/nodeCmds.cpp \
     node/nodeController.cpp \
     node/nodeExecutive.cpp \
     node/nodeControl.cpp
    

TEST_SRC:=tests/radio_UT.cpp \
          tests/nodeConfig_UT.cpp \
          tests/cmdHeader_UT.cpp \
          tests/command_UT.cpp \
          tests/nodeCmds_UT.cpp \
          tests/tdmaCmds_UT.cpp \
          tests/commandUtils_UT.cpp \
          tests/msgParser_UT.cpp \
          tests/SLIPMsg_UT.cpp \
          tests/SLIPMsgParser_UT.cpp \
          tests/nodeMsgProcessor_UT.cpp \
          tests/tdmaMsgProcessor_UT.cpp \
          tests/serialComm_UT.cpp \
          tests/tdmaComm_UT.cpp
          #tests/xbeeRadio_UT.cpp \
          #tests/li1Radio_UT.cpp \
          #tests/commBuffer_UT.cpp \
          #tests/commProcessor_UT.cpp \
          #comm/testMsgProcessor.cpp \
          #tests/crc_UT.cpp \
          #tests/checksum_UT.cpp \
          #tests/serialComm_UT.cpp \
          #tests/formationClock_UT.cpp \
          #tests/nodeConfig_UT.cpp \
          #tests/nodeParams_UT.cpp \

TGT:=commControl
TGT_TYPE:=application

SP:=./

CFLAGS=-I./ -I./$(LIBDIR) -I$(GPIODIR) -I$(JSONDIR) -I$(GTESTINCDIR) #-DXPRINT_LOCATION #-DPRINT_DEBUG


CPPFLAGS:=-std=c++11

include $(SP)rules.mk

LDFLAGS+=-L$(JSONDIR) -lprotobuf -lrapidjson -lserial -lm -lrt -ldl -L$(GPIODIR) -lgpiowrapper -lcrypto -L$(GTESTLIBDIR) -lgtest -lpthread

pi: LDFLAGS+=-lwiringPi
pi: $(TGT)

%.d:%.cpp
	$(CPP) -MM $(CPPFLAGS) -MT $*.o $< -o $@

commControl: commControl.o $(COMM_OBJS)
	$(CPP) -o $@ $^ $(LDFLAGS)

test: runTest.o $(TEST_OBJS) $(COMM_OBJS)
	$(CPP) -o $@ $^ $(LDFLAGS)

EXTRA_CLEAN+=$(TGT).o $(TGT).d
