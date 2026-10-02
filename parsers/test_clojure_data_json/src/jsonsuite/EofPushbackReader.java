package jsonsuite;

import java.io.IOException;
import java.io.PushbackReader;
import java.io.Reader;

// data.json 1.0.0 and 2.2.0 both try to unread -1 after a number at EOF.
public final class EofPushbackReader extends PushbackReader {
    public EofPushbackReader(Reader input, int size) {
        super(input, size);
    }

    @Override
    public void unread(int value) throws IOException {
        if (value != -1) {
            super.unread(value);
        }
    }
}
