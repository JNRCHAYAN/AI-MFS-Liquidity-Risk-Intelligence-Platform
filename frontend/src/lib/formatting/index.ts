/**
 * Display-layer formatting helpers.
 *
 * Money is integer poisha everywhere else in the system; conversion to BDT
 * happens only here, using integer arithmetic so no binary float touches a
 * ledger quantity.
 */

const TAKA_MARK = "৳"; // ৳

/** Format integer poisha as a BDT string, e.g. 1250000 -> "৳12,500.00". */
export function formatPoisha(poisha: number): string {
  if (!Number.isFinite(poisha)) {
    return `${TAKA_MARK}—`;
  }

  const negative = poisha < 0;
  const absolute = Math.abs(Math.trunc(poisha));
  const taka = Math.floor(absolute / 100);
  const fraction = absolute % 100;

  const grouped = taka.toLocaleString("en-US");
  const padded = String(fraction).padStart(2, "0");

  return `${negative ? "-" : ""}${TAKA_MARK}${grouped}.${padded}`;
}

const DHAKA_FORMATTER = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Asia/Dhaka",
  year: "numeric",
  month: "short",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZoneName: "short",
});

/** Render a UTC timestamp in Asia/Dhaka with the timezone shown. */
export function formatDateTimeDhaka(isoUtc: string): string {
  const date = new Date(isoUtc);
  if (Number.isNaN(date.getTime())) {
    return "Unknown time";
  }
  return DHAKA_FORMATTER.format(date);
}
