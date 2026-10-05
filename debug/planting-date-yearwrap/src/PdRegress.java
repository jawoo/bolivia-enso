package org.cgiar.tokki;

import java.io.File;
import java.util.Arrays;
import java.util.TreeMap;

/** Dumps planting-date decisions for a sample of real cells/years/medians so the
 *  unpatched and patched builds can be diffed byte-for-byte. */
public class PdRegress
{
    public static void main(String[] args) throws Exception
    {
        App.directoryWeather = args[0].endsWith("/") ? args[0] : args[0] + "/";
        int nCells = Integer.parseInt(args[1]);

        String[] all = new File(App.directoryWeather).list((d, n) -> n.endsWith(".WTH"));
        Arrays.sort(all);
        // even spread across the sorted cell list
        int step = Math.max(1, all.length / nCells);

        for (int i = 0; i < all.length && i / step < nCells; i += step)
        {
            String wth = all[i];
            for (String crop : new String[]{"MZ", "SB", "WH", "RI", "SG"})
                for (int median : new int[]{100, 110, 120, 130, 140, 150, 160})
                {
                    ScanningPlantingDates s =
                            new ScanningPlantingDates(median, wth, crop, 1995, 31, null);
                    Object[] r = s.call();
                    @SuppressWarnings("unchecked")
                    TreeMap<Integer, Integer> y2d = (TreeMap<Integer, Integer>) r[1];
                    StringBuilder sb = new StringBuilder();
                    for (java.util.Map.Entry<Integer, Integer> e : y2d.entrySet())
                        sb.append(e.getKey()).append(':').append(e.getValue()).append(' ');
                    System.out.println(wth + " " + crop + " m" + median + " | " + sb.toString().trim());
                }
        }
    }
}
