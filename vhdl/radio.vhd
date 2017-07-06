-- radio.vhd
--
-- Interface to XBee radio.  
--
-- Chris Becker
-- NASA MSFC EV42
-- 3/22/2016

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use work.meshPack.all;

entity radio is
    port (
            clk         : in std_logic;
            rst         : in std_logic;
            radioMode   : in radioModes;
            sendDataIn  : in std_logic;
            dataIn      : in std_logic_vector(7 downto 0);
            dataOut     : out std_logic_vector(7 downto 0);
            sendDataOut : out std_logic;
            sleepStatus : in std_logic;
            sleepOut    : out std_logic
        );
end radio;

architecture behave of radio is
    type radioStates is (sleeping, waitForSleep, waitForWake, awake, sendData);
    signal radioState : radioStates;

    begin
        sleepOut <= '0'; -- radio on
    
        process(rst, clk)
        begin
            if rst = '0' then
                --sleepOut <= '1'; -- set HIGH to sleep
                radioState <= sleeping;
                sendDataOut <= '0';

            elsif clk'event and clk = '1' then
                case radioState is
                    when sleeping =>
                        if (radioMode = receive or radioMode = transmit) then -- wake radio
                            --sleepOut <= '0';
                            radioState <= waitForWake;
                        else -- stay asleep
                            --sleepOut <= '1';
                        end if;
                    when waitForWake =>
                        if (radioMode = sleep or radioMode = off) then -- sleep radio
                            --sleepOut <= '1';
                            radioState <= waitForSleep;
                        elsif (sleepStatus = '1') then -- radio is awake
                            radioState <= awake;
                        else 
                            --sleepOut <= '0';
                        end if;
                    when awake =>
                        if (radioMode = sleep or radioMode = off) then -- request to sleep
                            --sleepOut <= '1';
                            radioState <= waitForSleep;
                        elsif (sendDataIn = '1') then -- request to send data
                            sendDataOut <= '1';
                            dataOut <= dataIn;
                            radioState <= sendData;
                        else -- stay awake
                            --sleepOut <= '0';
                        end if;
                    when waitForSleep =>
                        if (radioMode = receive or radioMode = transmit) then -- wake radio
                            --sleepOut <= '0';
                            radioState <= waitForWake;
                        elsif (sleepStatus = '0') then -- radio is sleeping
                            radioState <= sleeping;
                        else 
                            --sleepOut <= '1';
                        end if;
                    when sendData => -- wait for data to send
                        sendDataOut <= '0';
                        radioState <= awake;
                        
                end case;
            end if;
        end process;
        
end behave;

