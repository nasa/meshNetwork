
-- Controls FM28V202A FRAM memory configured as 256K x 8 bit.
-- Reads are performed by using the rdEn flag and providing a
-- memory address.  The requested data and success flag are provided
-- upon successful read.  Writes are performed in the same manner, with
-- a success flag upon write completion.

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;
use work.meshPack.all;
use work.compDec.all;

entity memController is
    port(
        rst                 : in  std_logic;
        clk                 : in  std_logic;
        
        -- Data storage/access
        dataAddr            : in std_logic_vector(17 downto 0);
        rdEn                : in std_logic;
        rdData              : out std_logic_vector(7 downto 0);
        rdInProgress        : out std_logic;
        rdComplete          : out std_logic;
        wrEn                : in std_logic;
        wrData              : in std_logic_vector(7 downto 0);
        wrInProgress        : out std_logic;
        wrComplete          : out std_logic;
        
        -- memory control
        framEn              : out std_logic; -- chip enable (active low)
        framWrEn            : out std_logic; -- write enable (active high)
        framOeEn           : out std_logic; -- output enable (active low)
        framSleep           : out std_logic; -- sleep pin (0 = sleep, 1 = wake)
        framData            : inout std_logic_vector(7 downto 0); -- input/output data pins
        framAddr            : out std_logic_vector(17 downto 0) -- memory address to access ()
    );
end memController;

architecture memController_arch of memController is
    constant rdDelay : integer range 0 to (clkSpeed/1e9)*60+1 := (clkSpeed/1e9)*60 + 1;
    constant wrDelay : integer range 0 to (clkSpeed/1e9)*60+1 := (clkSpeed/1e9)*60 + 1;
    signal rdInProgressOut, wrInProgressOut : std_logic;
    
    type memCtrlStates is (idle, rdConfig, readData, wrConfig, waitWr1, writeData);
    signal memCtrlState : memCtrlStates;
    signal wrCnt,rdCnt : integer range 0 to 7;
    signal framWrEnOut : std_logic;
    signal framDin : std_logic_vector(7 downto 0);
    
    -- memory addressing
    signal memAddr : std_logic_vector(17 downto 0) := "000000000000000000";
    
    begin
            
        --dual rank sync data bus
        dualRankSync_data : dualRankSyncBus
            generic map (
                resetVal    => '0',
                busWidth    => 8) 
            port map (
                rst         => rst,
                clk         => clk,
                inData      => framData,
                outData     => framDin);    
    
        framAddr <= memAddr(17 downto 0);
        framWrEn <= framWrEnOut;
        
        rdInProgress <= rdInProgressOut;
        wrInProgress <= wrInProgressOut;
        
        --select what drives fram data base
        framData <= wrData when framWrEnOut = '0' else
                    "ZZZZZZZZ";
        
        framSleep <= '1'; -- always wake
        
        process(rst, clk)
            begin
                if (rst = '0') then
                    memCtrlState <= idle;
                    rdCnt <= 0;
                    wrCnt <= 0;
                    framEn <= '1'; -- fram disable
                    framOeEn <= '1'; -- bus controlled by fpga
                    framWrEnOut <= '1'; -- read enabled
                    rdInProgressOut <= '0';
                    wrInProgressOut <= '0';
                    rdComplete <= '0';
                    wrComplete <= '0';
                    
                elsif (clk'event and clk = '1') then
                    
                    case memCtrlState is
                        when idle =>
                            framEn <= '1'; -- fram disable
                            framOeEn <= '1'; -- bus controlled by fpga
                            framWrEnOut <= '1'; -- write enabled

                            if (rdEn = '0') then -- hold status until rdEn cleared
                                rdInProgressOut <= '0';
                                rdComplete <= '0';
                            end if;
                            
                            if (wrEn = '0') then -- hold status until wrEn cleared
                                wrInProgressOut <= '0';
                                wrComplete <= '0';
                            end if;
                            
                            if (rdEn = '1' and rdInProgressOut = '0') then -- don't start new read until in progress cleared
                                rdComplete <= '0';
                                rdInProgressOut <= '1'; -- feedback read started
                                memCtrlState <= rdConfig;
                            elsif (wrEn = '1' and wrInProgressOut = '0') then -- don't start new write until in progress cleared
                                wrComplete <= '0';
                                wrInProgressOut <= '1';
                                memCtrlState <= wrConfig;
                            end if;
                            
                        when rdConfig =>
                            --Setup a read from memory
                            framEn <= '0';
                            framOeEn <= '0';
                            framWrEnOut <= '1';
                            memAddr <= dataAddr;
                            memCtrlState <= readData; -- read from memory
                        
                        when readData =>
                            if rdCnt = rdDelay then -- read complete
                                rdCnt <= 0;
                                framOeEn <= '1';
                                rdComplete <= '1';
                                rdData <= framData;
                                memCtrlState <= idle;
                            else
                                rdCnt <= rdCnt + 1;
                            end if;
                            
                        when wrConfig =>                            
                            --store requested data
                            framEn <= '1';  
                            framWrEnOut <= '0';
                            framOeEn <= '1';
                            memAddr <= dataAddr;
                            memCtrlState <= waitWr1;
                        
                        when waitWr1 =>
                            framEn <= '0';
                            memCtrlState <= writeData;
                            
                        when writeData =>
                            if wrCnt = wrDelay then
                                wrCnt <= 0;
                                framEn <= '1';
                                framWrEnOut <= '1';
                                wrComplete <= '1';
                                memCtrlState <= idle; 
                            else
                                wrCnt <= wrCnt + 1;
                            end if;
                    end case;
                end if;
                    
        end process;            
                    
                    
end memController_arch;