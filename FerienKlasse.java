
import java.util.*;

public class FerienKlasse {
	public static void main(String[] args) {
		
		int[][] obj = new int[9][9];
		

		for (int i = 0; i < obj.length; i++) {
            for (int j = 0; j < obj[i].length; j++) {
                obj[i][j] = 0;
            }
        }
		
		obj [5][5] = 1;
		
		for (int i = 0; i+1 < obj.length; i++) {
            for (int j = 0; j+1 < obj[i].length; j++) {
            
         int a = 0;
        		 int b = 0;
        		 int c = 0;
        		 int d = 0;
        		 
                 a =    	obj[i][j+1];
                 b =	obj[i+1][j];
            	 c = obj[i][j];
                 d = obj[i][j];
                 
                 if (((a+b+c+d)%2) == 1) {
                	 
                	 obj[i][j] = 1;
                 }
                	 else {
                		 obj[i][j]=0;
                	 }
             
            }
        }
		
		System.out.print(obj[5][6]);
		
		for (int i = 0; i < obj.length; i++) {
            for (int j = 0; j < obj[i].length; j++) {
            	System.out.print(obj[i][j]);
            	int a = 0;
            	a++;
            	if (a%5 == 0) {
            		System.out.println();
            	}
            }
        }

	}
	
		
}
