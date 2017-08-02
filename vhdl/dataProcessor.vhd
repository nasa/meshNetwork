-- dataProcessor.vhd
--
-- Manages reception, storing, and sending data received by fpga
-- from node and radio UARTs. Interfaces with FRAM to store and 
-- retrieve data.
--
-- Chris Becker
-- NASA MSFC EV42
-- 04/06/2016

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use ieee.numeric_std.all;
use work.meshPack.all;
use work.crc16.all;

entity dataProcessor is
    port (
        clk                 : in std_logic;
        rst                 : in std_logic;
        enable              : in std_logic;
        -- TDMA interface
        --tdmaInited          : in std_logic;
        tdmaTransmitFlag    : in std_logic;
        --tdmaFifoWrEn        : out std_logic;
        --tdmaFifoOut         : out std_logic_vector(7 downto 0);
        -- Data in/out to mesh radio
        radioRxFifoEmpty    : in std_logic;
        radioRxFifoRdEn     : out std_logic;          
        radioTxFifoFull     : in std_logic;
        radioTxFifoWrEn     : out std_logic;
        meshDataIn          : in std_logic_vector(7 downto 0);
        nodeDataOut         : out std_logic_vector(7 downto 0);
        -- Data in/out to node
        nodeRxFifoEmpty     : in std_logic;
        nodeRxFifoRdEn      : out std_logic;          
        nodeTxFifoFull      : in std_logic;
        nodeTxFifoWrEn      : out std_logic;
        nodeDataIn          : in std_logic_vector(7 downto 0);
        meshDataOut         : out std_logic_vector(7 downto 0);
        -- TDMA control messages    
        tdmaCtrlFifoRdEn    : out std_logic;
        tdmaCtrlFifoEmpty   : in std_logic;
        tdmaCtrlIn          : in std_logic_vector(7 downto 0);
        -- Data parser interface
        parserFifoWrEn      : out std_logic;
        parserFifoOut       : out std_logic_vector(7 downto 0);
        parserFifoRdEn      : out std_logic;
        parserFifoEmpty     : in std_logic;
        parserIn            : in std_logic_vector(7 downto 0);
        -- node data memory interface
        nodeMemRd           : out std_logic;
        nodeMemWr           : out std_logic;
        nodeMemDataOut      : out std_logic_vector(7 downto 0);
        nodeDataAddr        : out std_logic_vector(17 downto 0);
        nodeMemDataIn       : in std_logic_vector(7 downto 0);
        nodeMemComp         : in std_logic;
        -- radio data memory interface
        radioMemRd          : out std_logic;
        radioMemWr          : out std_logic;
        radioMemDataOut     : out std_logic_vector(7 downto 0);
        radioDataAddr       : out std_logic_vector(17 downto 0);
        radioMemDataIn      : in std_logic_vector(7 downto 0);
        radioMemComp        : in std_logic;
        -- tdma ctrl memory interface
        tdmaCtrlMemRd       : out std_logic;
        tdmaCtrlMemWr       : out std_logic;
        tdmaCtrlMemDataOut  : out std_logic_vector(7 downto 0);
        tdmaCtrlDataAddr    : out std_logic_vector(17 downto 0);
        tdmaCtrlMemDataIn   : in std_logic_vector(7 downto 0);
        tdmaCtrlMemComp     : in std_logic;
        currMemAct          : in MemAction
        
        
        
        
    );
end dataProcessor;

architecture behave of dataProcessor is
    type dataProcessorStates is (waitForChange, checkTDMA, readNodeFromFram, checkTDMACtrlRd, checkRadioRx, readRadioDelay, beginMeshMemWr, checkNodeRx, readNodeDelay, 
        readNodeFromBBB, readNodeByte, beginNodeMemWr, readNodeMsgCRC, checkForMesh, parserReadDelay, 
        checkTDMACtrlWr, tdmaCtrlReadDelay, beginMeshMemWrCtrl,
        waitForMemRd, updateDataRdAddr, forwardData, forwardDelay, waitForMemWr, updateDataWrAddr ); 
    signal dataProcState : dataProcessorStates;
    signal nextNodeReadState : dataProcessorStates := readNodeFromBBB;
    signal nextProcState : dataProcessorStates;
    
    -- Node message parameters
    signal nodeMsgRdPos : std_logic_vector(17 downto 0);
    signal bbbMsgPos : integer range 0 to nodeMsgMaxLength := 0;
    signal nodeMsgSize : integer range 0 to nodeMsgMaxLength := 0;
    signal nodeMsgReceive : std_logic := '0';
    signal nodeStartByteFound : std_logic := '0';
    signal nodeMsgIDByteFound : std_logic := '0'; 
    signal crcCalc : std_logic_vector(15 downto 0);
    signal crcByte : std_logic_vector(7 downto 0);
    signal nodeRdMsgSelect : std_logic := '0';
    signal nodeWrMsgSelect : std_logic := '1';
    signal nodeMsgValid : nodeMsgValidArray := ('0', '0');
    signal nodeMsgLength : nodeMsgLengthArray := (0, 0);
    signal currentMsgLength : integer range 0 to nodeMsgMaxLength := 0;
    signal tdmaTransmitComplete: std_logic;
    type nodeMsgEndArray is array (1 downto 0) of std_logic_vector(17 downto 0);
    signal nodeMsgEnd : nodeMsgEndArray := (framStartAddr_node2, framStartAddr_node1);
    signal meshWriteLoc, meshReadLoc : std_logic_vector(17 downto 0);
    signal meshBytesToRead : integer range 0 to framMeshLength;
    signal tdmaCtrlWriteLoc, tdmaCtrlReadLoc : std_logic_vector(17 downto 0);
    signal tdmaCtrlBytesToRead : integer range 0 to framMeshLength;
    signal cnt : integer range 0 to 2 := 0;
    
    signal meshMemRd : std_logic;
    
    -- read/write parameters
    signal rdType, wrType : msgType;
    
    begin
    
        -- Node slot control
        nodeRdMsgSelect <= not nodeWrMsgSelect;
        
        -- Data processing state machine
        process(rst, clk)
            variable temp : std_logic_vector(15 downto 0);
            
            begin
                if (rst = '0') then
                    dataProcState <= waitForChange;
                    nextProcState <= checkTDMA;
                    nextNodeReadState <= readNodeFromBBB;
                    bbbMsgPos <= 0;
                    nodeMsgRdPos <= framStartAddr_node1; -- default to second node buffer start (will be overwritten before first read)
                    nodeMsgValid <= ('0','0');
                    nodeMsgLength <= (0, 0);
                    nodeMsgEnd <= (framStartAddr_node2, framStartAddr_node1);
                    
                    -- Mesh memory access
                    meshWriteLoc <= framStartAddr_mesh;
                    meshReadLoc <= framStartAddr_mesh;
                    meshBytesToRead <= 0;
                    
                    -- TDMA Ctrl memory access
                    tdmaCtrlWriteLoc <= framStartAddr_tdmaCtrl;
                    tdmaCtrlReadLoc <= framStartAddr_tdmaCtrl;
                    tdmaCtrlBytesToRead <= 0;
                    
                    -- node message parsing
                    nodeMsgSize <= 0;
                    nodeMsgReceive <= '0';
                    nodeStartByteFound <= '0';
                    nodeMsgIDByteFound <= '0';
                    crcCalc <= X"0000";
                    crcByte <= X"00";
                    nodeWrMsgSelect <= '0'; -- default to first node message slot in fram
                    
                    
                    -- memory access
                    nodeMemRd <= '0';
                    nodeMemWr <= '0';
                    radioMemRd <= '0';
                    radioMemWr <= '0';
                    tdmaCtrlMemRd <= '0';
                    tdmaCtrlMemWr <= '0';
                    
                    -- data parser
                    parserFifoRdEn <= '0';
                    parserFifoWrEn <= '0';
                    
                    -- uart access
                    radioTxFifoWrEn <= '0';
                    radioRxFifoRdEn <= '0';
                    nodeRxFifoRdEn <= '0';
                    radioTxFifoWrEn <= '0';
                    nodeTxFifoWrEn <= '0';

                    currentMsgLength <= 0;
                    tdmaTransmitComplete <= '0';
                    rdType <= none;
                    --tdmaFifoWrEn <= '0';
                    --tdmaFifoOut <= X"00";
                    
                    -- Initialize output data to zero
                    nodeDataOut <= X"00";
                    meshDataOut <= X"00";
                    nodeMemDataOut <= X"00";
                    
                    
                    meshMemRd <= '0';
                    
                    cnt <= 1;
                    
                elsif (clk'event and clk = '1') then
                    
                    -- Priority
                        -- TDMA
                        -- Radio read
                        -- Node read
                        -- Mesh data forward to node
                    
                    case dataProcState is
                        when waitForChange =>

                            
                            -- status checks
                            if (tdmaTransmitFlag = '0' and tdmaTransmitComplete = '1') then
                                tdmaTransmitComplete <= '0'; -- clear completion
                            end if;
                        
                            dataProcState <= nextProcState;

                            
                        --- Data maintence sequence ---
                        -- TDMA
                        when checkTDMA =>
                            -- Check if time for mesh transmit
                            if (tdmaTransmitFlag = '1' and tdmaTransmitComplete = '0') then -- time to transmitData
                                if (nodeRdMsgSelect = '0' and nodeMsgValid(0) = '1') then -- valid data available
                                    nodeMsgRdPos <= framStartAddr_node1;
                                    currentMsgLength <= nodeMsgLength(0);
                                    dataProcState <= readNodeFromFram;
                                elsif (nodeRdMsgSelect = '1' and nodeMsgValid(1) = '1') then -- valid data available
                                    nodeMsgRdPos <= framStartAddr_node2;
                                    currentMsgLength <= nodeMsgLength(1);
                                    dataProcState <= readNodeFromFram;
                                else -- no valid data to send so skip this task
                                    nextProcState <= checkTDMACtrlRd;
                                    dataProcState <= waitForChange;
                                end if;
                            else -- proceed to next step
                                nextProcState <= checkTDMACtrlRd;
                                dataProcState <= waitForChange;
                            end if;
                        -- Read node data from fram for transmit
                        when readNodeFromFram =>
                            if (tdmaTransmitFlag = '0' or tdmaTransmitComplete = '1') then -- cease transmitting
                                nextProcState <= checkTDMACtrlRd;
                                dataProcState <= waitForChange;
                            else -- send data
                                rdType <= nodeMsg;
                                if (nodeRdMsgSelect = '0') then -- node message slot 1
                                    if (nodeMsgRdPos < nodeMsgEnd(0)) then -- more data to send
                                        nodeMemRd <= '1';
                                        nodeDataAddr <= nodeMsgRdPos;
                                        nextProcState <= readNodeFromFram;
                                        dataProcState <= waitForMemRd;
                                    else -- end of data
                                        nodeMsgValid(0) <= '0';
                                        tdmaTransmitComplete <= '1';
                                    end if;
                                else -- node message slot 2
                                    if (nodeMsgRdPos < nodeMsgEnd(1)) then -- more data to send
                                        nodeMemRd <= '1';
                                        nodeDataAddr <= nodeMsgRdPos;
                                        nextProcState <= readNodeFromFram;
                                        dataProcState <= waitForMemRd;
                                    else -- end of data
                                        nodeMsgValid(1) <= '0';
                                        tdmaTransmitComplete <= '1';
                                    end if;
                                end if;
                            end if;

                        when checkTDMACtrlRd =>
                            if (tdmaCtrlBytesToRead > 0) then -- more data to send
                                tdmaCtrlMemRd <= '1';
                                rdType <= tdmaCtrlMsg;
                                tdmaCtrlDataAddr <= tdmaCtrlReadLoc;
                                nextProcState <= checkTDMACtrlRd;
                                dataProcState <= waitForMemRd; 
                            else -- end of data
                                nextProcState <= checkRadioRx;
                                dataProcState <= waitForChange;
                            end if;
                            
                        -- Mesh radio receive
                        when checkRadioRx =>
                            nextProcState <= checkNodeRx;
                            if (radioRxFifoEmpty = '0') then -- new mesh data from radio
                                radioRxFifoRdEn <= '1'; -- enable read from radio uart fifo
                                dataProcState <= readRadioDelay;
                            else
                                dataProcState <= waitForChange;
                            end if;
                        when readRadioDelay =>
                            radioRxFifoRdEn <= '0';
                            if (cnt >= 2) then
                                dataProcState <= beginMeshMemWr;
                                cnt <= 1;
                            else
                                cnt <= cnt + 1;
                            end if;
                        when beginMeshMemWr =>
                            radioMemWr <= '1';
                            wrType <= meshMsg;
                            radioDataAddr <= meshWriteLoc;
                            radioMemDataOut <= meshDataIn;
                            dataProcState <= waitForMemWr;
                            
                            -- if (tdmaInited = '0') then -- pass data to tdma
                                -- tdmaFifoWrEn <= '1';
                                -- tdmaFifoOut <= meshDataIn;
                            -- end if;
                            
                            -- Pass data to data parser
                            parserFifoWrEn <= '1';
                            parserFifoOut <= meshDataIn;
                        
                        -- Node data receive
                        when checkNodeRx => 
                            nextProcState <= checkForMesh;
                            if (nodeRxFifoEmpty = '0') then -- new data from node
                                nodeRxFifoRdEn <= '1'; -- enable read from node uart fifo
                                cnt <= 1;
                                dataProcState <= readNodeDelay;
                            else
                                dataProcState <= waitForChange;
                            end if; 
                        -- Read node data from BBB and place in fram
                        when readNodeDelay => -- delay to read from fifo
                            nodeRxFifoRdEn <= '0';
                            if (cnt >= 2) then
                                dataProcState <= nextNodeReadState;
                                cnt <= 1;
                            else
                                cnt <= cnt + 1;
                            end if;
                        when readNodeFromBBB =>
                            -- Look for message start
                            --if (nodeMsgReceive = '0') then
                                if (nodeStartByteFound = '1') then -- look for start byte
                                    if (nodeMsgIDByteFound = '1') then -- get message length
                                        if (bbbMsgPos = 1) then -- first byte of message length
                                            --nodeMsgSize <= to_integer(unsigned(std_logic_vector(nodeDataIn & std_logic_vector(X"00")))));
                                            --temp := X"00" & nodeDataIn; -- little endian
                                            nodeMsgSize <= to_integer(unsigned(nodeDataIn));
                                            bbbMsgPos <= bbbMsgPos + 1;
                                        else -- second byte of message length
                                            temp := nodeDataIn & X"00";
                                            if (nodeMsgSize + to_integer(unsigned(temp)) <= nodeMsgMaxLength) then
                                                nodeMsgSize <= nodeMsgSize + to_integer(unsigned(temp));
                                                bbbMsgPos <= 1;
                                                nodeWrMsgSelect <= not nodeWrMsgSelect; -- alternate message slots in fram
                                                if (nodeWrMsgSelect = '0') then -- reset node message end position (opposite of current wrSelect)
                                                    nodeMsgEnd(1) <= framStartAddr_node2;
                                                else
                                                    nodeMsgEnd(0) <= framStartAddr_node1;
                                                end if;
                                                crcCalc <= X"0000"; -- clear calculated CRC
                                                nextNodeReadState <= readNodeByte;
                                            else -- message too big
                                                -- Reset node message search parameters
                                                bbbMsgPos <= 1;
                                                nodeStartByteFound <= '0';
                                                nodeMsgIDByteFound <= '0';
                                                nextNodeReadState <= readNodeFromBBB;
                                            end if;
                                        end if;
                                    elsif (nodeDataIn = nodeMsgStartByte) then -- node message found
                                        nodeMsgIDByteFound <= '1';
                                        bbbMsgPos <= 1;
                                    elsif (nodeDataIn = slipEnd) then -- false start
                                        bbbMsgPos <= 1;
                                    else
                                        nodeStartByteFound <= '0'; -- clear start status
                                    end if;
                                    
                                elsif (nodeDataIn = slipEnd) then -- start byte
                                    nodeStartByteFound <= '1';
                                    bbbMsgPos <= 1;
                                end if;
                                dataProcState <= nextProcState;                           
                        when readNodeByte =>
                            -- Update CRC
                            crcCalc <= crc16_update(crcCalc, nodeDataIn);
                            if (bbbMsgPos >= nodeMsgSize) then -- check CRC validity
                                bbbMsgPos <= 1;
                                nextNodeReadState <= readNodeMsgCRC;
                            else -- update crc
                                bbbMsgPos <= bbbMsgPos + 1;
                            end if;
                            dataProcState <= beginNodeMemWr;
                        when beginNodeMemWr =>
                            nodeMemWr <= '1';
                            wrType <= nodeMsg;
                            if (nodeWrMsgSelect = '0') then
                                nodeDataAddr <= nodeMsgEnd(0);
                            else
                                nodeDataAddr <= nodeMsgEnd(1);
                            end if;
                            nodeMemDataOut <= nodeDataIn;
                            dataProcState <= waitForMemWr;                       
                        when readNodeMsgCRC =>
                            --nodeFramFifoWrEn <= '1'; -- pipe read byte to memory
                            if (bbbMsgPos = 1) then -- first byte of CRC
                                crcByte <= nodeDataIn;
                                bbbMsgPos <= bbbMsgPos + 1;
                            else -- second byte of CRC
                                crcCalc <= X"0000"; -- clear calculated CRC
                                if (nodeDataIn & crcByte = crcCalc) then -- little endian
                                    if (nodeWrMsgSelect = '0') then -- set message slot valid
                                        nodeMsgLength(0) <= nodeMsgSize;
                                        nodeMsgValid(0) <= '1';
                                    else
                                        nodeMsgLength(1) <= nodeMsgSize;
                                        nodeMsgValid(1) <= '1';
                                    end if;
                                else -- CRC failed, clear message slot validity
                                    if (nodeWrMsgSelect = '0') then
                                        nodeMsgLength(0) <= 0;
                                        nodeMsgValid(0) <= '0';
                                    else
                                        nodeMsgLength(1) <= 0;
                                        nodeMsgValid(1) <= '0';
                                    end if;
                                end if;
                                
                                -- Reset node message search parameters
                                bbbMsgPos <= 1;
                                nodeStartByteFound <= '0';
                                nodeMsgIDByteFound <= '0';
                                nextNodeReadState <= readNodeFromBBB;
                            end if;
                            dataProcState <= waitForChange;    
                        
                        -- Check for mesh data to send to node
                        when checkForMesh =>
                            nextProcState <= checkTDMACtrlWr;
                            if (meshBytesToRead > 0) then -- mesh data waiting in memory
                                meshMemRd <= '1';
                                rdType <= meshMsg;
                                radioMemRd <= '1';
                                radioDataAddr <= meshReadLoc;
                                dataProcState <= waitForMemRd;
                            -- elsif (parserFifoEmpty = '0') then -- new parsed data
                                -- parserFifoRdEn <= '1';
                                -- cnt <= 1;
                                -- dataProcState <= parserReadDelay;
                            else
                                dataProcState <= waitForChange;
                            end if;
                        when parserReadDelay =>
                            parserFifoRdEn <= '0';
                            if (cnt >= 2) then
                                rdType <= meshMsg;
                                dataProcState <= forwardData;
                                cnt <= 1;
                            else
                                cnt <= cnt + 1;
                            end if;
                            -- if (meshBytesToRead > 0) then -- mesh data waiting in memory
                                -- rdType <= mesh;
                                -- memRdEn <= '1';
                                -- memDataAddr <= meshReadLoc;
                                -- dataProcState <= waitForMemRd;
                            -- else
                                -- dataProcState <= waitForChange;
                            -- end if;
                                   
                        -- Check for TDMA control messages
                        when checkTDMACtrlWr =>
                            if (tdmaCtrlFifoEmpty = '0') then -- new control bytes to forward
                                tdmaCtrlFifoRdEn <= '1';
                                cnt <= 1;
                                dataProcState <= tdmaCtrlReadDelay;
                            else
                                --tdmaTransmitComplete <= '1';
                                nextProcState <= checkTDMA; -- only update once no bytes pending
                                dataProcState <= waitForChange;
                            end if;
                        when tdmaCtrlReadDelay => -- delay to read from fifo
                            tdmaCtrlFifoRdEn <= '0';
                            if (cnt >= 2) then
                                dataProcState <= beginMeshMemWrCtrl;
                                cnt <= 1;
                            else
                                cnt <= cnt + 1;
                            end if;
                        when beginMeshMemWrCtrl => -- append ctrl bytes to mesh received data
                            tdmaCtrlMemWr <= '1';
                            wrType <= tdmaCtrlMsg;
                            tdmaCtrlDataAddr <= tdmaCtrlWriteLoc;
                            tdmaCtrlMemDataOut <= tdmaCtrlIn;
                            dataProcState <= waitForMemWr;
                            
                        -- Memory access states
                        -- memory read sequence
                        when waitForMemRd =>
                            if (rdType = nodeMsg) then
                                if (currMemAct = nodeRd) then -- read started
                                    nodeMemRd <= '0';
                                end if;
                                if (nodeMemComp = '1') then -- read complete
                                    dataProcState <= updateDataRdAddr;
                                end if;
                            elsif (rdType = meshMsg) then -- mesh read complete
                                if (currMemAct = radioRd) then -- read started                                       
                                    radioMemRd <= '0';
                                end if;
                                if (radioMemComp = '1') then -- read complete
                                    dataProcState <= updateDataRdAddr;
                                end if;
                            elsif (rdType = tdmaCtrlMsg) then
                                if (currMemAct = tdmaCtrlRd) then -- read started
                                    tdmaCtrlMemRd <= '0';
                                end if;
                                if (tdmaCtrlMemComp = '1') then -- read complete
                                    dataProcState <= updateDataRdAddr;
                                end if;
                            end if;
                                
                            
                        when updateDataRdAddr =>
                            if (rdType = meshMsg) then -- mesh read
                                if (meshReadLoc < framEndAddr_mesh - 1) then -- check for buffer wrap
                                    meshReadLoc <= meshReadLoc + '1';
                                else
                                    meshReadLoc <= framStartAddr_mesh;
                                end if;
                                
                                meshBytesToRead <= meshBytesToRead - 1;
                            elsif (rdType = nodeMsg) then -- node read
                                nodeMsgRdPos <= nodeMsgRdPos + '1';
                            elsif (rdType = tdmaCtrlMsg) then -- tdma ctrl read
                                if (tdmaCtrlReadLoc < framEndAddr_tdmaCtrl - 1) then -- check for buffer wrap
                                    tdmaCtrlReadLoc <= tdmaCtrlReadLoc + '1';
                                else
                                    tdmaCtrlReadLoc <= framStartAddr_tdmaCtrl;
                                end if;
                                
                                tdmaCtrlBytesToRead <= tdmaCtrlBytesToRead - 1;
                            end if;
                            dataProcState <= forwardData;
                        when forwardData =>
                            if (rdType = meshMsg) then -- forward to node uart
                                nodeTxFifoWrEn <= '1';
                                if (meshMemRd = '1') then -- memory read
                                    meshDataOut <= radioMemDataIn;
                                    meshMemRd <= '0';
                                else -- parser read
                                    meshDataOut <= parserIn;
                                end if;
                            else -- send to radio uart
                                radioTxFifoWrEn  <= '1';
                                if (rdType = nodeMsg) then
                                    nodeDataOut <= nodeMemDataIn;
                                else -- tdma ctrl message
                                    nodeDataOut <= tdmaCtrlMemDataIn;
                                end if;
                            end if;
                            dataProcState <= forwardDelay;
                        when forwardDelay =>    
                            -- clear fifo wr enables
                            nodeTxFifoWrEn <= '0';
                            radioTxFifoWrEn <= '0';
                            dataProcState <= waitForChange;
                        
                        -- memory write sequence
                        when waitForMemWr =>
                            --tdmaFifoWrEn <= '0'; -- end tdma fifo write
                            parserFifoWrEn <= '0'; -- end parser fifo write
                            if (wrType = nodeMsg) then
                                if (currMemAct = nodeWr) then -- write started
                                    nodeMemWr <= '0';
                                end if;
                                if (nodeMemComp = '1') then -- write complete
                                    dataProcState <= updateDataWrAddr;
                                end if;
                            elsif (wrType = meshMsg) then
                                if (currMemAct = radioWr) then -- write started
                                    radioMemWr <= '0';
                                end if;
                                if (radioMemComp = '1') then -- write complete
                                    dataProcState <= updateDataWrAddr;
                                end if;
                            elsif (wrType = tdmaCtrlMsg) then
                                if (currMemAct = tdmaCtrlWr) then -- write started
                                    tdmaCtrlMemWr <= '0';
                                end if;
                                if (tdmaCtrlMemComp = '1') then -- write complete
                                    dataProcState <= updateDataWrAddr;
                                end if;
                            end if;

                        when updateDataWrAddr =>
                            if (wrType = meshMsg) then -- mesh write
                                -- Check for memory buffer wrap
                                if (meshWriteLoc < framEndAddr_mesh - 1) then
                                    meshWriteLoc <= meshWriteLoc + '1';
                                else
                                    meshWriteLoc <= framStartAddr_mesh;
                                end if;
                                
                                -- Increment number of bytes in buffer
                                if (meshBytesToRead < framMeshLength) then
                                    meshBytesToRead <= meshBytesToRead + 1;
                                end if;
                            elsif (wrType = nodeMsg) then -- node write
                                if (nodeWrMsgSelect = '0') then
                                    if (nodeMsgEnd(0) < framEndAddr_node1) then 
                                        nodeMsgEnd(0) <= nodeMsgEnd(0) + '1';
                                    end if;
                                else
                                    if (nodeMsgEnd(1) < framEndAddr_node2) then 
                                        nodeMsgEnd(1) <= nodeMsgEnd(1) + '1';
                                    end if;
                                end if;
                            elsif (wrType = tdmaCtrlMsg) then -- tdma ctrl write
                                -- Check for memory buffer wrap
                                if (tdmaCtrlWriteLoc < framEndAddr_tdmaCtrl - 1) then
                                    tdmaCtrlWriteLoc <= tdmaCtrlWriteLoc + '1';
                                else
                                    tdmaCtrlWriteLoc <= framStartAddr_tdmaCtrl;
                                end if;
                                
                                -- Increment number of bytes in buffer
                                if (tdmaCtrlBytesToRead < framMeshLength) then
                                    tdmaCtrlBytesToRead <= tdmaCtrlBytesToRead + 1;
                                end if;
                            end if;
                            dataProcState <= waitForChange;                        

                    end case;         
                end if;
        end process;
        
end behave;