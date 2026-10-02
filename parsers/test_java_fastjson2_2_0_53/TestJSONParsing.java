import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONException;

import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;

public class TestJSONParsing {
    private static int parse(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: TestJSONParsing FILE");
            return 2;
        }
        byte[] bytes;
        try {
            bytes = Files.readAllBytes(Paths.get(args[0]));
        } catch (Exception error) {
            System.err.println(error.toString());
            return 2;
        }
        try {
            String input = StandardCharsets.UTF_8.newDecoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(bytes)).toString();
            if (input.isEmpty() || input.trim().isEmpty()) {
                return 1;
            }
            JSON.parse(input);
            return 0;
        } catch (JSONException | CharacterCodingException error) {
            System.err.println(error.toString());
            return 1;
        } catch (Throwable error) {
            System.err.println(error.toString());
            return 2;
        }
    }

    public static void main(String[] args) {
        System.exit(parse(args));
    }
}
