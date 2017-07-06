-- uartRx.vhd
--
-- UART receiver model.  
--
-- David Hyde
-- NASA MSFC EI31
-- 3/6/2006
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use work.meshPack.all;

entity uartRx is
    generic(
        ctrStrtCnt : integer range 0 to baudIntSize := baudCtrCnt;
        baudCnt : integer range 0 to baudIntSize := baudWidthCnt
    );
    port (
		clk          : in  std_logic;
		rst          : in  std_logic;
		rx           : in  std_logic; -- 
		rxData       : out std_logic_vector(7 downto 0); -- received data
		rxFifoWrEn   : out std_logic;
		rxFifoFull   : in  std_logic;
		frameError   : out std_logic
    );
end uartRx;

architecture behave of uartRx is

    type rxStates is (wait4High, wait4Start, centerStart, sampleAndShift, findStop,waitDeadtime);
    signal rxState : rxStates;

    signal startBaud    : std_logic;
    signal shiftCnt             : std_logic_vector(2 downto 0);
    signal rxDataReg            : std_logic_vector(7 downto 0);
    signal rxByteRdy            : std_logic;
    signal cnt 					: integer range 0 to baudIntSize;

    begin

        -- receiver
        process(rst, clk)
        begin
            if rst = '0' then
                rxState <= wait4High;
                rxFifoWrEn <= '0';
                cnt <= 0;
                shiftCnt <= "000";
                frameError <= '0';
                rxDataReg <= X"00";
                rxData <= X"00";

            elsif clk'event and clk = '1' then
                case rxState is
                    when wait4High =>	   -- to handle break condition
                        rxFifoWrEn <= '0';
                        if (rx = '1') then
                            rxState <= wait4Start;
                        end if;
                    when wait4Start =>
                        rxFifoWrEn <= '0';
                        -- finds first '0' then finds center of start bit
                        if (rx = '0') then
                            cnt <= cnt + 1;
                            rxState <= centerStart;
                        end	if;
                    when centerStart =>
                        if cnt = ctrStrtCnt then
                            cnt <= 1;
                            rxState <= sampleAndShift;
                        else
                            cnt <= cnt + 1;
                        end if;
                    when sampleAndShift =>
                        if cnt = baudCnt then
                            cnt <= 1;
                            shiftCnt <= shiftCnt + '1';
                            rxDataReg <= rx & rxDataReg(7 downto 1);
                            if shiftCnt = "111" then
                                rxState <= findStop;
                            end if;
                        else
                            cnt <= cnt + 1;
                            
                        end if;
                    when findStop =>
                        if cnt = baudCnt then
                            cnt <= 0;
                            -- this should be the stop bit, flag a frame error if it isn't
                            if rx = '0' then
                                frameError <= '1';
                                rxState <= wait4High;
                            else
                                rxData <= rxDataReg; 
                                rxFifoWrEn <= '1';
                                rxState <= wait4Start; --waitDeadtime;
                            end if;
                        else
                            cnt <= cnt + 1;
                        end if;
                    when waitDeadtime =>
                        rxFifoWrEn <= '0';
                        --the HV module goes to '0' for a bit period after stop bit
                        --wait in this state to make sure the line is zero 
                        --before going back to wait4High state. (line might still be high after
                        --(txEn from hvPktTx is released)
                        if cnt = baudCnt then
                            cnt <= 0;
                            rxState <= wait4High;
                        else
                            cnt <= cnt + 1;
                        end if;

                end case;
            end if;
        end process;

end behave;

