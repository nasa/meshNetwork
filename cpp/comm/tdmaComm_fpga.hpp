#ifndef COMM_TDMA_COMM_FPGA_HPP
#define COMM_TDMA_COMM_FPGA_HPP

#include "comm/tdmaComm.hpp"
//#include "comm/commProcessor.hpp"
#include "comm/radio.hpp"
#include "comm/msgParser.hpp"

namespace comm {

    class TDMAComm_FPGA : public TDMAComm {

        public:
            /**
             * Default constructor
             */
            TDMAComm_FPGA() {};

            /**
             * Constructor.
             * @param msgProcessorsIn Vector of message processors.
             * @param radioIn Radio to send/receive messages.
             * @param msgParserIn Message parser.
             */
            TDMAComm_FPGA(std::vector<MsgProcessor *> msgProcessorsIn, Radio * radioIn, MsgParser * msgParserIn = NULL);

            /**
             * Executes TDMA communication logic.
             * @param currentTime Current clock time.
             */
            virtual void executeTDMAComm(double currenTime);
    
            /**
             * Communication initialization function.
             * @param currentTime Current time.
             */
            virtual void init(double currentTime);

            /**
             * Initializes mesh network.
             * @param currentTime Current time.
             */
            virtual void initMesh(double currentTime);

            /**
             * Sleeps until end of TDMA frame.
             */
            virtual void sleep();

            /**
             * Checks for any received data.
             * @return End of transmission indication.
             */
            virtual bool readMsg();

            /**
             * TDMA transmit interval between messages to FPGA.
             */
            double transmitInterval;

            /**
             * TDMA last transmit time to FPGA.
             */
            double lastTransmitTime;
    };

}

#endif // COMM_TDMA_COMM_FPGA_HPP
