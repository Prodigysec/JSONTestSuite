-- JSONTestSuite adapter for Patrick Lehmann's JSON-for-VHDL (Apache-2.0).
-- Read each byte, including whitespace and NUL, without textio normalization.
library work;
use work.JSON.all;

entity JSONSuiteVHDL is
  generic (G_FILENAME : string := "");
end entity;

architecture validator of JSONSuiteVHDL is
  type byte_file is file of character;

  impure function read_bytes(filename : string) return string is
    file source : byte_file open read_mode is filename;
    variable bytes_buf : string(1 to 65534);
    variable length : natural := 0;
    variable byte_value : character;
  begin
    while not endfile(source) loop
      assert length < bytes_buf'length report "input exceeds VHDL content limit" severity failure;
      read(source, byte_value);
      length := length + 1;
      bytes_buf(length) := byte_value;
    end loop;
    file_close(source);
    return bytes_buf(1 to length);
  end function;

  constant content : string := read_bytes(G_FILENAME);
begin
  process
    variable parsed : T_JSON;
  begin
    if content'length = 0 then
      report "JSONTESTSUITE_VHDL_REJECT" severity note;
    else
      parsed := jsonParseStream(content);
      if jsonNoParserError(parsed) then
        report "JSONTESTSUITE_VHDL_ACCEPT" severity note;
      else
        report "JSONTESTSUITE_VHDL_REJECT" severity note;
      end if;
    end if;
    wait;
  end process;
end architecture;
