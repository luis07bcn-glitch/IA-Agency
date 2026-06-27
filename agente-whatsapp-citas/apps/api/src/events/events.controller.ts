import { Controller, Sse } from '@nestjs/common';
import { map, Observable, startWith } from 'rxjs';
import { EventsService } from './events.service';

interface MessageEvent {
  data: string | object;
  type?: string;
}

@Controller('events')
export class EventsController {
  constructor(private readonly events: EventsService) {}

  // Single SSE endpoint: GET /api/events
  // The frontend connects with the native EventSource and refreshes on changes.
  @Sse()
  stream(): Observable<MessageEvent> {
    return this.events.asObservable().pipe(
      // Send an initial "connected" ping so the client knows the stream is live.
      startWith({ type: 'connected', data: {} }),
      map((event) => ({
        type: event.type,
        data: JSON.stringify(event.data ?? {}),
      })),
    );
  }
}
