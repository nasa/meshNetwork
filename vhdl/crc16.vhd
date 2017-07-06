library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package crc16 is
    type crc16Table is array (0 to 255) of std_logic_vector(15 downto 0);
    constant crc16LookupTable : crc16Table := (X"0000", X"c0c1", X"c181", X"0140", X"c301", X"03c0", X"0280", X"c241",
        X"c601", X"06c0", X"0780", X"c741", X"0500", X"c5c1", X"c481", X"0440",
        X"cc01", X"0cc0", X"0d80", X"cd41", X"0f00", X"cfc1", X"ce81", X"0e40",
        X"0a00", X"cac1", X"cb81", X"0b40", X"c901", X"09c0", X"0880", X"c841",
        X"d801", X"18c0", X"1980", X"d941", X"1b00", X"dbc1", X"da81", X"1a40",
        X"1e00", X"dec1", X"df81", X"1f40", X"dd01", X"1dc0", X"1c80", X"dc41",
        X"1400", X"d4c1", X"d581", X"1540", X"d701", X"17c0", X"1680", X"d641",
        X"d201", X"12c0", X"1380", X"d341", X"1100", X"d1c1", X"d081", X"1040",
        X"f001", X"30c0", X"3180", X"f141", X"3300", X"f3c1", X"f281", X"3240",
        X"3600", X"f6c1", X"f781", X"3740", X"f501", X"35c0", X"3480", X"f441",
        X"3c00", X"fcc1", X"fd81", X"3d40", X"ff01", X"3fc0", X"3e80", X"fe41",
        X"fa01", X"3ac0", X"3b80", X"fb41", X"3900", X"f9c1", X"f881", X"3840",
        X"2800", X"e8c1", X"e981", X"2940", X"eb01", X"2bc0", X"2a80", X"ea41",
        X"ee01", X"2ec0", X"2f80", X"ef41", X"2d00", X"edc1", X"ec81", X"2c40",
        X"e401", X"24c0", X"2580", X"e541", X"2700", X"e7c1", X"e681", X"2640",
        X"2200", X"e2c1", X"e381", X"2340", X"e101", X"21c0", X"2080", X"e041",
        X"a001", X"60c0", X"6180", X"a141", X"6300", X"a3c1", X"a281", X"6240",
        X"6600", X"a6c1", X"a781", X"6740", X"a501", X"65c0", X"6480", X"a441",
        X"6c00", X"acc1", X"ad81", X"6d40", X"af01", X"6fc0", X"6e80", X"ae41",
        X"aa01", X"6ac0", X"6b80", X"ab41", X"6900", X"a9c1", X"a881", X"6840",
        X"7800", X"b8c1", X"b981", X"7940", X"bb01", X"7bc0", X"7a80", X"ba41",
        X"be01", X"7ec0", X"7f80", X"bf41", X"7d00", X"bdc1", X"bc81", X"7c40",
        X"b401", X"74c0", X"7580", X"b541", X"7700", X"b7c1", X"b681", X"7640",
        X"7200", X"b2c1", X"b381", X"7340", X"b101", X"71c0", X"7080", X"b041",
        X"5000", X"90c1", X"9181", X"5140", X"9301", X"53c0", X"5280", X"9241",
        X"9601", X"56c0", X"5780", X"9741", X"5500", X"95c1", X"9481", X"5440",
        X"9c01", X"5cc0", X"5d80", X"9d41", X"5f00", X"9fc1", X"9e81", X"5e40",
        X"5a00", X"9ac1", X"9b81", X"5b40", X"9901", X"59c0", X"5880", X"9841",
        X"8801", X"48c0", X"4980", X"8941", X"4b00", X"8bc1", X"8a81", X"4a40",
        X"4e00", X"8ec1", X"8f81", X"4f40", X"8d01", X"4dc0", X"4c80", X"8c41",
        X"4400", X"84c1", X"8581", X"4540", X"8701", X"47c0", X"4680", X"8641",
        X"8201", X"42c0", X"4380", X"8341", X"4100", X"81c1", X"8081", X"4040");

    function crc16_update(crc : std_logic_vector(15 downto 0); newData : std_logic_vector(7 downto 0)) return std_logic_vector;
   
end package;

package body crc16 is
    function crc16_update(crc : std_logic_vector(15 downto 0); newData : std_logic_vector(7 downto 0)) return std_logic_vector is
        variable table_index : integer range 0 to 255 := 0;
        begin
            table_index := to_integer(unsigned((crc(7 downto 0) xor newData) and X"FF")); 
            return (crc16LookupTable(table_index) xor (X"00" & crc(15 downto 8))) and X"FFFF";
            --return X"FFFF";
    end crc16_update;
end crc16;