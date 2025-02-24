
import java.io.*;
import java.security.*;
import java.math.*;

public class Hasher
{
    public String Hasher(String mode, FileInputStream fis)
    throws Exception
    {
	MessageDigest md = MessageDigest.getInstance(mode);
	DigestInputStream dis = new DigestInputStream(fis, md);
	byte[] digest = md.digest();
	BigInteger bigInt = new BigInteger(1, digest);
	String hash = bigInt.toString(16);

	return hash;
    }
}
