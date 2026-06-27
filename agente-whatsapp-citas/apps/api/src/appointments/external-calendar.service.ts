import { Injectable, Logger } from '@nestjs/common';
// eslint-disable-next-line @typescript-eslint/no-require-imports
const ical = require('node-ical');

export interface BusyRange {
  start: Date;
  end: Date;
}

@Injectable()
export class ExternalCalendarService {
  private readonly logger = new Logger('ExternalCalendarService');

  /**
   * Fetches an iCal URL and returns busy time ranges for a given UTC date.
   * Works with Google Calendar, TheFork, CoverManager, Outlook, Apple Calendar…
   * Returns [] on any error so availability never crashes.
   */
  async getBusyRanges(icalUrl: string, dateUtc: Date): Promise<BusyRange[]> {
    try {
      const events = await ical.async.fromURL(icalUrl);
      const dayStart = new Date(dateUtc);
      dayStart.setUTCHours(0, 0, 0, 0);
      const dayEnd = new Date(dateUtc);
      dayEnd.setUTCHours(23, 59, 59, 999);

      const ranges: BusyRange[] = [];

      for (const event of Object.values(events) as any[]) {
        if (event.type !== 'VEVENT') continue;

        const start: Date = event.start instanceof Date ? event.start : new Date(event.start);
        const end: Date = event.end instanceof Date ? event.end : new Date(start.getTime() + 60 * 60 * 1000);

        // Check if event overlaps with the requested day.
        if (start <= dayEnd && end >= dayStart) {
          ranges.push({ start, end });
        }

        // Handle recurring events expanded by node-ical.
        if (event.recurrences) {
          for (const rec of Object.values(event.recurrences) as any[]) {
            const rs: Date = rec.start instanceof Date ? rec.start : new Date(rec.start);
            const re: Date = rec.end instanceof Date ? rec.end : new Date(rs.getTime() + 60 * 60 * 1000);
            if (rs <= dayEnd && re >= dayStart) {
              ranges.push({ start: rs, end: re });
            }
          }
        }
      }

      return ranges;
    } catch (e) {
      this.logger.warn(`No se pudo leer el calendario externo: ${e instanceof Error ? e.message : e}`);
      return [];
    }
  }

  /** Returns true if the given slot overlaps with any busy range. */
  isSlotBusy(slotStart: Date, slotEnd: Date, busyRanges: BusyRange[]): boolean {
    return busyRanges.some((r) => slotStart < r.end && slotEnd > r.start);
  }
}
