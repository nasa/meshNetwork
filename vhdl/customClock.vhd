-- uartRx.vhd
--
-- UART transmitter model for the camera link interface.  
--
-- David Hyde
-- NASA MSFC EI31
-- 3/6/2006
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use work.meshPack.all;

entity customClock is
    generic(
        clockDivider : integer range 0 to 100000 := 2;
        halfClk : integer range 0 to 100000 := 1
    );
    port (
            clk     : in  std_logic;
            rst     : in  std_logic;
            clkOut  : out std_logic 
    );
end customClock;
    
architecture behave of customClock is

type clockStates is (waitForClkHigh,waitForClkLow);
signal clockState : clockStates;

signal cnt : integer range 0 to clockDivider := 0;
begin

-- transmitter
process(rst, clk)
begin
	if rst = '0' then
		clockState <= waitForClkLow;
		cnt <= 1;
        clkOut <= '0';

	elsif (clk'event and clk = '1') then
        if (cnt = clockDivider) then
            clkOut <= '1';
            cnt <= 1;
        -- elsif (cnt >= halfClk) then
            -- clkOut <= '0';
            -- cnt <= cnt + 1;
        else
            clkOut <= '0';
            cnt <= cnt + 1;
        end if;

   
	end if;
end process;



------------------------------------------------------------------------------------------


end behave;

 