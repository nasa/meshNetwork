library ieee;
use ieee.std_logic_1164.all;
use IEEE.STD_LOGIC_unsigned.all;
use ieee.numeric_std.all;

package meshPack is
    -- types
    type msgArray is array (integer range <>) of std_logic_vector(7 downto 0);
    type radioModes is (off, sleep, receive, transmit);
    
    constant clkInSpeed : integer range 0 to 100000000 := 100000000;
    constant clkSpeed : integer range 0 to clkInSpeed := 25000000;
    constant clkDivider : integer range 0 to clkInSpeed/clkSpeed := clkInSpeed/clkSpeed;
    constant downclockMult : integer range 0 to clkInSpeed := clkInSpeed/clkSpeed;
    constant tdmaClkSpeed : integer range 0 to clkInSpeed := 10000000;
    constant tdmaClkDivider : integer range 0 to clkInSpeed/tdmaClkSpeed := clkInSpeed/tdmaClkSpeed;
    constant baudIntSize : integer range 0 to clkInSpeed/9600 := clkInSpeed/9600; -- based on minimum uart speed
    --constant baudCtrCnt : integer range 0 to baudIntSize := 2083; -- dev board
    --constant baudWidthCnt : integer range 0 to baudIntSize := 4166; -- dev board
    constant baudWidthCnt : integer range 0 to baudIntSize := clkSpeed/57600;
    constant baudCtrCnt : integer range 0 to baudIntSize := baudWidthCnt/2;

    --constant gpsBaudCtrCnt : integer range 0 to baudIntSize := 1042; -- dev board
    --constant gpsBaudWidthCnt : integer range 0 to baudIntSize := 2083; -- dev board
    constant gpsBaudWidthCnt : integer range 0 to baudIntSize := clkSpeed/19200; 
    constant gpsBaudCtrCnt : integer range 0 to baudIntSize := gpsBaudWidthCnt/2;
    constant maxTimeSec : integer range 0 to 86400 := 86400;
    
    constant MsToClk : integer range 0 to clkSpeed/1000 := clkSpeed/1000;  
    --constant tdmaMsToClk : integer range 0 to tdmaClkSpeed/1000 := tdmaClkSpeed/1000;
   
    -- tdma parameters
    constant tdma_frameRate : integer range 0 to 10 := 1; -- Hz
    constant tdma_frameLength : integer range 0 to clkSpeed := clkSpeed/tdma_frameRate; -- 1 s (1 Hz)
    constant tdma_slotLength : integer range 0 to 100*MsToClk := 100*MsToClk; -- 100 ms
    constant tdma_maxNumSlots : integer range 0 to 7 := 6;
    constant tdma_cycleLength : integer range 0 to tdma_slotLength * tdma_maxNumSlots := tdma_slotLength * tdma_maxNumSlots;
    -- constant tdma_preTxGuardLength : integer range 0 to tdma_slotLength := 5*MsToClk; -- 5 ms
    -- constant tdma_postTxGuardLength : integer range 0 to tdma_slotLength := 5*MsToClk; -- 5 ms
    -- constant tdma_txLength : integer range 0 to tdma_slotLength := 50*MsToClk; -- 50 ms
    -- constant tdma_rxLength : integer range 0 to tdma_slotLength := tdma_preTxGuardLength + tdma_txLength + tdma_postTxGuardLength;
    -- constant tdma_rxDelay : integer range 0 to tdma_slotLength := 0*MsToClk; -- ms
    -- constant tdma_enableLength : integer range 0 to tdma_slotLength := 5*MsToClk; -- 5 ms
    -- constant tdma_beginTxTime : integer range 0 to tdma_slotLength := tdma_enableLength + tdma_preTxGuardLength;
    -- constant tdma_endTxTime : integer range 0 to tdma_slotLength := tdma_beginTxTime + tdma_txLength;
    -- constant tdma_beginRxTime : integer range 0 to tdma_slotLength := tdma_enableLength;
    -- constant tdma_endRxTime : integer range 0 to tdma_slotLength := tdma_beginRxTime + tdma_rxLength;
    -- constant tdma_initTimeToWait : integer range 0 to 5 := 0; -- seconds
    -- constant tdma_rxReadTime : integer range 0 to tdma_slotLength := tdma_beginTxTime + tdma_rxDelay;
    constant tdma_preTxGuardLength : integer range 0 to tdma_slotLength := 5*MsToClk; -- 5 ms
    constant tdma_postTxGuardLength : integer range 0 to tdma_slotLength := 5*MsToClk; -- 5 ms
    constant tdma_txLength : integer range 0 to tdma_slotLength := 50*MsToClk; -- 50 ms
    constant tdma_rxLength : integer range 0 to tdma_slotLength := tdma_preTxGuardLength + tdma_txLength + tdma_postTxGuardLength;
    constant tdma_rxDelay : integer range 0 to tdma_slotLength := 0*MsToClk; -- ms
    constant tdma_enableLength : integer range 0 to tdma_slotLength := 5*MsToClk; -- 5 ms
    constant tdma_beginTxTime : integer range 0 to tdma_slotLength := tdma_enableLength + tdma_preTxGuardLength;
    constant tdma_endTxTime : integer range 0 to tdma_slotLength := tdma_beginTxTime + tdma_txLength;
    constant tdma_beginRxTime : integer range 0 to tdma_slotLength := tdma_enableLength;
    constant tdma_endRxTime : integer range 0 to tdma_slotLength := tdma_beginRxTime + tdma_rxLength;
    constant tdma_initTimeToWait : integer range 0 to 30 := 10; -- seconds
    constant tdma_rxReadTime : integer range 0 to tdma_slotLength := tdma_beginTxTime + tdma_rxDelay;
     
    -- Frame end times
    type tdmaFrameEndArray is array(tdma_frameRate-1 downto 0) of integer range 0 to clkSpeed;
    constant tdma_frameEnd : tdmaFrameEndArray := (0 => clkSpeed);
    --constant tdma_frame2End : integer range 0 to clkSpeed := tdma_frame1End + tdma_frameLength;
    
    -- Slot end times
    type tdmaSlotEndArray is array(tdma_maxNumSlots-1 downto 0) of integer range 0 to clkSpeed;
    constant tdma_slotEnd : tdmaSlotEndArray := (6*tdma_slotLength, 5*tdma_slotLength, 
        4*tdma_slotLength, 3*tdma_slotLength, 2*tdma_slotLength, tdma_slotLength);
    --constant tdma_slot1End : integer range 0 to clkSpeed := tdma_slotLength;
    --constant tdma_slot2End : integer range 0 to clkSpeed := tdma_slot1End + tdma_slotLength;
    --constant tdma_slot3End : integer range 0 to clkSpeed := tdma_slot2End + tdma_slotLength;
    --constant tdma_slot4End : integer range 0 to clkSpeed := tdma_slot3End + tdma_slotLength;
    --constant tdma_slot5End : integer range 0 to clkSpeed := tdma_slot4End + tdma_slotLength;
    --constant tdma_slot6End : integer range 0 to clkSpeed := tdma_slot5End + tdma_slotLength;
    --constant tdma_slot7End : integer range 0 to clkSpeed := tdma_slot6End + tdma_slotLength;                    
    --constant tdma_slot8End : integer range 0 to clkSpeed := tdma_slot7End + tdma_slotLength;    
    --constant tdma_slot9End : integer range 0 to clkSpeed := tdma_slot8End + tdma_slotLength;
    --constant tdma_slot10End : integer range 0 to clkSpeed := tdma_slot9End + tdma_slotLength;
    
    -- Node parameters
    signal nodeId : integer range 0 to 7 := 5;
    
    -- FRAM Partitioning
    -- type framAddrArray is array(tdma_maxNumSlots-1 downto 0) of std_logic_vector(17 downto 0);
    -- signal framStartAddr_meshArray : framAddrArray;
    -- signal framEndAddr_meshArray : framAddrArray;
    constant framMeshLength : integer range 0 to 1024 := 1024;
    constant framNodeLength : integer range 0 to 1024 := 1024;
    constant memStartAddr : std_logic_vector(17 downto 0) := "000000010000000000";
    -- Received mesh data partitions
    -- framStartAddr_mesh(1) := "000000010000000000";
    -- framEndAddr_mesh(1) := framStartAddr_mesh(1) + std_logic_vector(to_unsigned(framMeshLength, framStartAddr_mesh(1)'length));
    -- framStartAddr_mesh(2) := framEndAddr_mesh(1);
    -- framEndAddr_mesh(2) : std_logic_vector(17 downto 0) := framStartAddr_mesh(2) + std_logic_vector(to_unsigned(framMeshLength, framStartAddr_mesh(1)'length));
    -- framStartAddr_mesh(3) : std_logic_vector(17 downto 0) := framEndAddr_mesh(2);
    -- framEndAddr_mesh(3) : std_logic_vector(17 downto 0) := framStartAddr_mesh(3) + std_logic_vector(to_unsigned(framMeshLength, framStartAddr_mesh(1)'length));
    -- framStartAddr_mesh(4) : std_logic_vector(17 downto 0) := framEndAddr_mesh(3);
    -- framEndAddr_mesh(4) : std_logic_vector(17 downto 0) := framStartAddr_mesh(4) + std_logic_vector(to_unsigned(framMeshLength, framStartAddr_mesh(1)'length));
    -- framStartAddr_mesh(5) : std_logic_vector(17 downto 0) := framEndAddr_mesh(4);
    -- framEndAddr_mesh(5) : std_logic_vector(17 downto 0) := framStartAddr_mesh(5) + std_logic_vector(to_unsigned(framMeshLength, framStartAddr_mesh(1)'length));
    -- framStartAddr_mesh(6) : std_logic_vector(17 downto 0) := framEndAddr_mesh(5);
    -- framEndAddr_mesh(6) : std_logic_vector(17 downto 0) := framStartAddr_mesh(6) + std_logic_vector(to_unsigned(framMeshLength, framStartAddr_mesh(1)'length));
    constant framStartAddr_mesh : std_logic_vector(17 downto 0) := "000000010000000000";
    constant framEndAddr_mesh : std_logic_vector(17 downto 0) := framStartAddr_mesh + std_logic_vector(to_unsigned(framMeshLength, framStartAddr_mesh'length));
    -- Received data from node partitions
    constant framStartAddr_node1 : std_logic_vector(17 downto 0) := framEndAddr_mesh;
    constant framEndAddr_node1 : std_logic_vector(17 downto 0) := framStartAddr_node1 + std_logic_vector(to_unsigned(framNodeLength, framStartAddr_node1'length));
    constant framStartAddr_node2 : std_logic_vector(17 downto 0) := framEndAddr_node1;
    constant framEndAddr_node2 : std_logic_vector(17 downto 0) := framStartAddr_node2 + std_logic_vector(to_unsigned(framNodeLength, framStartAddr_node2'length));
    constant framStartAddr_tdmaCtrl : std_logic_vector(17 downto 0) := framEndAddr_node2;
    constant framEndAddr_tdmaCtrl : std_logic_vector(17 downto 0) := framStartAddr_tdmaCtrl + std_logic_vector(to_unsigned(framNodeLength, framStartAddr_tdmaCtrl'length));
    
    type msgType is (none, nodeMsg, meshMsg, tdmaCtrlMsg); -- fram read request type
    
    -- Node message parameters
    constant tdmaStatusCmdId: std_logic_vector(7 downto 0) := X"5A"; -- 90
    constant nodeMsgStartByte : std_logic_vector(7 downto 0) := X"FA"; -- 250
    constant nodeMsgMaxLength : integer range 0 to framNodeLength/2 := framNodeLength/2;
    type nodeMsgLengthArray is array (1 downto 0) of integer range 0 to nodeMsgMaxLength;
    type nodeMsgValidArray is array (1 downto 0) of std_logic;
    --signal nodeMsgLength : nodeMsgLengthArray := (0, 0);
    --signal nodeMsgValid : nodeMsgValidArray := ('0', '0');
   
    -- Memory access action
    type MemAction is (noMemAct, nodeRd, nodeWr, radioRd, radioWr, tdmaCtrlRd, tdmaCtrlWr);
   
    -- SLIP
    constant slipEnd : std_logic_vector(7 downto 0) := X"C0"; -- 192
    constant slipEsc : std_logic_vector(7 downto 0) := X"DB"; -- 219
    constant slipEscEnd : std_logic_vector(7 downto 0) := X"DC"; -- 220
    constant slipEscEsc : std_logic_vector(7 downto 0) := X"DD"; -- 221
    constant slipEndTdma : std_logic_vector(7 downto 0) := X"C1"; -- 193
    constant slipEscEndTdma : std_logic_vector(7 downto 0) := X"DE"; -- 222    
    constant slipMsgMaxLength : integer range 0 to 256 := 256;
    type slipAction is (slipNone, slipEncode, slipParse, slipMsgEnd);

   
    -- Functions
    function ascii_to_hex(ascii: std_logic_vector(7 downto 0)) return std_logic_vector;
    
end package;

package body meshPack is
    function ascii_to_hex(ascii: std_logic_vector(7 downto 0)) return std_logic_vector is
        begin
            if (ascii = X"30") then
                return X"0"; 
            elsif (ascii = X"31") then
                return X"1"; 
            elsif (ascii = X"32") then
                return X"2";   
            elsif (ascii = X"33") then
                return X"3"; 
            elsif (ascii = X"34") then
                return X"4"; 
            elsif (ascii = X"35") then
                return X"5"; 
            elsif (ascii = X"36") then
                return X"6"; 
            elsif (ascii = X"37") then
                return X"7"; 
            elsif (ascii = X"38") then
                return X"8"; 
            elsif (ascii = X"39") then
                return X"9";                 
            elsif (ascii = X"41") then
                return X"A";
            elsif (ascii = X"42") then
                return X"B";
            elsif (ascii = X"43") then
                return X"C";
            elsif (ascii = X"44") then
                return X"D";
            elsif (ascii = X"45") then
                return X"E";
            elsif (ascii = X"46") then
                return X"F";
            else -- invalid value
                return X"0";
            end if;
    end ascii_to_hex;
    
    
end meshPack;