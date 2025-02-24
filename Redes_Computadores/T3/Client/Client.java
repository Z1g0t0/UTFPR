import java.io.*;
import java.net.*;
import java.util.Scanner;
import java.util.Arrays; 
import java.util.zip.CRC32;
import java.util.Random;

public class Client {

    private static final int PORT = 9876;
    private static final int BUFFER = 1118;
    private static final int ACK_SIZE = 4;
    //private static final int ATT = 11;
    private static final int ATT = 2147483647;
    private static final int TIMEOUT = 3333;
    private static double LOSS_P = 0.0;
    private static double CORR_P = 0.0;

    public static void main( String[] args ) 
    throws Exception
    {
	while(true)
	{
	    try(DatagramSocket socket = new DatagramSocket()) {
		socket.setSoTimeout(0);
		Scanner scanner = new Scanner(System.in);
		String prob = "";

		System.out.print("Nome do arquivo: ");
		String fileName = scanner.nextLine();
		//String fileName = "test.html";
		//String fileName = "sample.gif";
		//String fileName = "Robots.mp4";
		//String fileName = "PPSM.pdf";

		System.out.print("Probabilidade de perda: ");
		prob = scanner.nextLine();
		LOSS_P = !prob.isEmpty() ?  
		    Double.parseDouble("0." + prob) : 0.0;

		System.out.print("Probabilidade de corrupcao: ");
		prob = scanner.nextLine();
		CORR_P = !prob.isEmpty() ?  
		    Double.parseDouble("0." + prob) : 0.0;

		InetAddress sAdd = 
		    InetAddress.getByName("localhost");

		byte[] fileNameB = fileName.getBytes();
		DatagramPacket sPkt = 
		    new DatagramPacket( fileNameB, 
					fileNameB.length, 
					sAdd, PORT );

		socket.send(sPkt);

		if(fileName.equals("Sair"))
		    break;

		receiveFile(socket, fileName);


	    } catch (IOException e) {
		e.printStackTrace();
		continue;
	    }
	}
    }

    private static void receiveFile( DatagramSocket socket, 
				     String fileName ) 
    throws Exception 
    {
	FileOutputStream fos = new FileOutputStream(fileName);
        //BufferedOutputStream bos = new BufferedOutputStream(fos);
	int seq_n = 1; int att = 0; //int pos = 0;
	socket.setSoTimeout(TIMEOUT);

        while(true) 
	{
	    // Simulacao de packet loss
            if(new Random().nextDouble() < LOSS_P ) {
                System.out.println("!PACKET LOSS!");
                continue;
            }

	    try {
		byte[] buffer = new byte[BUFFER];

		DatagramPacket rPkt = 
		    new DatagramPacket(buffer, buffer.length);
		socket.receive(rPkt);

		if( att > ATT ) {
		    System.out.println( "Excedido numero de " +
					"tentativas de " +
					"retransmissao." );
		    return;
		}

		byte[] allB = Arrays.copyOf(buffer, buffer.length);

		if(new Random().nextDouble() < CORR_P) {
		    System.out.println("!PACKET CORRUPTION!");

		    allB[555] = (byte)new Random().nextInt(256);
		}
		    
		Packet packet = deserializer(allB);
		 
		//System.out.println("pkt_dataL: " + packet.getData().length);
		int sSeq_n = packet.getSeq_n();

		//System.out.println("sSeq_n: " + sSeq_n);
		//System.out.println("seq_n: " + seq_n);
		if(sSeq_n == -1)
		    break;
		if(sSeq_n == -2) {
		    System.out.println( "ERRO - Arquivo nao encontrado." );
		    sendAck(socket, -2);
		    return;
		}                
		
		// Determina dinamicamente CHECKSUM_SIZE
		int CHECKSUM_SIZE = String.valueOf(
		    packet.getChecksum()).length();

		// Extracao e validacao de checksum e n de sequencia
		long checksum = calculateChecksum( 
		    packet.getData(), packet.getData().length );	
					   
		if(packet.getChecksum() == checksum) {
		    if (sSeq_n == seq_n) {
		       //Escritura do arquivo
			fos.write(packet.getData());

			// Enviar ACK
			sendAck(socket, sSeq_n);
			System.out.println("Pacote: " + seq_n + " - ACKed ");
			att = 0;
			seq_n++;
		    } else {
			System.out.println( "Numero de sequencia "+ 
					    "inesperado: " + 
					    sSeq_n ); 
			System.out.println("Reenviando ACK: " + (seq_n-1));
			sendAck(socket, seq_n-1);
		    }
		} else {
		    System.out.println("Checksum invalido!");
		   sendAck(socket, seq_n-1);
		   System.out.println("Reenviando ACK: " + (seq_n-1));
		}
		att++;
	    } catch (SocketTimeoutException e) {
		// Caso Timeout
		System.out.println("Timeout: " + att + " de " + ATT);
		att++;
		if(att > ATT) {
		    System.out.println("Tentativas excedidas.");
		    return;
		}
		continue;
	    }
	}

	// Caso pacote informando finalizando transmissao
	// com n de sequencia -1
	if(att < ATT) {
	    System.out.println("Arquivo transmitido.");
	    sendAck(socket, -1);
	}
	return;
    }

    private static long calculateChecksum( byte[] data, 
					   int length ) 
    {
        CRC32 crc32 = new CRC32();
        crc32.update(data, 0, length);

        return crc32.getValue();
    }

    private static void sendAck( DatagramSocket socket, 
				 int seq_n ) 
    throws Exception 
    {
	InetAddress sAdd = InetAddress.getByName("localhost");

	//System.out.println("seq_n: " + seq_n); 
        byte[] ackData = intToBytes(seq_n);
	//System.out.println("ACK Size: " + ackData.length);

        DatagramPacket ackPacket = 
	    new DatagramPacket( ackData, ackData.length, 
				sAdd, PORT );
        socket.send(ackPacket);
    }
    
    private static Packet deserializer ( byte[] packetData ) 
    throws Exception
    {
        try( ByteArrayInputStream bais = 
		new ByteArrayInputStream(packetData);
             ObjectInputStream ois = 
		new ObjectInputStream(bais)) {

            return (Packet)ois.readObject();
        }
    }
    
    private static byte[] intToBytes(int value) {
        return new byte[]{
                (byte) (value >>> 24),
                (byte) (value >>> 16),
                (byte) (value >>> 8),
                (byte) value
        };
    }
}
