public class Main {
    public static void main(String[] args) {
        System.out.println("Hello and welcome!");
        trial();
    }

    public static void trial() {
        int a = 10;
        int b = 5;
        doubleValues(a, b);
        System.out.print(b);
        System.out.print(a);
    }

    public static void doubleValues(int c, int d) {
        c = c * 2;
        d = d * 2;
        System.out.print(c);
        System.out.print(d);
    }
}

