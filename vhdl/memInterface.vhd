-- memInterface.vhd
--
-- This entity provides an interface to the memory controller
-- for all other entities that which to access memory. 
--
-- Chris Becker
-- NASA MSFC EV42
-- 10/22/2016

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use work.meshPack.all;

entity memInterface is
    port (
        clk                 : in std_logic;
        rst                 : in std_logic;
        -- node data memory interface
        nodeMemRd           : in std_logic;
        nodeMemWr           : in std_logic;
        nodeDataIn          : in std_logic_vector(7 downto 0);
        nodeDataAddr        : in std_logic_vector(17 downto 0);
        nodeDataOut         : out std_logic_vector(7 downto 0);
        nodeMemComp         : out std_logic;
        -- radio data memory interface
        radioMemRd          : in std_logic;
        radioMemWr          : in std_logic;
        radioDataIn         : in std_logic_vector(7 downto 0);
        radioDataAddr       : in std_logic_vector(17 downto 0);
        radioDataOut        : out std_logic_vector(7 downto 0);
        radioMemComp        : out std_logic;
        -- tdma ctrl memory interface
        tdmaCtrlMemRd       : in std_logic;
        tdmaCtrlMemWr       : in std_logic;
        tdmaCtrlDataIn      : in std_logic_vector(7 downto 0);
        tdmaCtrlDataAddr    : in std_logic_vector(17 downto 0);
        tdmaCtrlDataOut     : out std_logic_vector(7 downto 0);
        tdmaCtrlMemComp     : out std_logic;
        -- memory control/status
        currMemAct          : out MemAction;
        memRdEn             : out std_logic;
        rdComplete          : in std_logic;
        memWrEn             : out std_logic;
        wrComplete          : in std_logic;
        memDataAddr         : out std_logic_vector(17 downto 0);
        dataToMem           : out std_logic_vector(7 downto 0);
        dataFromMem         : in std_logic_vector(7 downto 0)
    );
end memInterface;

architecture behave of memInterface is
    type MemInterfaceStates is (checkForReq, waitForMemRd, waitForMemWr); 
    signal memIntState : MemInterfaceStates;
    signal nextState : MemInterfaceStates;
     
    -- Memory action
    signal rdType, wrType : MemAction;
    
    begin
    
        -- Data processing state machine
        process(rst, clk)
            variable temp : std_logic_vector(15 downto 0);
            
            begin
                if (rst = '0') then
                    memIntState <= checkForReq;
                    
                    -- memory action outputs
                    nodeMemComp <= '0';
                    nodeDataOut <= X"00";
                    radioMemComp <= '0';
                    radioDataOut <= X"00";
                    tdmaCtrlMemComp <= '0';
                    tdmaCtrlDataOut <= X"00";
                    
                    -- memory access
                    memRdEn <= '0';
                    memWrEn <='0';
                    
                elsif (clk'event and clk = '1') then
                    
                    -- Data priority
                        -- Node read
                        -- Node write
                        -- TDMA Ctrl read
                        -- TDMA Ctrl write
                        -- Radio write
                        -- Radio read

                        
                    case memIntState is
                        when checkForReq => -- Check for memory access request
                            -- Cleanup memory request status
                            nodeMemComp <= '0';
                            radioMemComp <= '0';
                            tdmaCtrlMemComp <= '0';
                            
                            -- Take action on any requests
                            if (nodeMemRd = '1') then
                                memRdEn <= '1';
                                memDataAddr <= nodeDataAddr;
                                rdType <= nodeRd;
                                currMemAct <= nodeRd;
                                memIntState <= waitForMemRd;
                            elsif (nodeMemWr = '1') then
                                memWrEn <= '1';
                                memDataAddr <= nodeDataAddr;
                                dataToMem <= nodeDataIn;
                                wrType <= nodeWr;
                                currMemAct <= nodeWr;
                                memIntState <= waitForMemWr;
                            elsif (tdmaCtrlMemRd = '1') then
                                memRdEn <= '1';
                                memDataAddr <= tdmaCtrlDataAddr;
                                rdType <= tdmaCtrlRd;
                                currMemAct <= tdmaCtrlRd;
                                memIntState <= waitForMemRd;
                            elsif (tdmaCtrlMemWr = '1') then
                                memWrEn <= '1';
                                memDataAddr <= tdmaCtrlDataAddr;
                                dataToMem <= tdmaCtrlDataIn;
                                wrType <= tdmaCtrlWr;
                                currMemAct <= tdmaCtrlWr;
                                memIntState <= waitForMemWr;
                            elsif (radioMemWr = '1') then
                                memWrEn <= '1';
                                memDataAddr <= radioDataAddr;
                                dataToMem <= radioDataIn;
                                wrType <= radioWr;
                                currMemAct <= radioWr;
                                memIntState <= waitForMemWr;
                            elsif (radioMemRd = '1') then
                                memRdEn <= '1';
                                memDataAddr <= radioDataAddr;
                                rdType <= radioRd;
                                currMemAct <= radioRd;
                                memIntState <= waitForMemRd;
                            end if;
                        
                        -- Memory access states
                        when waitForMemRd => -- memory read
                            if (rdComplete = '1') then -- read complete
                                memRdEn <= '0';
                                currMemAct <= noMemAct; -- clear action
                                
                                -- Output data
                                if (rdType = nodeRd) then
                                    nodeMemComp <= '1';
                                    nodeDataOut <= dataFromMem;
                                elsif (rdType = radioRd) then
                                    radioMemComp <= '1';
                                    radioDataOut <= dataFromMem;
                                elsif (rdType = tdmaCtrlRd) then
                                    tdmaCtrlMemComp <= '1';
                                    tdmaCtrlDataOut <= dataFromMem;
                                end if;        
                                memIntState <= checkForReq;                                
                            end if;
    
                            
                            
                        when waitForMemWr => -- memory write
                            if (wrComplete = '1') then -- monitor memory write
                                memWrEn <= '0';
                                currMemAct <= noMemAct; -- clear action
                                
                                -- Update status
                                if (wrType = nodeWr) then
                                    nodeMemComp <= '1';
                                elsif (wrType = radioWr) then
                                    radioMemComp <= '1';
                                elsif (wrType = tdmaCtrlWr) then
                                    tdmaCtrlMemComp <= '1';
                                end if;
                                
                                memIntState <= checkForReq;
                            end if;

                            
                    end case;         
                end if;
        end process;
        
end behave;