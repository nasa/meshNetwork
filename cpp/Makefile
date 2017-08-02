LIBDIR:=./lib
JSONDIR:=$(LIBDIR)/rapidjson
GPIODIR:=$(LIBDIR)/GPIOWrapper

COMM_SRC:=comm/utilities.cpp \
     comm/radio.cpp \
     comm/serialRadio.cpp \
     comm/udpRadio.cpp \
     comm/commands.cpp \
     comm/msgParser.cpp \
     comm/xbeeRadio.cpp \
     comm/li1Radio.cpp \
     comm/fpgaRadio.cpp \
     comm/crc.cpp \
     comm/checksum.cpp \
     comm/SLIPMsg.cpp \
     comm/SLIPMsgParser.cpp \
     comm/commProcessor.cpp \
     comm/comm.cpp \
     comm/formationClock.cpp \
     comm/cmdHeader.cpp \
     comm/command.cpp \
     comm/tdmaMsgProcessor.cpp \
     comm/commandUtils.cpp \
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
          tests/msgParser_UT.cpp \
          tests/xbeeRadio_UT.cpp \
          tests/li1Radio_UT.cpp \
          tests/commBuffer_UT.cpp \
          tests/commProcessor_UT.cpp \
          comm/testMsgProcessor.cpp \
          tests/crc_UT.cpp \
          tests/checksum_UT.cpp \
          tests/SLIPMsg_UT.cpp \
          tests/SLIPMsgParser_UT.cpp \
          tests/serialComm_UT.cpp \
          tests/formationClock_UT.cpp \
          tests/nodeConfig_UT.cpp \
          tests/nodeParams_UT.cpp \
          tests/tdmaComm_UT.cpp

TGT:=commControl
TGT_TYPE:=application

SP:=./

CFLAGS=-I./ -I./$(LIBDIR) -I$(GPIODIR) -I$(JSONDIR) #-DXPRINT_LOCATION #-DPRINT_DEBUG


CPPFLAGS:=-std=c++11

include $(SP)rules.mk

LDFLAGS+=-L$(JSONDIR) -lpthread -lprotobuf -lrapidjson -lserial -lm -lrt -ldl -L$(GPIODIR) -lgpiowrapper -lcrypto

pi: LDFLAGS+=-lwiringPi
pi: $(TGT)

%.d:%.cpp
	$(CPP) -MM $(CPPFLAGS) -MT $*.o $< -o $@

commControl: commControl.o $(COMM_OBJS)
	$(CPP) -o $@ $^ $(LDFLAGS)


EXTRA_CLEAN+=$(TGT).o $(TGT).d
