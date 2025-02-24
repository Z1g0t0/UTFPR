import java.io.*;
import java.net.*;
import java.util.Arrays; 
import java.util.zip.CRC32;

public class Server 
{
    //private static final int PORT = 9876;
    private static final int PORT = 6789;
    private static final int BUFFER = 1024;
    private static final int ACK_SIZE = 4;
    //private static final int ATT = 11;
    private static final int ATT = 2147483647;
    private static final int TIMEOUT = 3333;

    public static void main( String[] args ) 
    throws Exception
    {
        try(DatagramSocket socket = new DatagramSocket(PORT)) {
            System.out.println("Servidor inicializado.");

            while(true) 
	    {
		socket.setSoTimeout(0);
                byte[] buffer = new byte[BUFFER];

		System.out.println("Aguardando request...");
                DatagramPacket rPkt = 
		    new DatagramPacket(buffer, buffer.length);
                socket.receive(rPkt);

                InetAddress cAdd = rPkt.getAddress();
                int cPort = rPkt.getPort();

                String fileName = new String( rPkt.getData(), 0, 
					      rPkt.getLength() );

		System.out.println("name: " + fileName);
		if(fileName.equals("Sair") || fileName.isEmpty())
		    continue;
		
		try {
		    sendFile(fileName, cAdd, cPort, socket);
		} catch (FileNotFoundException e) {
		    String error = "Arquivo nao encontrado.";
		    System.out.println(fileName + " - " + error);
		    byte[] errorB = error.getBytes();

		    Packet packet = new Packet(-2, 0, errorB);
		    byte[] pkt = serializer(packet);
		    DatagramPacket ePkt =
			new DatagramPacket( pkt, pkt.length, 
					    cAdd, cPort );
		    socket.send(ePkt);
		    
		    int att = 0;
		    while(!waitForAck(socket, -2))
		    {
			socket.send(ePkt);
			att++;
			if(att>ATT) {
			    System.out.println( "Excedido numero " +
						"de tentativas de " +
						"retransmissao." );
				break;
			}
		    }
		}
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void sendFile( String fileName, InetAddress cAdd, 
				  int cPort, DatagramSocket socket )
    throws Exception 
    {
        try( BufferedInputStream bis = 
		new BufferedInputStream(
		    new FileInputStream(fileName)) ) {
            System.out.println( "Enviando arquivo: "  + fileName + 
				" -> " + cAdd + ":" + cPort );

	    byte[] buffer = new byte[BUFFER];
	    int fileB; int seq_n = 1; byte[] pkt = new byte[0];
	    
	    while((fileB = bis.read(buffer)) != -1) 
	    {

		// Checksum
		long checksum = 
		    calculateChecksum(buffer, fileB);

		// Pacote e envio
                Packet packet = new Packet( seq_n, checksum, 
					    Arrays.copyOf(buffer, fileB) );

                pkt = serializer(packet);
		
		System.out.println("Transmitindo pacote " + seq_n);
		//System.out.println("Tamanho: " + pkt.length);

                DatagramPacket sPkt = 
		    new DatagramPacket( pkt, pkt.length, cAdd, cPort );
                socket.send(sPkt);

                // Esperar ACK
		int att = 0;
                while(!waitForAck(socket, seq_n))
		{
		    System.out.println("Restransmitindo pacote " + seq_n);
		    System.out.println("Tentativa " + att + " de " + ATT);
		    socket.send(sPkt);
		    att++;
		    if(att>ATT) {
			System.out.println( "Excedido numero " +
					    "de tentativas de " +
					    "retransmissao." );
			return;
		    }
		}
                seq_n++;
	    }

	    // Enviar pacote informando transmissao completa
	    // n de seq: -1, checksum: 0, payload: byte[0]
            Packet eofPacket = new Packet(-1, 0, new byte[0]);  
            byte[] eofData = serializer(eofPacket);
            DatagramPacket eofPkt = 
		new DatagramPacket( eofData, eofData.length, 
				    cAdd, cPort );
	    socket.send(eofPkt);

	    // Esperar ACK de transmissao completa (n = -1)
	    int att = 0;
            while(!waitForAck(socket, -1))
	    {
	        System.out.println("Restransmitindo pacote(EOF) -1");
	        socket.send(eofPkt);
		att++;
		if(att>=ATT) {
		    System.out.println( "Excedido numero " +
					"de tentativas de " +
					"retransmissao." );
		    return;
		}
	    }
	    System.out.println("Arquivo enviado.");
	}
    }
    
    private static boolean waitForAck( DatagramSocket socket, 
				       int seq_n ) 
    throws Exception 
    {
        // Tempo de Timeout
        socket.setSoTimeout(TIMEOUT);

        while(true)
	{
            try {
                byte[] ackData = new byte[ACK_SIZE];
                DatagramPacket ackPkt = 
		    new DatagramPacket(ackData, ackData.length);
                socket.receive(ackPkt);

                // Extrai n de sequencia ACKed e avalia
                int rSeq_n = deserializer(ackPkt.getData());

                if (rSeq_n == seq_n) {
                    System.out.println("Recebido ACK " + seq_n);
		    socket.setSoTimeout(0);

		    return true;
                } else {
                    System.out.println( "ACKs diferem - " +
					"Recebido: " + rSeq_n +" - "+
					"Esperado: " + seq_n );
		    return false;
		}

            } catch (SocketTimeoutException e) {
		// Caso Timeout na espera de ACK
                System.out.println("ACK Timeout");

		return false;
            }
        }
    }

    private static byte[] serializer( Packet packet ) 
    throws Exception 
    {
        try(ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ObjectOutputStream oos = new ObjectOutputStream(baos) ) {

            oos.writeObject(packet);

            return baos.toByteArray();
        }
    }
    
    private static int deserializer( byte[] ackData ) 
    throws Exception
    {
        try(ByteArrayInputStream bais = 
	    new ByteArrayInputStream(ackData);
	    DataInputStream dis = new DataInputStream(bais) ) { 
	    
	    return dis.readInt();	
	}
    }

    private static long calculateChecksum( byte[] data, 
					   int length ) 
    { 
        CRC32 crc32 = new CRC32();
        crc32.update(data, 0, length);

        return crc32.getValue();
    }
}
