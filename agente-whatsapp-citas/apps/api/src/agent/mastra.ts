import { Mastra } from '@mastra/core/mastra';
import { PostgresStore } from '@mastra/pg';

// Mastra storage lives in the SAME Postgres as TypeORM (a separate set of
// mastra_* tables). Used for the agent's persistence/telemetry.
let mastraInstance: Mastra | null = null;

export function getMastra(): Mastra {
  if (!mastraInstance) {
    const connectionString =
      process.env.DATABASE_URL ??
      'postgres://citas:cambia-esta-contrasena@localhost:5433/citas';
    mastraInstance = new Mastra({
      storage: new PostgresStore({ id: 'citas', connectionString }),
    });
  }
  return mastraInstance;
}
