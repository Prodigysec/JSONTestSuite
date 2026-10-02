import com.realtimetech.opack.codec.json.Json;
import com.realtimetech.opack.exception.DecodeException;

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
        try {
            byte[] bytes = Files.readAllBytes(Paths.get(args[0]));
            // The string-only API uses UTF-8 without BOM stripping or replacement.
            String input = StandardCharsets.UTF_8.newDecoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(bytes)).toString();
            Json.decodeObject(input);
            return 0;
        } catch (DecodeException | CharacterCodingException | NumberFormatException error) {
            System.err.println(error.toString());
            return 1;
        } catch (Throwable error) {
            // Includes I/O, missing classes, and unexpected parser failures.
            System.err.println(error.toString());
            return 2;
        }
    }

    public static void main(String[] args) {
        System.exit(parse(args));
    }
}
