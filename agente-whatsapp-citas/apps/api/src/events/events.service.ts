import { Injectable } from '@nestjs/common';
import { Observable, Subject } from 'rxjs';

// Types of realtime events the UI listens to over SSE.
export type AppEventType =
  | 'patient.changed'
  | 'appointment.changed'
  | 'conversation.changed'
  | 'message.created'
  | 'agent.changed';

export interface AppEvent {
  type: AppEventType;
  // Small, non-sensitive payload. NEVER put secrets or full PII dumps here.
  data?: Record<string, unknown>;
}

@Injectable()
export class EventsService {
  private readonly stream$ = new Subject<AppEvent>();

  emit(type: AppEventType, data?: Record<string, unknown>): void {
    this.stream$.next({ type, data });
  }

  asObservable(): Observable<AppEvent> {
    return this.stream$.asObservable();
  }
}
