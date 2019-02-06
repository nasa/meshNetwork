#ifndef COMM_TDMA_COMM_HPP
#define COMM_TDMA_COMM_HPP

#include <vector>
#include <unordered_map>
#include <memory>
#include <cstdint>
#include "comm/serialComm.hpp"
#include "comm/commProcessor.hpp"
#include "comm/radio.hpp"
#include "comm/msgParser.hpp"
#include "comm/command.hpp"
#include "comm/utilities.hpp"
#include "comm/formationClock.hpp"


namespace comm {

    // TDMA modes.
    enum TDMAMode {
        TDMA_SLEEP = 0,
        TDMA_INIT = 1,
        TDMA_RECEIVE = 2,
        TDMA_TRANSMIT = 3,
        TDMA_FAILSAFE = 4,
        TDMA_BLOCKRX = 5,
        TDMA_BLOCKTX = 6
    };

    // TDMA block transmit status.
    enum TDMABlockTxStatus {
        BLOCKTX_FALSE = 0,
        BLOCKTX_PENDING = 1,
        BLOCKTX_CONFIRMED = 2,
        BLOCKTX_ACTIVE = 3
    };

    // Status of current block transmit.
    struct BlockTxStatus {
        /**
         * Block transmit status.
         */
        TDMABlockTxStatus status;

        /**
         * Transmitting node ID.
         */
        uint8_t txNode;

        /**
         * Block transmit complete flag.
         */
        bool blockTxComplete;

        /**
         * Block start time.
         */
        double startTime;

        /**
         * Duration of this block transfer in number of frames.
         */
        uint8_t length;

        /**
         * IDs of nodes that have responded to this block transmit request.
         */
        std::vector<uint8_t> responseList;

        /**
         * Unique identifier of this block transmit request.
         */
        uint8_t blockReqID;

        /**
         * Time that block transmit request was made.
         */
        double requestTime;
    };

    // Buffered command for retransmission
    struct BufferedCmd {
        /**
         * Raw message bytes of command.
         */
        std::vector<uint8_t> bytes;

        /**
         * Command re-transmit interval.
         */
        double txInterval;
    };
    
    enum TDMAStatus {
        TDMASTATUS_NOMINAL = 0,
        TDMASTATUS_BLOCK_TX = 1
    };


    class TDMAComm : public SerialComm {

        public:
            /**
             * Default constructor
             */
            TDMAComm() {};

            /**
             * Constructor.
             * @param msgProcessorsIn Vector of message processors.
             * @param radioIn Radio to send/receive messages.
             * @param msgParserIn Message parser.
             */
            TDMAComm(std::vector<MsgProcessor *> msgProcessorsIn, Radio * radioIn, MsgParser * msgParserIn = NULL);

            /**
             * Primary class execution method.
             */
            void execute();
            
        public:
            /**
             * Executes TDMA communication logic.
             * @param currentTime Current clock time.
             */
            virtual void executeTDMAComm(double currenTime);
    
            /**
             * Updates current frame time.
             * @param currentTime Current clock time.
             * @return Returns frame period status.
             */
            int updateFrameTime(double currentTime);

            /**
             * Communication initialization function.
             * @param currentTime Current time.
             */
            virtual void init(double currentTime);

            /**
             * Initializes mesh network.
             * @param currentTime Current time.
             */
            virtual void initMesh(double currentTime = util::getTime());

            /**
             * Performs comm initialization.
             * @param currentTime Current clock time.
             */
            void initComm(double currentTime);

            /**            
             * Perform comm initializationChecks for comm initialization.
             */
            void checkForInit();

            /**
             * Synchronizes and resets TDMA framing.
             * @param currentTime Current time.
             */
            void syncTDMAFrame(double currentTime = util::getTime());

            /**
             * Updates contents of periodic mesh messages.
             */
            void updateMeshMsgs();

            /**
             * Sleeps until end of TDMA frame.
             */
            virtual void sleep();

            /**
             * Updates and monitors TDMA mode.
             * @param frameTime Current frame time.
             */
            void updateMode(double frameTime);

            /**
             * Resets TDMA slot parameters.
             * @param frameTime Current frame time.
             */
            void resetTDMASlot(double frameTime);

            /**
             * Sets TDMA mode.
             * @param mode Desired TDMA mode.
             */
            void setTDMAMode(TDMAMode mode);

            /**
             * Sends any buffered messages.
             */
            void sendMsg();

            /**
             * Checks for any received data.
             * @return End of transmission indication.
             */
            virtual bool readMsgs();

            /**
             * Buffers periodic TDMA command messages.
             */
            void sendTDMACmds();
    
            /**
             * Check clock time offset.
             * @param offset Current time offset value.
             * @return Returns status of time offset.
             */
            int checkTimeOffset(double offset = FormationClock::invalidOffset);


            /**
             * Checks time offset for failsafe condition.
             */
            int checkOffsetFailsafe();
        
            // *** EXPERIMENTAL ***

            /**
             * Sends block data.
             */
            void sendBlock();

            /**
             * Resets block transmit status.
             */
            void resetBlockTxStatus();

            /**
             * Monitors block transmission.
             */
            void monitorBlockTx();

            /**
             * Clears any stored data block.
             */
            void clearDataBlock();

            /**
             * Initiates block data transmit process.
             * @param dataBlock Data block to transmit.
             * @return Returns true upon successful block data transmit request sent.
             */
            bool sendDataBlock(std::vector<uint8_t> dataBlock);

            /**
             * Populates current node presence in block tx request response.
             */
            void populateBlockResponseList();

            /**
             * Checks for block tx request response from other nodes.
             * @return Returns current status of block request.
             */
            void checkBlockResponse();

            /**
             * TDMA Comm enable flag.
             */
            bool enabled;
    
            /**
             * TDMA communication start time.
             */
            double commStartTime;

            /**
             * Transmit slot for this node.
             */
            unsigned int transmitSlot;

            /**
             * TDMA frame length.
             */
            double frameLength;

            /**
             * TDMA slot length.
             */
            double slotLength;

            /**
             * Current TDMA frame time.
             */
            double frameTime;

            /**
             * TDMA cycle length.
             */
            double cycleLength;

            /**
             * Current TDMA mode.
             */
            TDMAMode tdmaMode;

            /**
             * Start time of current TDMA frame.
             */
            double frameStartTime;

            /**
             * Maximum number of TDMA slots.
             */
            unsigned int maxNumSlots;

            /**
             * TDMA slot enable length.
             */
            double enableLength;

            /**
             * Current TDMA slot time.
             */
            double slotTime;

            /**
             * Current TDMA slot number.
             */
            unsigned int slotNum;

            /**
             * Start time of current TDMA slot.
             */
            double slotStartTime;

            /**
             * Mesh network initialize flag.
             */
            bool inited;

            /**
             * Time to wait before initializing a new mesh network.
             */
            double initTimeToWait;

            /**
             * Mesh initialization wait start time.
             */
            double initStartTime;

            /**
             * Slot time to begin transmitting.
             */
            double beginTxTime;

            /**
             * Slot time to end transmitting.
             */
            double endTxTime;

            /**
             * Transmit completion flag.
             */
            bool transmitComplete;

            /**
             * Slot time to begin receiving.
             */
            double beginRxTime;

            /**
             * Slot time to end receiving.
             */
            double endRxTime;

            /**
             * Receive length.
             */
            double rxLength;

            /**
             * Time to begin reading including any desired delay.
             */
            double rxReadTime;

            /**
             * Receive completion flag.
             */
            bool receiveComplete;

            /**
             * Current read position in received data buffer.
             */
            unsigned int rxBufferReadPos;

            /**
             * Container of periodic TDMA commands.
             */
            std::unordered_map<uint8_t, std::unique_ptr<Command> > tdmaCmds;

            /**
             * Current block transmission status.
             */
            BlockTxStatus blockTxStatus;

            /**
             * Slot when last mode change occurred.
             */
            unsigned int lastModeChangeSlot;

            /**
             * Time that time offset was found unavailable.
             */
            double timeOffsetTimer;

            /**
             * TDMA in failsafe status flag.
             */
            bool tdmaFailsafe;

            /**
             * TDMA frame exceedance counter
             */
            uint16_t frameExceedanceCount;

            /**
             * Status of TDMA mesh network.
             */
            TDMAStatus tdmaStatus;

    };

}

#endif // COMM_TDMA_COMM_HPP
