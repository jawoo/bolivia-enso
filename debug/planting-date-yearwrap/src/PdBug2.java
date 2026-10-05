package org.cgiar.tokki;

import java.util.TreeMap;

/** Case B: an early-in-year median whose -30 d window reaches back into the PRIOR December. */
public class PdBug2
{
    static int scan(int median, String crop, int simYear, String wth) throws Exception
    {
        ScanningPlantingDates s =
                new ScanningPlantingDates(median, wth, crop, simYear, 1, null);
        Object[] r = s.call();
        @SuppressWarnings("unchecked")
        TreeMap<Integer, Integer> y2d = (TreeMap<Integer, Integer>) r[1];
        return y2d.get(simYear);
    }

    public static void main(String[] args) throws Exception
    {
        App.directoryWeather = args[0].endsWith("/") ? args[0] : args[0] + "/";
        String crop = args[1];
        int simYear = Integer.parseInt(args[2]);
        String wth = args[3];

        int half = Utility.getPlantingDateCriteria(crop)[4];
        System.out.printf("crop=%s simYear=%d windowHalf=%d  wth=%s%n%n", crop, simYear, half, wth);
        System.out.printf("%-10s %-16s %-10s %-12s %s%n",
                "medianDOY", "window(DOY)", "returned", "planted on", "verdict");
        System.out.println("-".repeat(78));

        for (int median : new int[]{5, 10, 20, 31, 32, 40, 60, 90})
        {
            int ddd = scan(median, crop, simYear, wth);
            int lo = median - half, hi = median + half;
            String win = lo + ".." + hi + (lo < 1 ? "  <-- reaches prior Dec" : "");
            // A returned DOY far ABOVE the window's upper bound came from the prior year
            String verdict = (ddd > hi)
                    ? "WRONG: +365 d (intended " + (simYear - 1) + "-" + String.format("%03d", ddd) + ")"
                    : "ok";
            System.out.printf("%-10d %-16s %-10d %-12s %s%n",
                    median, win, ddd, simYear + "-" + String.format("%03d", ddd), verdict);
        }
    }
}
