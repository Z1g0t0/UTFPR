// Packet.java
import java.io.Serializable;
import java.util.Arrays;

public class Packet implements Serializable {
    private static final long serialVersionUID = 1L;
    private int seq_n;
    private long checksum;
    private byte[] data;

    public Packet(int seq_n, long checksum, byte[] data) {
        this.seq_n = seq_n;
        this.checksum = checksum;
        this.data = data;
    }

    public int getSeq_n() {
        return seq_n;
    }

    public long getChecksum() {
        return checksum;
    }

    public byte[] getData() {
        return data;
    }
}
