import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import { AppointmentsService } from '../appointments/appointments.service';
import { Patient } from '../patients/patient.entity';
import { formatHuman } from '../common/timezone';

export interface ToolDeps {
  appointments: AppointmentsService;
  timezone: string;
  // The patient this conversation belongs to. Tools are scoped to them so the
  // model can never act on someone else's data.
  patient: Patient;
}

/**
 * Builds the agent tools bound to a specific patient. Tools are THIN wrappers:
 * all business logic lives in the Nest services.
 */
export function buildTools(deps: ToolDeps) {
  const { appointments, timezone, patient } = deps;

  const checkAvailability = createTool({
    id: 'check_availability',
    description:
      'Consulta los huecos libres para un servicio en una fecha concreta. ' +
      'Usar SIEMPRE antes de proponer u ofrecer una hora. Nunca inventes horas.',
    inputSchema: z.object({
      service: z.string().describe('Nombre del servicio, p. ej. "Primera valoración"'),
      date: z.string().describe('Fecha en formato YYYY-MM-DD'),
    }),
    outputSchema: z.object({
      slots: z.array(z.object({ startsAt: z.string(), label: z.string() })),
      message: z.string(),
    }),
    execute: async ({ context }) => {
      const slots = await appointments.availability(context.service, context.date);
      return {
        slots,
        message:
          slots.length > 0
            ? `Huecos libres: ${slots.map((s) => s.label).join(', ')}`
            : 'No hay huecos libres ese día.',
      };
    },
  });

  const bookAppointment = createTool({
    id: 'book_appointment',
    description:
      'Reserva una cita para el paciente actual. Solo tras confirmar el servicio ' +
      'y la hora exacta (startsAt en ISO) obtenida de check_availability.',
    inputSchema: z.object({
      service: z.string(),
      startsAt: z.string().describe('Inicio en ISO 8601 (UTC), de un hueco libre'),
    }),
    outputSchema: z.object({ ok: z.boolean(), message: z.string() }),
    execute: async ({ context }) => {
      try {
        const appt = await appointments.create(
          {
            patientId: patient.id,
            serviceName: context.service,
            startsAt: context.startsAt,
          },
          'agent',
        );
        return {
          ok: true,
          message: `Cita confirmada: ${appt.serviceName} el ${formatHuman(
            appt.startsAt,
            timezone,
          )}.`,
        };
      } catch (e) {
        return {
          ok: false,
          message:
            e instanceof Error
              ? e.message
              : 'No se pudo reservar esa hora, prueba otra.',
        };
      }
    },
  });

  const listAppointments = createTool({
    id: 'list_appointments',
    description: 'Lista las próximas citas del paciente actual.',
    inputSchema: z.object({}),
    outputSchema: z.object({
      appointments: z.array(
        z.object({ id: z.string(), description: z.string() }),
      ),
    }),
    execute: async () => {
      const all = await appointments.findForPatient(patient.id);
      const upcoming = all.filter(
        (a) => a.status === 'scheduled' && a.startsAt.getTime() > Date.now(),
      );
      return {
        appointments: upcoming.map((a) => ({
          id: a.id,
          description: `${a.serviceName} el ${formatHuman(a.startsAt, timezone)}`,
        })),
      };
    },
  });

  const cancelAppointment = createTool({
    id: 'cancel_appointment',
    description:
      'Cancela una cita del paciente actual por su id (obtenido de list_appointments).',
    inputSchema: z.object({ appointmentId: z.string() }),
    outputSchema: z.object({ ok: z.boolean(), message: z.string() }),
    execute: async ({ context }) => {
      const appt = await appointments.findOne(context.appointmentId).catch(() => null);
      if (!appt || appt.patientId !== patient.id) {
        return { ok: false, message: 'No encuentro esa cita.' };
      }
      await appointments.cancel(appt.id);
      return {
        ok: true,
        message: `Cita cancelada: ${appt.serviceName} el ${formatHuman(
          appt.startsAt,
          timezone,
        )}.`,
      };
    },
  });

  return { checkAvailability, bookAppointment, listAppointments, cancelAppointment };
}
