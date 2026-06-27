// Minimal timezone helpers built on the Intl API (no external deps).
// Appointments are stored in UTC (timestamptz); the center works in its own tz.

function offsetMs(date: Date, tz: string): number {
  const dtf = new Intl.DateTimeFormat('en-US', {
    timeZone: tz,
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  const parts = dtf.formatToParts(date);
  const map: Record<string, string> = {};
  for (const p of parts) map[p.type] = p.value;
  const asUTC = Date.UTC(
    Number(map.year),
    Number(map.month) - 1,
    Number(map.day),
    Number(map.hour),
    Number(map.minute),
    Number(map.second),
  );
  return asUTC - date.getTime();
}

/** Converts a wall-clock time in a given tz to a real UTC Date. */
export function zonedToUtc(
  year: number,
  month: number, // 1-12
  day: number,
  hour: number,
  minute: number,
  tz: string,
): Date {
  const utcGuess = Date.UTC(year, month - 1, day, hour, minute, 0);
  const off = offsetMs(new Date(utcGuess), tz);
  return new Date(utcGuess - off);
}

/** Parses "YYYY-MM-DD" + "HH:mm" in a tz into a UTC Date. */
export function parseZoned(dateStr: string, timeStr: string, tz: string): Date {
  const [y, m, d] = dateStr.split('-').map(Number);
  const [hh, mm] = timeStr.split(':').map(Number);
  return zonedToUtc(y, m, d, hh, mm, tz);
}

/** Weekday (0=Sun..6=Sat) of a UTC date as seen in the given tz. */
export function weekdayInTz(date: Date, tz: string): number {
  const name = new Intl.DateTimeFormat('en-US', {
    timeZone: tz,
    weekday: 'short',
  }).format(date);
  return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(name);
}

/** "YYYY-MM-DD" of a UTC date as seen in the given tz. */
export function dateKeyInTz(date: Date, tz: string): string {
  const dtf = new Intl.DateTimeFormat('en-CA', {
    timeZone: tz,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
  return dtf.format(date); // en-CA gives YYYY-MM-DD
}

/** Human-friendly Spanish date+time in the center tz, e.g. "lunes, 24 de junio a las 10:00". */
export function formatHuman(date: Date, tz: string): string {
  const fecha = new Intl.DateTimeFormat('es-ES', {
    timeZone: tz,
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(date);
  const hora = new Intl.DateTimeFormat('es-ES', {
    timeZone: tz,
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
  return `${fecha} a las ${hora}`;
}

/** "HH:mm" in the center tz. */
export function timeInTz(date: Date, tz: string): string {
  return new Intl.DateTimeFormat('es-ES', {
    timeZone: tz,
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}
