import java.net.*;
import java.io.*;
import java.util.*;

public class client
{
    final static String CRLF = "\r\n";
    public static void main(String argv[]) throws Exception
    {
    	Socket s = new Socket("192.168.18.6", 6789);
    	//Socket s = new Socket("localhost", 6789);
	ObjectInputStream ois = new ObjectInputStream(s.getInputStream());
    	ObjectOutputStream oos = new ObjectOutputStream(s.getOutputStream());
	
	Scanner scanner = new Scanner(System.in);

	System.out.println("Conexao inicializada");

	while (s.isConnected())
	{
	    System.out.print("Cliente: ");
	    String message = scanner.nextLine();
	    oos.writeObject(message);    
	    oos.flush();

	    if(message.equals("Sair")) 
		break;

	    Object res = ois.readObject();
	    
	    if (res instanceof Integer) 
	    {
		String hash_mode = "SHA-256";
		FileOutputStream fos = new FileOutputStream(message);
		int size = (int) res;
		//System.out.println(size);
	    	byte[] buffer = new byte[size];
	    	int bytes = 0;
		int i = 0;

	    	while ((bytes = ois.read(buffer)) != -1 ) {
		    fos.write(buffer, 0, bytes);
		    fos.flush();
	    	}
		//System.out.println(i + ": " + bytes);
		res = ois.readObject();

	        if (hashCheck(hash_mode, res))
		    res += CRLF + "Verificacao hash: " + 
			hash_mode + " - Confirmado.";
	        else
		    res += CRLF + "Erro de verificacao "+
			"hash: " + hash_mode + " - " + 
			"Arquivo corrompido.";
	    }

	    String response = res.toString();
	    System.out.println("Servidor: " + response);
	}

	ois.close();
	oos.close();
	s.close(); 
	System.out.println("Conexao terminada");
    }

    //Check hash
    public static boolean hashCheck(String mode, Object response) throws Exception
    {
	
	BufferedReader br = new BufferedReader(new StringReader(response.toString()));

	br.readLine();
	String fileName = br.readLine();
	fileName = fileName.replace("\tArquivo: ", "");

	String resHash;
	while(!(resHash=br.readLine()).contains("Hash")) { 
	    continue; 
	}
	resHash = resHash.replace("\tHash: ", "");

	//System.out.println(hash);
	FileInputStream fis;

	try {
	    File file = new File(fileName);
	    fis = new FileInputStream(file);
	} catch (FileNotFoundException e) {
	    System.out.println( "Arquivo: " + fileName + 
				" nao encontrado.");
	    return false;
	}

	Hasher hasher = new Hasher();
	String fileHash = hasher.Hasher("SHA-256", fis);
	//fileHash += "x";
	//System.out.println( "fileHash: " + fileHash + 
	//		    CRLF + "resHash: " + resHash);
	
	return(fileHash.equals(resHash));
    }

}
