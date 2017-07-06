-- dualRankSyncR0.vhd
--
-- dual rank synchronizer, generic determines reset val
--
-- David Hyde
-- NASA EI31
-- 3/9/2006

library ieee;
use ieee.std_logic_1164.all;

entity dualRankSync is
generic ( resetVal : std_logic := '0');
port (
	inData, clk, rst : in std_logic;
	outData          : out std_logic );
end dualRankSync;

architecture behave of dualRankSync is

signal inDataS : std_logic;

begin

process (rst, clk)
begin
	if rst = '0' then
		outdata <= resetVal;
		inDataS <= resetVal;
	elsif clk'event and clk = '1' then
		indataS <= inData;
		outData <= indataS;
	end if;
end process;
end behave;

			