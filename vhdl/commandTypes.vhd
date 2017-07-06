library ieee;
use ieee.std_logic_1164.all;
use IEEE.STD_LOGIC_unsigned.all;
use ieee.numeric_std.all;
use work.meshPack.all;

package commandTypes is

    constant numCmds : integer range 0 to 10 := 10;
    constant maxCmdSize : integer range 0 to 255 := 5;
    
    
    -- Definitions
    type CmdHeaderType is (MinimalHeader, SourceHeader, NodeHeader, InvalidHeader);
    type CommandType is record
        valid : std_logic;
        timestamp : integer range 0 to maxTimeSec;
        unique : std_logic;
    end record;
    
    type CommandTypeArray is array(0 to numCmds) of CommandType;
    
    signal cmdTypes : CommandTypeArray;
   
    -- Helper functions
    function getCmdHeaderType(cmdId : std_logic_vector(7 downto 0)) return CmdHeaderType;
    
end package;

package body commandTypes is

    function getCmdHeaderType(cmdId : std_logic_vector(7 downto 0)) return CmdHeaderType is
        variable cmdIdInt : integer range 0 to 255 := to_integer(unsigned(cmdId));
        
        begin
            if (cmdIdInt = 111) then -- PixhawkCmds.NodeStateUpdate
                return SourceHeader;
            elsif (cmdIdInt = 90) then -- TDMACmds.MeshStatus
                return SourceHeader;
            else -- invalid value
                return InvalidHeader;
            end if;
            
    end getCmdHeaderType;
    
end commandTypes;
    
