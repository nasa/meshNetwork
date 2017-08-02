#ifndef COMM_TDMA_COMMANDS_HPP
#define COMM_TDMA_COMMANDS_HPP

#include <vector>
#include <cstdint>
#include <unordered_map>
#include "comm/command.hpp"
#include "comm/cmdHeader.hpp"
#include "node/nodeState.hpp"
#include "node/nodeParams.hpp"

namespace comm {
    
    //extern std::unordered_map<uint8_t, comm::HeaderType> tdmaCmdDict;
    
    namespace TDMACmds {
        //public:
            /*
             * Allowed TDMA command IDs.
             */
            enum {
                MeshStatus = 90,
                TimeOffset = 91,
                TimeOffsetSummary = 92,
                LinkStatus = 93,
                LinkStatusSummary = 94,
                BlockTxRequest = 95,
                BlockTxRequestResponse = 96,
                BlockTxConfirmed = 97,
                BlockTxStatus = 98,
                BlockData = 99
            };

            /*
             * Container of all TDMA command IDs.
             */
            extern std::vector<uint8_t> cmds;

            /*
             * Command ID to header type mapping.
             */
            extern std::unordered_map<uint8_t, comm::HeaderType> cmdDict;

            //static bool loaded;

            //bool loadCmds();
        
            std::unordered_map<uint8_t, comm::HeaderType> getCmdDict();
            std::vector<uint8_t> getCmds();
    }


    class TDMA_MeshStatus : public Command {
        public:

            /**
             * Time of mesh network creation, whole seconds.
             */
            uint32_t commStartTimeSec;

            /**
             * Current TDMA mesh status.
             */
            uint8_t status;

            /**
             * Primary constructor.
             * @param commStartTimeSecIn Mesh network creation time, whole seconds.
             * @param statusIn TDMA mesh status.
             * @param header Command header.
             * @param txInterval Command re-transmit interval.
             */
            TDMA_MeshStatus(unsigned int commStartTimeSecIn, unsigned int statusIn, CmdHeader header, double txInterval = node::NodeParams::config.commConfig.statusTxInterval);

            /**
             * Parsing constructor for creating command from message bytes.
             * @param msg Raw message bytes.
             */
            TDMA_MeshStatus(std::vector<uint8_t> & msg);

            /**
             * Command serialization method.
             * @return Returns serialized command for transmission.
             */
            virtual std::vector<uint8_t> serialize();
    };
    
    class TDMA_LinkStatus : public Command {
        public:

            /**
             * Inter-node network link status.
             */
            std::vector<uint8_t> linkStatus;

            /**
             * Primary constructor.
             * @param linkStatusIn Network links status.
             * @param header Command header.
             * @param txInterval Command re-transmit interval.
             */
            TDMA_LinkStatus(std::vector<uint8_t> & linkStatusIn, CmdHeader header, double txInterval = node::NodeParams::config.commConfig.linksTxInterval);

            /**
             * Parsing constructor for creating command from message bytes.
             * @param msg Raw message bytes.
             */
            TDMA_LinkStatus(std::vector<uint8_t> & msg);

            /**
             * Command serialization method.
             * @return Returns serialized command for transmission.
             */
            virtual std::vector<uint8_t> serialize();
    };

    class TDMA_LinkStatusSummary : public Command {
        public:

            /**
             * Inter-node network link status table.
             */
            std::vector<uint8_t> linkTable;

            /**
             * Primary constructor.
             * @param linkStatusIn Network links status table.
             * @param header Command header.
             * @param txInterval Command re-transmit interval.
             */
            TDMA_LinkStatusSummary(std::vector< std::vector<uint8_t> > & linkStatusIn, CmdHeader header, double txInterval = node::NodeParams::config.commConfig.linksTxInterval);

            /**
             * Parsing constructor for creating command from message bytes.
             * @param msg Raw message bytes.
             */
            TDMA_LinkStatusSummary(std::vector<uint8_t> & msg);

            /**
             * Command serialization method.
             * @return Returns serialized command for transmission.
             */
            virtual std::vector<uint8_t> serialize();
    };

    class TDMA_TimeOffset : public Command {
        public:

            /**
             * Current clock time offset.
             */
            double timeOffset;

            /**
             * Primary constructor.
             * @param offset Clock time offset.
             * @param header Command header.
             * @param txInterval Command re-transmit interval.
             */
            TDMA_TimeOffset(double offset, CmdHeader header, double txInterval = node::NodeParams::config.commConfig.offsetTxInterval);

            /**
             * Parsing constructor for creating command from message bytes.
             * @param msg Raw message bytes.
             */
            TDMA_TimeOffset(std::vector<uint8_t> & msg); // Parsing constructor

            /**
             * Command serialization method.
             * @return Returns serialized command for transmission.
             */
            virtual std::vector<uint8_t> serialize();


    };

    class TDMA_TimeOffsetSummary : public Command {
        public:

            /**
             * Clock time offset values received from all nodes.
             */
            std::vector<double> timeOffset;

            /**
             * Default constructor.
             */
            TDMA_TimeOffsetSummary();

            /**
             * Primary constructor.
             * @param offsets Clock time offsets of all nodes.
             */
            TDMA_TimeOffsetSummary(std::vector<double> & offsets);

            /**
             * Parsing constructor for creating command from message bytes.
             * @param msg Raw message bytes.
             */
            TDMA_TimeOffsetSummary(std::vector<uint8_t> & msg);

            /**
             * Command serialization method.
             * @return Returns serialized command for transmission.
             */
            virtual std::vector<uint8_t> serialize();

    };


}

#endif // COMM_TDMA_COMMANDS_HPP
