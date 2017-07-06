-- dualRankSyncR0.vhd
--
-- dual rank synchronizer, generic determines reset val
--
-- David Hyde
-- NASA EI31
-- 3/9/2006

library ieee;
use ieee.std_logic_1164.all;

entity dualRankSyncBus is
generic ( 
    resetVal        : std_logic := '0';
    busWidth        : integer := 2
    );
port (
	clk, rst        : in  std_logic;
    inData          : in  std_logic_vector(busWidth - 1 downto 0);
	outData         : out std_logic_vector(busWidth - 1 downto 0)
    );
end dualRankSyncBus;

architecture behave of dualRankSyncBus is

signal inDataS : std_logic_vector(busWidth - 1 downto 0);

begin

process (rst, clk)
begin
	if rst = '0' then
		outdata <= (others => resetVal);
		inDataS <= (others => resetVal);
	elsif clk'event and clk = '1' then
		indataS <= inData;
		outData <= indataS;
	end if;
end process;
end behave;

			