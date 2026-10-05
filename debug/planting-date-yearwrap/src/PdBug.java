package org.cgiar.tokki;

import java.util.Map;
import java.util.TreeMap;

/** Exercises the real ScanningPlantingDates against a synthetic Bolivian weather file.
 *  Same package, so the package-private constructor and App's static fields are reachable. */
public class PdBug
{
    public static void main(String[] args) throws Exception
    {
        App.directoryWeather = args[0].endsWith("/") ? args[0] : args[0] + "/";
        App.verbose = false;

        String crop = args.length > 1 ? args[1] : "SG";
        int[] c = Utility.getPlantingDateCriteria(crop);
        System.out.println("crop=" + crop
                + "  tmin>=" + c[0] + "C  onsetRain>=" + c[1] + "mm/" + c[2] + "d"
                + "  drySpellMax=" + c[3] + "d  windowHalfDays=+/-" + c[4]);
        System.out.println();
        System.out.printf("%-10s %-14s %-12s %-10s %s%n",
                "medianDOY", "window(DOY)", "returned", "planted on", "offset vs intent");
        System.out.println("-".repeat(74));

        // One simulation year: 2026. Weather file covers 2026-2027.
        for (int median : new int[]{300, 310, 320, 330, 335, 336, 340, 350, 360, 365})
        {
            ScanningPlantingDates s =
                    new ScanningPlantingDates(median, "9999999.WTH", crop, 2026, 1, null);
            Object[] r = s.call();
            @SuppressWarnings("unchecked")
            TreeMap<Integer, Integer> y2d = (TreeMap<Integer, Integer>) r[1];
            int ddd = y2d.get(2026);

            // What the scan window actually spans, in absolute day-of-series terms
            int lo = median - c[4], hi = median + c[4];
            String win = lo + ".." + hi + (hi > 365 ? "  <-- crosses 1 Jan" : "");

            // The intended date: first day in the window that passes the onset test,
            // expressed as an absolute (year, doy). Recovered from the returned DOY:
            // if the returned DOY is far below the window's lower bound it came from
            // the next calendar year.
            boolean wrapped = ddd < lo;
            String plantedOn = "2026-" + String.format("%03d", ddd);
            String intended = wrapped ? "2027-" + String.format("%03d", ddd)
                                      : "2026-" + String.format("%03d", ddd);
            String verdict = wrapped
                    ? "WRONG: -365 d (intended " + intended + ")"
                    : "ok";

            System.out.printf("%-10d %-14s %-12d %-10s %s%n",
                    median, win, ddd, plantedOn, verdict);
        }
    }
}
