import java.io.*;
import java.net.*;
import java.util.*;

public final class WebServer
{
    public static void main(String argv[]) throws Exception
    {
	// Set the port number.
	int port = 6789;

	// Establish the listen socket.
	ServerSocket ss = new ServerSocket(port);

	while (true) {
	    // Listen for a TCP connection request.
	    Socket socket = ss.accept();

	    Cliente cliente = new Cliente(socket);

	    // Create a new thread to process the request.
	    Thread thread = new Thread(cliente);
	    thread.start();
	}
    }
}

final class Cliente implements Runnable
{
    final static String CRLF = "\r\n";

    Socket socket;

    ObjectInputStream ois;
    ObjectOutputStream oos;

    // Constructor
    public Cliente(Socket socket) throws Exception
    {
	this.socket = socket;
	this.oos = new ObjectOutputStream(socket.getOutputStream());
	this.ois = new ObjectInputStream(socket.getInputStream());
    }

    // Implement the run() method of the Runnable interface
    public void run()
    {
	try {
	    processMessage();
	} catch (Exception e) {
	    System.out.println(e);
	}
    }

    private void processMessage() throws Exception
    {
	System.out.println("Conexao inicializada");

	while (socket.isConnected())
	{	
	    Object msg = ois.readObject();
	    String message = msg.toString();
	    String response;

	    if (message.equals("Sair")) { break; }
	    else if (message.contains("."))
	    {
		response = processFile(message);
		System.out.println("Resposta: " + response);
		//System.out.println(response);
	    } else {
		System.out.println("Cliente: " + message);
		response = message;
	    }

	    oos.writeObject(response);    
	    oos.flush();
	}

	ois.close();
	oos.close();
	socket.close(); 
	System.out.println("Conexao terminada");
    }

    private String processFile( String message )
    throws Exception
    {
	System.out.println("Request arquivo: " + message);
	int code = 0;
	int size = 0;
	String hash = "";

	// Open the requested file.
	FileInputStream fis = null;
	boolean fileExists = true;

	try {
	    File file = new File(message);
	    fis = new FileInputStream(file);
	} catch (FileNotFoundException e) {
	    fileExists = false;
	    System.out.println( "Arquivo: " + message + 
				" nao encontrado.");
	}

    	if (fileExists) {
	    code = 200;

	    Hasher hasher = new Hasher();
	    hash = hasher.Hasher("SHA-256", fis);
	    //System.out.println("HASH: " + hash);
	    
	    int length = 512;
	    size = length;
	    oos.writeObject(length);
	    oos.flush();

	    byte[] buffer = new byte[length];
	    int bytes = 0;

	    while ((bytes = fis.read(buffer)) != -1 ) {
		oos.flush();
	    	oos.write(buffer, 0, bytes);
		oos.flush();
		size += bytes;
	    }

	    fis.close();
	    System.out.println( "Arquivo: " + message + 
				" enviado com sucesso");
	    return CRLF + "\tArquivo: " + message + CRLF +
		"\tStatus: " + code + CRLF +
		"\tDescricao: Arquivo transferido" + 
		CRLF + "\tTamanho: " + size + CRLF +
		"\tHash: " + hash;
	} else {
	    code = 404;

	    return CRLF + "\tArquivo: " + message + CRLF +
		"\tStatus: " + code + CRLF +
		"\tDescricao: Arquivo nao encontrado." +
		CRLF + "\tTamanho: " + size + CRLF +
		"\tHash: " + hash;
	}

    }
}
